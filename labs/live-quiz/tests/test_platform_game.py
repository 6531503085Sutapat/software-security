import os, sys, importlib, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
SET_MD = "## Week 1\n1. 2+2? a) 3 · b) 4 ✓ · c) 5 · d) 6\n2. Sky? a) blue ✓ · b) red\n"


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db")); monkeypatch.setenv("INVITE_CODE", "INV")
    monkeypatch.setenv("SECRET_KEY", "s")
    import app as appmod; importlib.reload(appmod); appmod.app.config["TESTING"] = True
    return appmod


def _reg_with_set(appmod, name):
    c = appmod.app.test_client()
    tok = re.search(r'value="([^"]+)"', c.get("/register").get_data(as_text=True))
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', c.get("/register").get_data(as_text=True)).group(1)
    c.post("/register", data={"username": name, "password": "pw123456", "invite": "INV", "csrf_token": csrf})
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', c.get("/console").get_data(as_text=True)).group(1)
    c.post("/console/sets/new", data={"title": "W1", "source_md": SET_MD, "csrf_token": csrf})
    sid = appmod.dbmod.list_sets(appmod.get_db(),
            appmod.dbmod.get_teacher_by_username(appmod.get_db(), name)["id"])[0]["id"]
    return c, sid, csrf


def test_host_requires_login(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    assert appmod.app.test_client().get("/host", follow_redirects=False).status_code in (302, 303)


def test_create_game_from_owned_set(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    c, sid, csrf = _reg_with_set(appmod, "alice")
    r = c.post("/host/create", data={"set_id": sid, "topic": "Week 1", "csrf_token": csrf})
    assert r.status_code == 200 and b"GAME PIN" in r.get_data().upper()
    pin = [p for p, g in appmod.GAMES.items()][0]
    assert len(appmod.GAMES[pin].questions) == 2                    # both questions loaded


def test_cannot_create_game_from_others_set(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, _ = _reg_with_set(appmod, "alice")
    c_b, _, csrf_b = _reg_with_set(appmod, "bob")
    r = c_b.post("/host/create", data={"set_id": sid_a, "topic": "Week 1", "csrf_token": csrf_b})
    assert r.status_code == 404                                    # bob can't host alice's set


def test_create_game_rejects_out_of_range_set_id(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    c, _, csrf = _reg_with_set(appmod, "alice")
    # A numerically valid but oversized id parses fine as a Python int, then overflows SQLite's
    # INTEGER — must 404 (fail closed), never 500.
    r = c.post("/host/create", data={"set_id": "99999999999999999999", "topic": "Week 1", "csrf_token": csrf})
    assert r.status_code == 404


def test_export_owner_only(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, csrf_a = _reg_with_set(appmod, "alice")
    c_a.post("/host/create", data={"set_id": sid_a, "topic": "Week 1", "csrf_token": csrf_a})
    pin = list(appmod.GAMES)[0]
    c_b, _, _ = _reg_with_set(appmod, "bob")
    assert c_b.get(f"/host/{pin}/export").status_code == 404        # not bob's game
    assert c_a.get(f"/host/{pin}/export").status_code == 200        # alice owns it


def _create_game(appmod, client, sid, csrf, topic="Week 1"):
    before = set(appmod.GAMES)
    r = client.post("/host/create", data={"set_id": sid, "topic": topic, "csrf_token": csrf})
    assert r.status_code == 200
    new_pins = set(appmod.GAMES) - before
    assert len(new_pins) == 1                                        # exactly one game was minted
    return new_pins.pop()


def test_host_next_rejected_from_non_owner_socket(tmp_path, monkeypatch):
    # The SocketIO layer must not trust "knows the PIN" as proof of host identity — a player
    # legitimately learns the PIN just by joining, so that alone can't authorize host_next.
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, csrf_a = _reg_with_set(appmod, "alice")
    pin = _create_game(appmod, c_a, sid_a, csrf_a)

    alice_sock = appmod.socketio.test_client(appmod.app, flask_test_client=c_a)
    alice_sock.emit("host_join", {"pin": pin})
    alice_sock.emit("host_next", {"pin": pin})
    assert any(e["name"] == "question:show" for e in alice_sock.get_received())
    assert appmod.GAMES[pin].current_index == 0                     # alice's legitimate call advanced it

    c_b, _, _ = _reg_with_set(appmod, "bob")                        # a real teacher, but not this game's owner
    bob_sock = appmod.socketio.test_client(appmod.app, flask_test_client=c_b)
    bob_sock.emit("host_join", {"pin": pin})                        # should fail to bind (not the owner)
    bob_sock.emit("host_next", {"pin": pin})
    assert not any(e["name"] == "question:show" for e in bob_sock.get_received())
    assert appmod.GAMES[pin].current_index == 0                     # unchanged — bob's call was a true no-op


def test_host_next_rejected_from_owner_of_a_different_game(tmp_path, monkeypatch):
    # Owning SOME game must not be enough to drive a DIFFERENT game — HOST_SIDS binding is
    # per-pin, not per-authenticated-teacher.
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, csrf_a = _reg_with_set(appmod, "alice")
    pin_a = _create_game(appmod, c_a, sid_a, csrf_a)

    c_b, sid_b, csrf_b = _reg_with_set(appmod, "bob")
    pin_b = _create_game(appmod, c_b, sid_b, csrf_b)                # bob owns a real, different game
    assert pin_a != pin_b

    bob_sock = appmod.socketio.test_client(appmod.app, flask_test_client=c_b)
    bob_sock.emit("host_join", {"pin": pin_a})                      # bob is authenticated, just not the owner
    bob_sock.emit("host_next", {"pin": pin_a})
    assert not any(e["name"] == "question:show" for e in bob_sock.get_received())
    assert appmod.GAMES[pin_a].current_index == -1                  # alice's game never started
    assert appmod.GAMES[pin_b].current_index == -1                  # bob's own game is untouched too


def test_host_join_does_not_bind_unauthorized_socket(tmp_path, monkeypatch):
    # Isolates that on_host_join's ownership check (not just on_host_next's guard) does real work.
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, csrf_a = _reg_with_set(appmod, "alice")
    pin = _create_game(appmod, c_a, sid_a, csrf_a)

    anon_sock = appmod.socketio.test_client(appmod.app)             # no flask_test_client -> unauthenticated
    anon_sock.emit("host_join", {"pin": pin})
    anon_sock.emit("host_next", {"pin": pin})
    assert not any(e["name"] == "question:show" for e in anon_sock.get_received())
    assert appmod.GAMES[pin].current_index == -1                    # game never started


def test_answer_submit_ignores_spoofed_nickname(tmp_path, monkeypatch):
    # The answering identity must come from the socket's own join record, not the payload —
    # otherwise any connected player can submit/score under another player's nickname.
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, csrf_a = _reg_with_set(appmod, "alice")
    pin = _create_game(appmod, c_a, sid_a, csrf_a)

    alice_sock = appmod.socketio.test_client(appmod.app, flask_test_client=c_a)
    alice_sock.emit("host_join", {"pin": pin})
    alice_sock.emit("host_next", {"pin": pin})                      # question live; correct choice is index 1

    attacker_sock = appmod.socketio.test_client(appmod.app)
    attacker_sock.emit("player_join", {"pin": pin, "nickname": "attacker"})
    victim_sock = appmod.socketio.test_client(appmod.app)
    victim_sock.emit("player_join", {"pin": pin, "nickname": "victim"})
    attacker_sock.get_received()  # clear join/lobby noise

    # attacker's own socket answers, but claims to be "victim" in the payload
    attacker_sock.emit("answer_submit", {"pin": pin, "nickname": "victim", "choice": 1})

    assert appmod.GAMES[pin].players["attacker"].score > 0          # scored under the socket's OWN identity
    assert appmod.GAMES[pin].players["victim"].score == 0           # victim's real score untouched by the spoof
    fb = [e for e in attacker_sock.get_received() if e["name"] == "answer:feedback"]
    assert fb and fb[0]["args"][0]["score"] == appmod.GAMES[pin].players["attacker"].score


def test_answer_submit_before_join_is_noop(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, csrf_a = _reg_with_set(appmod, "alice")
    pin = _create_game(appmod, c_a, sid_a, csrf_a)

    alice_sock = appmod.socketio.test_client(appmod.app, flask_test_client=c_a)
    alice_sock.emit("host_join", {"pin": pin})
    alice_sock.emit("host_next", {"pin": pin})

    ghost_sock = appmod.socketio.test_client(appmod.app)            # never called player_join
    ghost_sock.emit("answer_submit", {"pin": pin, "nickname": "ghost", "choice": 0})
    assert "ghost" not in appmod.GAMES[pin].players
