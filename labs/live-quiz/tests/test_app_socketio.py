# tests/test_app_socketio.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import app, socketio, GAMES
from game import GameSession

QUESTIONS = [{"stem": "Q1?", "options": ["a", "b", "c", "d"], "correct": 1}]


def test_full_round_trip_join_question_answer_results():
    GAMES.clear()
    GAMES["999999"] = GameSession("999999", QUESTIONS)

    host = socketio.test_client(app)
    alice = socketio.test_client(app)
    bob = socketio.test_client(app)

    host.emit("host_join", {"pin": "999999"})
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

    host = socketio.test_client(app)
    alice = socketio.test_client(app)
    bob = socketio.test_client(app)
    host.emit("host_join", {"pin": "888888"})
    alice.emit("player_join", {"pin": "888888", "nickname": "alice"})
    bob.emit("player_join", {"pin": "888888", "nickname": "bob"})
    host.emit("host_next", {"pin": "888888"})
    host.get_received()  # clear

    bob.disconnect()  # bob closes his tab mid-question
    alice.emit("answer_submit", {"pin": "888888", "nickname": "alice", "choice": 1})

    # alice is now the only connected player, so the round reveals without waiting for the timer
    results = [e for e in host.get_received() if e["name"] == "question:results"]
    assert len(results) == 1


def test_joining_mid_question_shows_the_active_question():
    GAMES.clear()
    GAMES["777777"] = GameSession("777777", QUESTIONS)

    host = socketio.test_client(app)
    host.emit("host_join", {"pin": "777777"})
    host.emit("host_next", {"pin": "777777"})  # question is live before anyone joins

    late = socketio.test_client(app)
    late.emit("player_join", {"pin": "777777", "nickname": "late"})
    shown = [e for e in late.get_received() if e["name"] == "question:show"]
    assert len(shown) == 1  # the latecomer/reconnecter sees the in-progress question, not a blank wait
    assert shown[0]["args"][0]["stem"] == "Q1?"

