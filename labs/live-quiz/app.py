# app.py
import csv
import datetime
import io
import json
import os

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    session,
    redirect,
    url_for,
    abort,
)
from flask_socketio import SocketIO, join_room, emit

import auth
import db as dbmod
import quiz_loader
from game import GameSession, generate_pin

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-not-secret-override-in-prod")
socketio = SocketIO(app, async_mode="eventlet")

# --- Platform data + config (teachers, question sets, sessions) -------------------------------
# DB_PATH resolves from the env (tests point it at a tmp file; the container defaults to the
# persistent /data volume). The connection + schema are established once, at import time.
DB_PATH = os.environ.get("DB_PATH", "/data/live-quiz.db")
INVITE_CODE = os.environ.get("INVITE_CODE", "")
_conn = dbmod.connect(DB_PATH)
dbmod.init_db(_conn)
if not INVITE_CODE:
    print("WARNING: INVITE_CODE is unset — teacher registration is CLOSED until you set it.", flush=True)
if app.config["SECRET_KEY"] == "dev-not-secret-override-in-prod":
    print("WARNING: SECRET_KEY is the insecure default — set a real one before any real use.", flush=True)

# Harden the session cookie: never readable from JS, and not sent on cross-site requests.
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
# Bound request bodies at ingestion (Werkzeug 413s anything larger before a handler buffers it).
# 256 KB comfortably fits the 100 KB markdown cap + multipart/form overhead; anything past it is abuse.
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
# SESSION_COOKIE_SECURE is opt-in via env so local http dev still works while TLS prod is hardened.
if os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes"):
    app.config["SESSION_COOKIE_SECURE"] = True


def get_db():
    return _conn


def _now():
    return datetime.datetime.utcnow().isoformat(timespec="seconds")


def _issue_csrf():
    # One CSRF token per session, embedded as a hidden field in every state-changing form.
    if "csrf" not in session:
        session["csrf"] = auth.new_csrf_token()
    return session["csrf"]


def _check_csrf():
    if not auth.csrf_ok(session.get("csrf"), request.form.get("csrf_token")):
        abort(400)

GAMES = {}  # pin -> GameSession
GAME_OWNER = {}  # pin -> teacher_id, so only the creating teacher can export a game's results
SID_TO_PLAYER = {}  # socket id -> (pin, nickname), so a dropped socket can mark its player away
CURRENT_SID = {}    # (pin, nickname) -> latest socket id, to ignore a stale reconnect's disconnect


@app.route("/")
def index():
    return render_template("player.html")


@app.route("/host", methods=["GET"])
@auth.login_required
def host_page():
    # the set+topic are chosen in the console, which POSTs straight to /host/create;
    # a bare GET /host just sends the teacher to their console to pick one.
    return redirect(url_for("console_page"))


@app.route("/host/create", methods=["POST"])
@auth.login_required
def host_create():
    _check_csrf()
    tid = auth.current_teacher_id()
    try:
        set_id = int(request.form.get("set_id", ""))
    except ValueError:
        abort(404)                                   # malformed id -> same not-found as unowned
    if not (0 < set_id <= 2**63 - 1):
        abort(404)                                   # out of SQLite INTEGER range -> not-found, never a 500
    s = dbmod.get_set(get_db(), set_id, tid)
    if s is None:
        abort(404)                                   # not this teacher's set (IDOR-safe)
    topics = quiz_loader.parse_topics_from_text(s["source_md"])
    topic = request.form.get("topic") or next(iter(topics), None)
    questions = topics.get(topic, [])
    if not questions:
        abort(400)
    pin = generate_pin()
    while pin in GAMES:  # avoid an extremely unlikely PIN collision
        pin = generate_pin()
    GAMES[pin] = GameSession(pin, questions)
    GAME_OWNER[pin] = tid
    return render_template("host.html", created_pin=pin)


@app.route("/host/<pin>/export")
@auth.login_required
def host_export(pin):
    game = GAMES.get(pin)
    if game is None or GAME_OWNER.get(pin) != auth.current_teacher_id():
        return "not found", 404                      # unknown OR not this teacher's game
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=["nickname", "total_score", "correct_count", "avg_response_time_ms"]
    )
    writer.writeheader()
    writer.writerows(game.export_results())
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"quiz-{pin}-results.csv")


# --- Teacher auth: register / login / logout --------------------------------------------------


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html", csrf_token=_issue_csrf(), error=None)
    _check_csrf()
    username = (request.form.get("username") or "").strip()[:40]
    password = request.form.get("password") or ""
    if not auth.invite_ok(request.form.get("invite"), INVITE_CODE):
        return render_template("register.html", csrf_token=_issue_csrf(), error="Invalid invite code."), 200
    if len(username) < 3 or len(password) < 8:
        return render_template("register.html", csrf_token=_issue_csrf(),
                               error="Username ≥ 3 chars, password ≥ 8 chars."), 200
    # DELIBERATE DEVIATION FROM PLAN: bcrypt 5.x RAISES `ValueError: password cannot be longer
    # than 72 bytes` (no silent truncation), so an over-long password would 500 hash_password.
    # Reject it here with a friendly 200 form error instead of letting the route crash.
    if len(password.encode("utf-8")) > 72:
        return render_template("register.html", csrf_token=_issue_csrf(),
                               error="Password must be 8–72 characters."), 200
    if dbmod.get_teacher_by_username(get_db(), username):
        return render_template("register.html", csrf_token=_issue_csrf(), error="Username taken."), 200
    tid = dbmod.create_teacher(get_db(), username, auth.hash_password(password), _now())
    session["teacher_id"] = tid
    return redirect(url_for("console_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html", csrf_token=_issue_csrf(), error=None)
    _check_csrf()
    t = dbmod.get_teacher_by_username(get_db(), (request.form.get("username") or "").strip())
    if t and auth.verify_password(request.form.get("password") or "", t["password_hash"]):
        session.clear()                              # anti session-fixation: drop any pre-login state
        session["teacher_id"] = t["id"]
        session["csrf"] = auth.new_csrf_token()      # a fresh token bound to the new session
        return redirect(url_for("console_page"))
    return render_template("login.html", csrf_token=_issue_csrf(), error="Wrong username or password."), 200


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# --- Teacher console: question-set CRUD + live parse preview ----------------------------------
# Every route below is login-gated AND owner-scoped: a set is only ever fetched/updated/deleted
# with owner_id = the logged-in teacher's id (db.get_set/update_set/delete_set enforce
# `teacher_id = owner_id` in SQL). A teacher poking at another teacher's set id therefore gets a
# 404 (get_set -> None -> abort) and update/delete no-op (rowcount 0 -> abort) — never a data leak
# or a cross-tenant write (IDOR-safe).

MAX_TITLE_LEN = 120            # a set title is capped, not a crash risk
MAX_SOURCE_BYTES = 100 * 1024  # 100 KB cap on a set's pasted/uploaded markdown


def _read_source(req):
    # Accept either a pasted textarea or an uploaded .md file. Read a little past the cap so
    # oversize input is *rejected* by _source_too_big below rather than silently truncated.
    f = req.files.get("source_file")
    if f and f.filename:
        raw = f.read(MAX_SOURCE_BYTES + 1024)
        return raw.decode("utf-8", errors="replace")
    return req.form.get("source_md") or ""


def _source_too_big(source_md):
    return len(source_md.encode("utf-8")) > MAX_SOURCE_BYTES


def _parse_or_none(source_md):
    # Returns the parsed topics only if at least one question was recognised, else None so the
    # route can refuse an empty/unparseable set with a friendly form error (never store junk).
    topics = quiz_loader.parse_topics_from_text(source_md or "")
    total = sum(len(v) for v in topics.values())
    return topics if total > 0 else None


def _set_form(error=None, editing=None, title="", source_md=""):
    # Render the create/edit form. `editing` (a set Row) switches the form to edit mode; when
    # re-rendering after a validation error we echo the submitted title/source so work isn't lost.
    return render_template(
        "set_form.html",
        csrf_token=_issue_csrf(),
        error=error,
        editing=editing,
        title=title,
        source_md=source_md,
    )


@app.route("/console")
@auth.login_required
def console_page():
    sets = dbmod.list_sets(get_db(), auth.current_teacher_id())
    # Per-set metadata for the console cards: the topic names (populate the "Start game" dropdown)
    # plus a question count so a teacher can see a set's size at a glance.
    set_meta = {}
    for s in sets:
        parsed = quiz_loader.parse_topics_from_text(s["source_md"])
        set_meta[s["id"]] = {"topics": list(parsed.keys()),
                             "count": sum(len(v) for v in parsed.values())}
    return render_template("console.html", sets=sets, set_meta=set_meta, csrf_token=_issue_csrf())


@app.route("/console/preview", methods=["POST"])
@auth.login_required
def console_preview():
    _check_csrf()
    # Bound the work: parse at most the size cap so a giant paste can't tie up the worker.
    source_md = (request.form.get("source_md") or "")[:MAX_SOURCE_BYTES]
    topics = quiz_loader.parse_topics_from_text(source_md)
    payload = {"topics": [{"topic": k, "count": len(v)} for k, v in topics.items()]}
    return app.response_class(json.dumps(payload), mimetype="application/json")


@app.route("/console/sets/new", methods=["GET", "POST"])
@auth.login_required
def console_set_new():
    if request.method == "GET":
        return _set_form()
    _check_csrf()
    title = (request.form.get("title") or "").strip()[:MAX_TITLE_LEN] or "Untitled set"
    source_md = _read_source(request)
    if _source_too_big(source_md):
        return _set_form(error="That set is too large (max 100 KB).", title=title, source_md=""), 200
    if _parse_or_none(source_md) is None:
        return _set_form(error="That set has no questions the parser can read — check the format.",
                         title=title, source_md=source_md), 200
    dbmod.create_set(get_db(), auth.current_teacher_id(), title, source_md, _now())
    return redirect(url_for("console_page"))


@app.route("/console/sets/<int:set_id>/edit", methods=["GET", "POST"])
@auth.login_required
def console_set_edit(set_id):
    s = dbmod.get_set(get_db(), set_id, auth.current_teacher_id())
    if s is None:
        abort(404)                                   # not this teacher's set (IDOR-safe)
    if request.method == "GET":
        return _set_form(editing=s, title=s["title"], source_md=s["source_md"])
    _check_csrf()
    title = (request.form.get("title") or "").strip()[:MAX_TITLE_LEN] or s["title"]
    source_md = _read_source(request)
    if _source_too_big(source_md):
        return _set_form(error="That set is too large (max 100 KB).",
                         editing=s, title=title, source_md=s["source_md"]), 200
    if _parse_or_none(source_md) is None:
        return _set_form(error="That set has no questions the parser can read — check the format.",
                         editing=s, title=title, source_md=source_md), 200
    dbmod.update_set(get_db(), set_id, auth.current_teacher_id(), title, source_md, _now())
    return redirect(url_for("console_page"))


@app.route("/console/sets/<int:set_id>/delete", methods=["POST"])
@auth.login_required
def console_set_delete(set_id):
    _check_csrf()
    if dbmod.delete_set(get_db(), set_id, auth.current_teacher_id()) == 0:
        abort(404)                                   # unknown OR not this teacher's set
    return redirect(url_for("console_page"))


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
