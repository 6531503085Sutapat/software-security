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
    assert payload["leaderboard"][0]["nickname"] == "alice"  # alice scored, bob didn't
