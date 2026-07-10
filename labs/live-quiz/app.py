# app.py
import csv
import io
import os

from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, join_room, emit

from game import GameSession, generate_pin
from quiz_loader import load_all_topics

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-not-secret-override-in-prod")
socketio = SocketIO(app, async_mode="eventlet")

GAMES = {}  # pin -> GameSession
SID_TO_PLAYER = {}  # socket id -> (pin, nickname), so a dropped socket can mark its player away
CURRENT_SID = {}    # (pin, nickname) -> latest socket id, to ignore a stale reconnect's disconnect

# Default item-bank mount points (see docker-compose.yml). Override for local dev or a
# different deployment layout with ITEM_BANK_PATHS (an os.pathsep-separated list of paths).
_DEFAULT_ITEM_BANKS = [
    "/item-banks/weekly-item-bank.md",
    "/item-banks/review-quiz-item-bank.md",
]


def resolve_item_bank_paths(configured, default):
    """Pick which item-bank files to load: the ITEM_BANK_PATHS env value if set (a
    pathsep-separated list), else the defaults — keeping only paths that exist on disk."""
    candidates = configured.split(os.pathsep) if configured else list(default)
    return [p for p in candidates if os.path.isfile(p)]


ITEM_BANK_PATHS = resolve_item_bank_paths(os.environ.get("ITEM_BANK_PATHS"), _DEFAULT_ITEM_BANKS)
if not ITEM_BANK_PATHS:
    print(
        "WARNING: no item-bank files found — the host topic list will be empty. "
        "Mount the banks (see docker-compose.yml) or set ITEM_BANK_PATHS.",
        flush=True,
    )


def _topics():
    if not ITEM_BANK_PATHS:
        return {}
    return load_all_topics(ITEM_BANK_PATHS)


@app.route("/")
def index():
    return render_template("player.html")


@app.route("/host", methods=["GET"])
def host_page():
    return render_template("host.html", topics=sorted(_topics().keys()))


@app.route("/host/create", methods=["POST"])
def host_create():
    topic = request.form["topic"]
    questions = _topics().get(topic, [])
    pin = generate_pin()
    while pin in GAMES:  # avoid an extremely unlikely PIN collision
        pin = generate_pin()
    GAMES[pin] = GameSession(pin, questions)
    return render_template("host.html", topics=sorted(_topics().keys()), created_pin=pin)


@app.route("/host/<pin>/export")
def host_export(pin):
    game = GAMES.get(pin)
    if game is None:
        return "unknown game", 404
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=["nickname", "total_score", "correct_count", "avg_response_time_ms"]
    )
    writer.writeheader()
    writer.writerows(game.export_results())
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"quiz-{pin}-results.csv")


@socketio.on("host_join")
def on_host_join(data):
    join_room(data["pin"])


@socketio.on("player_join")
def on_player_join(data):
    game = GAMES.get(data["pin"])
    if game is None:
        emit("join_error", {"message": "unknown game PIN"})
        return
    # trust nothing from the socket: cap length and drop control chars server-side
    # (the client maxlength is cosmetic and bypassable), then require something left
    nickname = "".join(c for c in (data.get("nickname") or "") if c.isprintable()).strip()[:24]
    if not nickname:
        emit("join_error", {"message": "pick a nickname"})
        return
    game.join(nickname)
    join_room(data["pin"])
    SID_TO_PLAYER[request.sid] = (data["pin"], nickname)
    CURRENT_SID[(data["pin"], nickname)] = request.sid
    emit("join_ok", {"nickname": nickname})
    # if a question is already live, show it to this (re)joining player instead of a blank wait
    q = game.current_question()
    if q is not None and not getattr(game, "_revealed_this_round", False):
        emit(
            "question:show",
            {
                "stem": q["stem"],
                "options": q["options"],
                "time_limit": game.time_limit,
                "index": game.current_index,
                "total": len(game.questions),
                "players": _connected_count(game),
            },
        )
    _broadcast_lobby(game, data["pin"])


def _broadcast_lobby(game, pin):
    # let the host's lobby screen fill up (and thin out) live as players come and go
    socketio.emit(
        "lobby:update",
        {"count": _connected_count(game), "players": sorted(game.players)[:60]},
        to=pin,
    )


@socketio.on("disconnect")
def on_disconnect():
    info = SID_TO_PLAYER.pop(request.sid, None)
    if info is None:
        return  # e.g. the host socket — the game persists, nothing to do
    pin, nickname = info
    if CURRENT_SID.get((pin, nickname)) != request.sid:
        return  # the player already reconnected on a newer socket; ignore the stale drop
    CURRENT_SID.pop((pin, nickname), None)
    game = GAMES.get(pin)
    if game is None:
        return
    game.disconnect(nickname)
    _broadcast_lobby(game, pin)
    # We deliberately do NOT reveal the round here: a disconnect can be a brief wifi blip of the
    # last un-answered player, and revealing on it would prematurely end the round and rob that
    # player of their answer. The round stays bounded by the 20s timer and still ends early when
    # the remaining connected players all answer (handled in on_answer_submit).


@socketio.on("host_next")
def on_host_next(data):
    game = GAMES.get(data["pin"])
    if game is None:
        return
    question = game.next_question()
    if question is None:
        emit("game:finished", {"leaderboard": game.leaderboard(top_n=len(game.players))}, to=data["pin"])
        return
    emit(
        "question:show",
        {
            "stem": question["stem"],
            "options": question["options"],
            "time_limit": game.time_limit,
            "index": game.current_index,
            "total": len(game.questions),
            "players": _connected_count(game),
        },
        to=data["pin"],
    )
    socketio.start_background_task(_auto_reveal_after_timeout, data["pin"], game.current_index)


def _connected_count(game):
    return sum(1 for p in game.players.values() if p.connected)


def _auto_reveal_after_timeout(pin, question_index):
    game = GAMES.get(pin)
    if game is None:
        return
    socketio.sleep(game.time_limit)
    # only reveal if the round is still the same one (host may have already advanced)
    # and results haven't already been sent because everyone answered early
    if game.current_index == question_index and not getattr(game, "_revealed_this_round", False):
        _reveal_results(pin)


def _reveal_results(pin):
    game = GAMES.get(pin)
    if game is None:
        return
    if getattr(game, "_revealed_this_round", False):
        return  # already revealed for this round (guards both the timeout path and the
                # all-answered path from double-firing regardless of which ran first)
    game._revealed_this_round = True
    q = game.current_question()
    socketio.emit(
        "question:results",
        {
            "distribution": game.answer_distribution(),
            "leaderboard": game.leaderboard(),
            "correct": q["correct"] if q else None,
        },
        to=pin,
    )


@socketio.on("answer_submit")
def on_answer_submit(data):
    game = GAMES.get(data["pin"])
    if game is None:
        return
    if getattr(game, "_revealed_this_round", False):
        return  # the round is already revealed; a late tap must not score after the fact
    try:
        result = game.submit_answer(data["nickname"], data["choice"])
    except ValueError:
        return
    if result is None:
        return
    # feedback carries the player's authoritative cumulative score so the phone never has to
    # guess it (client-side accumulation drifts across a reconnect)
    player = game.players.get(data["nickname"])
    emit("answer:feedback", {**result, "score": player.score if player else 0})
    # keep the projector's "answered" counter climbing live — count only still-connected answerers
    answered = sum(1 for n in game.answers_this_round if game.players[n].connected)
    socketio.emit(
        "answer:tally",
        {"answered": answered, "total": _connected_count(game)},
        to=data["pin"],
    )
    if game.all_answered():
        _reveal_results(data["pin"])


if __name__ == "__main__":
    # PORT override is for local dev outside Docker (macOS AirPlay squats on 5000);
    # the container keeps the 5000 default and docker-compose maps it to host 5050.
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
