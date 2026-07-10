# tests/test_routes_render.py
"""Smoke tests that every page-rendering route actually renders. None of the
socketio-event tests exercise Flask's template loader, so a Jinja syntax error
(e.g. an HTML comment that accidentally contains {% %} and breaks parsing)
can slip through 100% green socket tests — this closes that gap."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import app, GAMES


def test_player_join_page_renders():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200


def test_host_setup_page_renders():
    client = app.test_client()
    resp = client.get("/host")
    assert resp.status_code == 200


def test_host_created_page_renders():
    GAMES.clear()
    client = app.test_client()
    resp = client.post("/host/create", data={"topic": "does-not-matter"})
    assert resp.status_code == 200
    assert b"Game PIN" in resp.data
    assert len(GAMES) == 1  # host_create() minted a fresh session
