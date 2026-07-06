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

ITEM_BANK_PATHS = [
    p
    for p in [
        "/item-banks/weekly-item-bank.md",
        "/item-banks/review-quiz-item-bank.md",
    ]
    if os.path.isfile(p)
]


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
    game.join(data["nickname"])
    join_room(data["pin"])
    emit("join_ok", {"nickname": data["nickname"]})


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
        },
        to=data["pin"],
    )
    socketio.start_background_task(_auto_reveal_after_timeout, data["pin"], game.current_index)


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
    socketio.emit(
        "question:results",
        {"distribution": game.answer_distribution(), "leaderboard": game.leaderboard()},
        to=pin,
    )


@socketio.on("answer_submit")
def on_answer_submit(data):
    game = GAMES.get(data["pin"])
    if game is None:
        return
    try:
        result = game.submit_answer(data["nickname"], data["choice"])
    except ValueError:
        return
    if result is None:
        return
    emit("answer:feedback", result)
    if game.all_answered():
        _reveal_results(data["pin"])


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
