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
    resp = client.get("/play")
    assert resp.status_code == 200
    assert b"Game PIN" in resp.data


def test_root_is_the_course_front_door_not_the_game():
    """The bare hostname must mean "the course".

    `/` used to render the game-PIN box, which is what made `learn.zcr.ai`
    land a student on "enter a Game PIN" with no route to any coursework —
    the exact confusion the rename was meant to end.
    """
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code in (301, 302)
    assert resp.headers["Location"].endswith("/learn")


def test_front_door_links_to_the_live_game():
    """Moving the join screen must not strand the in-class game: the front door
    has to name it, or a student who types the bare host has no way back."""
    client = app.test_client()
    resp = client.get("/learn")
    assert b'href="/play"' in resp.data


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
