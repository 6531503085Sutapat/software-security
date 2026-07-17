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
