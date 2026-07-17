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


# Platform T6: /host and /host/create are now login + owned-set gated (games come from a DB
# question set the logged-in teacher owns, not a mounted item-bank file), so an unauthenticated
# GET/POST no longer renders a page — it redirects to login. The actual host.html Jinja-render
# smoke test now lives in tests/test_platform_game.py::test_create_game_from_owned_set, which
# logs in, creates an owned set, and asserts the rendered response contains "GAME PIN".


def test_host_setup_page_redirects_when_logged_out():
    client = app.test_client()
    resp = client.get("/host", follow_redirects=False)
    assert resp.status_code in (302, 303)


def test_host_create_redirects_when_logged_out():
    GAMES.clear()
    client = app.test_client()
    resp = client.post("/host/create", data={"topic": "does-not-matter"}, follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert len(GAMES) == 0  # no session was minted for an unauthenticated request
