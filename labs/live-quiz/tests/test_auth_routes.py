import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _client(tmp_path, monkeypatch, invite="LETMEIN"):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("INVITE_CODE", invite)
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    import importlib, app as appmod
    importlib.reload(appmod)
    appmod.app.config["TESTING"] = True
    return appmod, appmod.app.test_client()


def _csrf(client, path):
    import re
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def test_register_login_logout_flow(tmp_path, monkeypatch):
    appmod, c = _client(tmp_path, monkeypatch)
    tok = _csrf(c, "/register")
    r = c.post("/register", data={"username": "alice", "password": "pw123456",
                                  "invite": "LETMEIN", "csrf_token": tok}, follow_redirects=False)
    assert r.status_code in (302, 303)                 # registered -> redirect
    c.get("/logout")
    tok = _csrf(c, "/login")
    r = c.post("/login", data={"username": "alice", "password": "pw123456", "csrf_token": tok})
    assert r.status_code in (302, 303)                 # logged in -> redirect to console


def test_bad_invite_rejected(tmp_path, monkeypatch):
    appmod, c = _client(tmp_path, monkeypatch)
    tok = _csrf(c, "/register")
    r = c.post("/register", data={"username": "eve", "password": "pw123456",
                                  "invite": "WRONG", "csrf_token": tok})
    assert b"invite" in r.get_data().lower() and r.status_code == 200  # stayed on form


def test_console_requires_login(tmp_path, monkeypatch):
    appmod, c = _client(tmp_path, monkeypatch)
    r = c.get("/console", follow_redirects=False)
    assert r.status_code in (302, 303) and "/login" in r.headers["Location"]


def test_missing_csrf_rejected(tmp_path, monkeypatch):
    appmod, c = _client(tmp_path, monkeypatch)
    r = c.post("/login", data={"username": "x", "password": "y"})  # no csrf_token
    assert r.status_code == 400


def test_forged_csrf_token_rejected(tmp_path, monkeypatch):
    # a PRESENT-but-wrong token must hit the compare_digest mismatch path, not just the
    # absent-token guard — proves forged tokens are rejected at the route, not only in unit tests
    appmod, c = _client(tmp_path, monkeypatch)
    real = _csrf(c, "/login")
    r = c.post("/login", data={"username": "x", "password": "y", "csrf_token": real + "x"})
    assert r.status_code == 400


def test_unset_invite_closes_registration(tmp_path, monkeypatch):
    # INVITE_CODE unset ⇒ registration fully closed: no invite value should get through
    appmod, c = _client(tmp_path, monkeypatch, invite="")
    tok = _csrf(c, "/register")
    r = c.post("/register", data={"username": "eve", "password": "pw123456",
                                  "invite": "", "csrf_token": tok})
    assert r.status_code == 200 and b"invite" in r.get_data().lower()   # stayed on form, not created
    assert appmod.get_db().execute("SELECT COUNT(*) FROM teachers").fetchone()[0] == 0


def test_overlong_password_is_form_error_not_500(tmp_path, monkeypatch):
    # DELIBERATE DEVIATION FROM PLAN. bcrypt 5.x RAISES `ValueError: password cannot be longer
    # than 72 bytes` (it does NOT silently truncate like some older builds), so a >72-byte
    # password would 500 the register route inside hash_password. The route guards against it and
    # returns the form with an error at 200 instead. This test locks that behaviour in.
    appmod, c = _client(tmp_path, monkeypatch)
    tok = _csrf(c, "/register")
    r = c.post("/register", data={"username": "longpw", "password": "a" * 100,
                                  "invite": "LETMEIN", "csrf_token": tok})
    assert r.status_code == 200                         # NOT a 500
    body = r.get_data().lower()
    assert b"72" in r.get_data() or b"character" in body   # a helpful length message, not a stack trace
