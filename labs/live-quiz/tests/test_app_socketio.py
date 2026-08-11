# tests/test_app_socketio.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import app, socketio, GAMES, GAME_OWNER, get_db
import content as C
import db as dbmod
import roster
from game import GameSession

QUESTIONS = [{"stem": "Q1?", "options": ["a", "b", "c", "d"], "correct": 1}]


def _enroll(student_ids, course_slug=None):
    """Enroll fake students in a real course so a nickname can be checked against
    a genuine roster, the same way roster.py itself is tested."""
    slug = course_slug or C.COURSES[0]["slug"]
    conn = get_db()
    t = dbmod.get_teacher_by_username(conn, "roster_check_teacher")
    tid = t["id"] if t else dbmod.create_teacher(conn, "roster_check_teacher", "unused-hash", now="t")
    roster.enroll(conn, course_slug=slug, teacher_id=tid, student_ids=student_ids, now="t")
    return slug


def _authed_host_socket(pin):
    """host_next now requires the emitting socket to be bound (in on_host_join) as the game's
    owner, verified via the same Flask-session auth.current_teacher_id() the HTTP routes use — so
    a bare unauthenticated socketio.test_client(app) can no longer drive host_next. Give this pin
    a real owning teacher and hand back a Socket.IO test client authenticated as that teacher
    (idempotent: safe to call again for the same pin across test runs against a persistent DB)."""
    username = f"host_{pin}"
    t = dbmod.get_teacher_by_username(get_db(), username)
    tid = t["id"] if t else dbmod.create_teacher(get_db(), username, "unused-hash", now="t")
    GAME_OWNER[pin] = tid
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["teacher_id"] = tid
    sock = socketio.test_client(app, flask_test_client=client)
    sock.emit("host_join", {"pin": pin})
    return sock


def test_full_round_trip_join_question_answer_results():
    GAMES.clear()
    GAMES["999999"] = GameSession("999999", QUESTIONS)

    host = _authed_host_socket("999999")
    alice = socketio.test_client(app)
    bob = socketio.test_client(app)

    alice.emit("player_join", {"pin": "999999", "nickname": "alice"})
    bob.emit("player_join", {"pin": "999999", "nickname": "bob"})

    # the host lobby fills up live as players join
    lobby = [e for e in host.get_received() if e["name"] == "lobby:update"]
    assert lobby, "expected lobby:update broadcasts on player joins"
    assert lobby[-1]["args"][0] == {"count": 2, "players": ["alice", "bob"]}

    host.emit("host_next", {"pin": "999999"})
    # every client in the room should receive the question
    assert any(e["name"] == "question:show" for e in alice.get_received())
    assert any(e["name"] == "question:show" for e in bob.get_received())

    alice.emit("answer_submit", {"pin": "999999", "nickname": "alice", "choice": 1})  # correct
    bob.emit("answer_submit", {"pin": "999999", "nickname": "bob", "choice": 0})  # wrong

    # both answered -> results broadcast immediately, no need to wait for the timer
    host_events = host.get_received()
    results = [e for e in host_events if e["name"] == "question:results"]
    assert len(results) == 1
    payload = results[0]["args"][0]
    assert payload["distribution"] == [1, 1, 0, 0]
    assert payload["correct"] == 1  # results reveal the correct option index
    assert payload["leaderboard"][0]["nickname"] == "alice"  # alice scored, bob didn't

    # the projector's live "answered" counter climbs as responses arrive
    tallies = [e for e in host_events if e["name"] == "answer:tally"]
    assert tallies, "expected at least one answer:tally broadcast"
    assert tallies[-1]["args"][0] == {"answered": 2, "total": 2}


def test_disconnect_lets_remaining_players_finish_the_round():
    GAMES.clear()
    GAMES["888888"] = GameSession("888888", QUESTIONS)

    host = _authed_host_socket("888888")
    alice = socketio.test_client(app)
    bob = socketio.test_client(app)
    alice.emit("player_join", {"pin": "888888", "nickname": "alice"})
    bob.emit("player_join", {"pin": "888888", "nickname": "bob"})
    host.emit("host_next", {"pin": "888888"})
    host.get_received()  # clear

    bob.disconnect()  # bob closes his tab mid-question
    alice.emit("answer_submit", {"pin": "888888", "nickname": "alice", "choice": 1})

    # alice is now the only connected player, so the round reveals without waiting for the timer
    results = [e for e in host.get_received() if e["name"] == "question:results"]
    assert len(results) == 1


def test_answer_after_reveal_is_rejected():
    GAMES.clear()
    GAMES["666666"] = GameSession("666666", QUESTIONS)

    host = _authed_host_socket("666666")
    alice = socketio.test_client(app)
    alice.emit("player_join", {"pin": "666666", "nickname": "alice"})
    host.emit("host_next", {"pin": "666666"})

    alice.emit("answer_submit", {"pin": "666666", "nickname": "alice", "choice": 1})  # scores + reveals
    score_after_first = GAMES["666666"].players["alice"].score
    assert score_after_first > 0

    # a second (post-reveal) tap must not score — the round is already revealed
    alice.emit("answer_submit", {"pin": "666666", "nickname": "alice", "choice": 1})
    assert GAMES["666666"].players["alice"].score == score_after_first


def test_host_join_does_not_create_a_room_for_a_nonexistent_pin():
    # join_room() ran unconditionally, before checking the pin identified a real game — an
    # unauthenticated socket could make the server hold an unbounded number of arbitrary Socket.IO
    # rooms just by emitting host_join with made-up PINs. HOST_SIDS (the actual host-authorization
    # gate used by on_host_next) was never affected by this, but the room registry growth is real.
    GAMES.clear()
    sock = socketio.test_client(app)
    sock.emit("host_join", {"pin": "NOPE99"})
    rooms = socketio.server.manager.rooms.get("/", {})
    assert "NOPE99" not in rooms, "must not create a Socket.IO room for a PIN with no real game"


def test_host_join_still_creates_a_room_for_a_real_pin():
    GAMES.clear()
    GAMES["333333"] = GameSession("333333", QUESTIONS)
    sock = socketio.test_client(app)
    sock.emit("host_join", {"pin": "333333"})
    rooms = socketio.server.manager.rooms.get("/", {})
    assert "333333" in rooms, "a real game's PIN must still be joinable as a room"


def test_a_stale_socket_cannot_answer_after_its_nickname_is_reclaimed():
    # Nicknames aren't authenticated (see nickname_matches_roster's own docstring) and are
    # broadcast to the whole lobby, so anyone can emit player_join with a name they saw there.
    # game.join() silently hands back the SAME player on a repeat nickname (this is intentional —
    # a dropped wifi connection must let the real student rejoin), but on_answer_submit must only
    # trust the MOST RECENT socket to have claimed that nickname, exactly like on_disconnect
    # already does via CURRENT_SID — not every socket that has ever held it.
    GAMES.clear()
    GAMES["444444"] = GameSession("444444", QUESTIONS)

    host = _authed_host_socket("444444")
    victim = socketio.test_client(app)
    victim.emit("player_join", {"pin": "444444", "nickname": "alice"})

    attacker = socketio.test_client(app)
    attacker.emit("player_join", {"pin": "444444", "nickname": "alice"})  # claims the same name

    host.emit("host_next", {"pin": "444444"})
    host.get_received()  # clear

    # the now-stale original socket must not be able to score as "alice" any more
    victim.emit("answer_submit", {"pin": "444444", "nickname": "alice", "choice": 1})
    assert GAMES["444444"].players["alice"].score == 0, \
        "the stale socket must not have been able to submit an answer"

    # the socket that most recently claimed the nickname is the one that can
    attacker.emit("answer_submit", {"pin": "444444", "nickname": "alice", "choice": 1})
    assert GAMES["444444"].players["alice"].score > 0, \
        "the current socket for the nickname should still be able to answer"


def test_nickname_is_sanitized_server_side():
    GAMES.clear()
    GAMES["555555"] = GameSession("555555", QUESTIONS)

    empty = socketio.test_client(app)
    empty.emit("player_join", {"pin": "555555", "nickname": "   "})
    assert any(e["name"] == "join_error" for e in empty.get_received())  # blank rejected

    long = socketio.test_client(app)
    long.emit("player_join", {"pin": "555555", "nickname": "x" * 100})
    ok = [e for e in long.get_received() if e["name"] == "join_ok"]
    assert ok and len(ok[0]["args"][0]["nickname"]) == 24  # capped server-side


def test_joining_mid_question_shows_the_active_question():
    GAMES.clear()
    GAMES["777777"] = GameSession("777777", QUESTIONS)

    host = _authed_host_socket("777777")
    host.emit("host_next", {"pin": "777777"})  # question is live before anyone joins

    late = socketio.test_client(app)
    late.emit("player_join", {"pin": "777777", "nickname": "late"})
    shown = [e for e in late.get_received() if e["name"] == "question:show"]
    assert len(shown) == 1  # the latecomer/reconnecter sees the in-progress question, not a blank wait
    assert shown[0]["args"][0]["stem"] == "Q1?"


def test_nickname_matching_a_real_enrolled_id_is_not_flagged():
    GAMES.clear()
    slug = _enroll(["6631503001", "6631503002"])
    GAMES["444401"] = GameSession("444401", QUESTIONS, course_slug=slug)

    real = socketio.test_client(app)
    real.emit("player_join", {"pin": "444401", "nickname": "6631503001"})
    ok = [e for e in real.get_received() if e["name"] == "join_ok"]
    assert ok and not ok[0]["args"][0]["id_mismatch"]


def test_nickname_not_matching_any_enrolled_id_is_flagged():
    GAMES.clear()
    slug = _enroll(["6631503003", "6631503004"])
    GAMES["444402"] = GameSession("444402", QUESTIONS, course_slug=slug)

    typo = socketio.test_client(app)
    typo.emit("player_join", {"pin": "444402", "nickname": "some nickname"})
    ok = [e for e in typo.get_received() if e["name"] == "join_ok"]
    assert ok and ok[0]["args"][0]["id_mismatch"] is True


def test_mismatch_warning_does_not_block_joining():
    # the whole point is a nudge, not a gate — a mismatched nickname still gets in
    GAMES.clear()
    slug = _enroll(["6631503005"])
    GAMES["444403"] = GameSession("444403", QUESTIONS, course_slug=slug)

    typo = socketio.test_client(app)
    typo.emit("player_join", {"pin": "444403", "nickname": "definitely not an id"})
    ok = [e for e in typo.get_received() if e["name"] == "join_ok"]
    assert ok  # still joined despite the mismatch
    assert "444403" in GAMES and "definitely not an id" in GAMES["444403"].players


def test_no_enrollment_data_skips_validation_entirely(tmp_path):
    # A course nobody has issued slips for yet must not flag anyone — graceful
    # degradation, same principle as the ledger's unmatched-row handling. This
    # exercises nickname_matches_roster directly against a freshly isolated DB
    # (no enrollments possible) rather than the shared cross-test app DB, which
    # by this point in the suite already has real enrollments from the tests
    # above — a real "empty roster" state can't be relied on there.
    from app import nickname_matches_roster

    conn = dbmod.connect(str(tmp_path / "empty.db"))
    dbmod.init_db(conn, default_course=C.COURSES[0]["slug"])
    assert nickname_matches_roster(conn, C.COURSES[0]["slug"], "whatever i typed")

