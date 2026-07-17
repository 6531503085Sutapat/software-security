import os, sys, importlib, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SET_MD = "## Week 1\n1. 2+2? a) 3 · b) 4 ✓ · c) 5 · d) 6\n"


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("INVITE_CODE", "INV"); monkeypatch.setenv("SECRET_KEY", "s")
    import app as appmod; importlib.reload(appmod)
    appmod.app.config["TESTING"] = True
    return appmod


def _register(appmod, name="alice"):
    c = appmod.app.test_client()
    tok = re.search(r'name="csrf_token" value="([^"]+)"', c.get("/register").get_data(as_text=True)).group(1)
    c.post("/register", data={"username": name, "password": "pw123456", "invite": "INV", "csrf_token": tok})
    return c


def _tok(c, path="/console"):
    return re.search(r'name="csrf_token" value="([^"]+)"', c.get(path).get_data(as_text=True)).group(1)


def _alice_set_id(appmod):
    return appmod.dbmod.list_sets(
        appmod.get_db(),
        appmod.dbmod.get_teacher_by_username(appmod.get_db(), "alice")["id"],
    )[0]["id"]


def test_create_list_and_isolation(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    alice.post("/console/sets/new", data={"title": "W1", "source_md": SET_MD, "csrf_token": _tok(alice)})
    assert b"W1" in alice.get("/console").get_data()
    bob = _register(appmod, "bob")
    assert b"W1" not in bob.get("/console").get_data()          # bob doesn't see alice's set


def test_idor_edit_delete_blocked(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    alice.post("/console/sets/new", data={"title": "W1", "source_md": SET_MD, "csrf_token": _tok(alice)})
    set_id = appmod.dbmod.list_sets(appmod.get_db(),
                appmod.dbmod.get_teacher_by_username(appmod.get_db(), "alice")["id"])[0]["id"]
    bob = _register(appmod, "bob")
    # GET another teacher's set -> 404
    r = bob.get(f"/console/sets/{set_id}/edit")
    assert r.status_code == 404                                 # not bob's set
    # POST (update) another teacher's set -> 404, row untouched
    r = bob.post(f"/console/sets/{set_id}/edit",
                 data={"title": "HACKED", "source_md": SET_MD, "csrf_token": _tok(bob)})
    assert r.status_code == 404
    # POST (delete) another teacher's set -> 404
    r = bob.post(f"/console/sets/{set_id}/delete", data={"csrf_token": _tok(bob)})
    assert r.status_code == 404
    alice_id = appmod.dbmod.get_teacher_by_username(appmod.get_db(), "alice")["id"]
    survivor = appmod.dbmod.get_set(appmod.get_db(), set_id, alice_id)
    assert survivor is not None                                 # survives every IDOR attempt
    assert survivor["title"] == "W1"                            # and is completely unchanged


def test_owner_can_edit_own_set(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    alice.post("/console/sets/new", data={"title": "W1", "source_md": SET_MD, "csrf_token": _tok(alice)})
    set_id = _alice_set_id(appmod)
    r = alice.post(f"/console/sets/{set_id}/edit",
                   data={"title": "W1-updated", "source_md": SET_MD, "csrf_token": _tok(alice)},
                   follow_redirects=False)
    assert r.status_code in (302, 303)                          # saved -> redirect to console
    alice_id = appmod.dbmod.get_teacher_by_username(appmod.get_db(), "alice")["id"]
    assert appmod.dbmod.get_set(appmod.get_db(), set_id, alice_id)["title"] == "W1-updated"


def test_owner_edit_form_renders_prefilled(tmp_path, monkeypatch):
    # The "teacher clicks Edit" path: GET the edit form as the owner. Exercises set_form.html in
    # edit mode, including the {{ editing.id }} deref that builds the form's POST action.
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    alice.post("/console/sets/new", data={"title": "W1", "source_md": SET_MD, "csrf_token": _tok(alice)})
    set_id = _alice_set_id(appmod)
    r = alice.get(f"/console/sets/{set_id}/edit")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert f'action="/console/sets/{set_id}/edit"' in html      # posts back to the edit URL, not new
    assert 'value="W1"' in html                                 # title prefilled
    assert "Week 1" in html                                     # source_md prefilled in the textarea


def test_empty_set_refused(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    r = alice.post("/console/sets/new",
                   data={"title": "X", "source_md": "no questions here", "csrf_token": _tok(alice)})
    assert r.status_code == 200 and b"no questions" in r.get_data().lower()  # refused with a message


def test_preview_endpoint_counts(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    r = alice.post("/console/preview", data={"source_md": SET_MD, "csrf_token": _tok(alice)})
    assert r.status_code == 200 and b'"Week 1"' in r.get_data() and b'"count": 1' in r.get_data()


def test_console_routes_require_login(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    anon = appmod.app.test_client()
    for path in ("/console", "/console/sets/new", "/console/sets/1/edit"):
        r = anon.get(path, follow_redirects=False)
        assert r.status_code in (302, 303) and "/login" in r.headers["Location"]
    # state-changing POSTs are gated too (redirect to login before any CSRF check)
    for path in ("/console/sets/new", "/console/preview", "/console/sets/1/edit", "/console/sets/1/delete"):
        r = anon.post(path, data={"title": "x", "source_md": SET_MD}, follow_redirects=False)
        assert r.status_code in (302, 303) and "/login" in r.headers["Location"]


def test_missing_csrf_rejected(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    r = alice.post("/console/sets/new", data={"title": "x", "source_md": SET_MD})  # no csrf_token
    assert r.status_code == 400


def test_oversize_markdown_is_form_error_not_500(tmp_path, monkeypatch):
    # 150 KB is over the 100 KB source cap but under MAX_CONTENT_LENGTH (256 KB), so it reaches the
    # handler and gets the friendly 200 rejection rather than a 413 or a 500.
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    big = SET_MD + ("x" * (150 * 1024))
    r = alice.post("/console/sets/new",
                   data={"title": "big", "source_md": big, "csrf_token": _tok(alice)})
    assert r.status_code == 200 and b"too large" in r.get_data().lower()   # not a 500, not a 413
    assert appmod.dbmod.list_sets(appmod.get_db(),
              appmod.dbmod.get_teacher_by_username(appmod.get_db(), "alice")["id"]) == []  # nothing saved


def test_create_from_file_upload(tmp_path, monkeypatch):
    # exercises the _read_source file-upload branch (req.files["source_file"]), previously untested
    import io
    appmod = _app(tmp_path, monkeypatch)
    alice = _register(appmod, "alice")
    r = alice.post("/console/sets/new",
                   data={"title": "FromFile", "source_file": (io.BytesIO(SET_MD.encode()), "wk.md"),
                         "csrf_token": _tok(alice)},
                   content_type="multipart/form-data", follow_redirects=False)
    assert r.status_code in (302, 303)                                     # created -> redirect
    assert b"FromFile" in alice.get("/console").get_data()
