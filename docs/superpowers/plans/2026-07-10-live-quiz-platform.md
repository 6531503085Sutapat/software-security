# Live Quiz Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the single-classroom `labs/live-quiz/` app into a small multi-teacher platform —
teachers register (invite-code gated), log in, manage their own question sets in a web console, and
start games from them; students still join anonymously by PIN.

**Architecture:** Same Flask + Flask-SocketIO app + one SQLite DB file (persistent volume). The
Socket.IO game engine (`game.py`, `scoring.py`, in-memory `GAMES`, the round loop in `app.py`)
is unchanged — only the *source of a game's questions* changes from mounted files to a DB question
set the logged-in teacher owns. Full rationale: `docs/superpowers/specs/2026-07-10-live-quiz-platform-design.md`.

**Tech Stack:** Python 3.12, Flask, Flask-SocketIO/eventlet, SQLite (stdlib `sqlite3`), `bcrypt`,
pytest. No new runtime services.

**Working dir for every path below:** `labs/live-quiz/` (run tests from there:
`python3 -m pytest tests/ -q`). A venv with the deps + pytest already exists at `/tmp/lq-venv2`.

---

## File structure

- `db.py` (NEW) — SQLite connection, schema init, teacher + question_set query helpers.
- `schema.sql` (NEW) — table definitions.
- `auth.py` (NEW) — bcrypt hashing, register/login/logout logic, session helpers,
  `login_required`, CSRF token helpers.
- `quiz_loader.py` (MODIFY) — add `parse_topics_from_text(text)`; `parse_topics(path)` becomes a
  thin wrapper (so a stored set's markdown string can be parsed, not just a file).
- `app.py` (MODIFY) — DB init on boot; auth + console routes; `login_required` on `/host*`;
  game source = owned set; `GAME_OWNER` map for export ownership.
- `templates/login.html`, `templates/register.html`, `templates/console.html` (NEW).
- `templates/host.html` (MODIFY) — drop the file-topic dropdown (the set+topic is chosen in the
  console before this page is reached).
- `static/console.js` (NEW) — upload/paste → live parse preview. Reuse `static/style.css`.
- `requirements.txt` (MODIFY) — add `bcrypt>=4.1`.
- `docker-compose.yml` (MODIFY) — named volume for the DB; `SECRET_KEY` + `INVITE_CODE` env; drop
  item-bank bind-mounts; optional `IMPORT_ITEM_BANKS` one-time seed mount.
- `README.md` (MODIFY) — "Running as a shared platform" section; remove the now-fixed
  "host endpoints unauthenticated" known limitation.
- Tests under `tests/`: `test_db.py`, `test_auth.py`, `test_auth_routes.py`, `test_console.py`,
  `test_platform_game.py` (NEW); existing tests stay green.

DB path resolves from `DB_PATH` env (default `/data/live-quiz.db` in the container; tests pass a
`tmp_path` file). Never hardcode a single global path that tests can't override.

---

### Task 1: Database layer (`db.py` + `schema.sql`)

**Files:**
- Create: `labs/live-quiz/schema.sql`
- Create: `labs/live-quiz/db.py`
- Test: `labs/live-quiz/tests/test_db.py`

- [ ] **Step 1: Write `schema.sql`**

```sql
-- schema.sql — live-quiz platform tables. Applied idempotently at startup (db.init_db).
CREATE TABLE IF NOT EXISTS teachers (
  id            INTEGER PRIMARY KEY,
  username      TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS question_sets (
  id          INTEGER PRIMARY KEY,
  teacher_id  INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  source_md   TEXT NOT NULL,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sets_teacher ON question_sets(teacher_id);
```

- [ ] **Step 2: Write the failing test** — `tests/test_db.py`

```python
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import db


def _fresh(tmp_path):
    d = db.connect(str(tmp_path / "t.db"))
    db.init_db(d)
    return d


def test_init_is_idempotent(tmp_path):
    p = str(tmp_path / "t.db")
    db.init_db(db.connect(p)); db.init_db(db.connect(p))  # second call must not raise


def test_create_and_get_teacher(tmp_path):
    d = _fresh(tmp_path)
    tid = db.create_teacher(d, "alice", "hash1", now="2026-01-01")
    t = db.get_teacher_by_username(d, "alice")
    assert t["id"] == tid and t["password_hash"] == "hash1"


def test_duplicate_username_rejected(tmp_path):
    d = _fresh(tmp_path)
    db.create_teacher(d, "alice", "h", now="t")
    try:
        db.create_teacher(d, "alice", "h2", now="t")
        assert False, "expected an integrity error on duplicate username"
    except Exception:
        pass


def test_set_crud_and_owner_isolation(tmp_path):
    d = _fresh(tmp_path)
    a = db.create_teacher(d, "alice", "h", now="t")
    b = db.create_teacher(d, "bob", "h", now="t")
    sid = db.create_set(d, a, "W1", "## T\n1. q a) x ✓ · b) y", now="t")
    assert [s["title"] for s in db.list_sets(d, a)] == ["W1"]
    assert db.list_sets(d, b) == []                       # bob sees nothing
    assert db.get_set(d, sid, owner_id=a)["source_md"].startswith("## T")
    assert db.get_set(d, sid, owner_id=b) is None         # IDOR-safe: not bob's
    db.update_set(d, sid, owner_id=a, title="W1b", source_md="## T2\n1. q a) x ✓ · b) y", now="t2")
    assert db.get_set(d, sid, owner_id=a)["title"] == "W1b"
    assert db.delete_set(d, sid, owner_id=b) == 0         # bob can't delete alice's
    assert db.delete_set(d, sid, owner_id=a) == 1
    assert db.get_set(d, sid, owner_id=a) is None
```

- [ ] **Step 3: Run it, confirm it fails** — `python3 -m pytest tests/test_db.py -q` → `ModuleNotFoundError: db`.

- [ ] **Step 4: Write `db.py`**

```python
# db.py — SQLite access for the live-quiz platform (teachers + question_sets).
import os
import sqlite3

_SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def connect(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    with open(_SCHEMA, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def create_teacher(conn, username, password_hash, now):
    cur = conn.execute(
        "INSERT INTO teachers (username, password_hash, created_at) VALUES (?,?,?)",
        (username, password_hash, now),
    )
    conn.commit()
    return cur.lastrowid


def get_teacher_by_username(conn, username):
    return conn.execute("SELECT * FROM teachers WHERE username = ?", (username,)).fetchone()


def get_teacher(conn, teacher_id):
    return conn.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,)).fetchone()


def create_set(conn, teacher_id, title, source_md, now):
    cur = conn.execute(
        "INSERT INTO question_sets (teacher_id, title, source_md, created_at, updated_at)"
        " VALUES (?,?,?,?,?)",
        (teacher_id, title, source_md, now, now),
    )
    conn.commit()
    return cur.lastrowid


def list_sets(conn, teacher_id):
    return conn.execute(
        "SELECT * FROM question_sets WHERE teacher_id = ? ORDER BY updated_at DESC, id DESC",
        (teacher_id,),
    ).fetchall()


def get_set(conn, set_id, owner_id):
    # owner_id is mandatory: a teacher can only ever fetch their own set (no IDOR)
    return conn.execute(
        "SELECT * FROM question_sets WHERE id = ? AND teacher_id = ?", (set_id, owner_id)
    ).fetchone()


def update_set(conn, set_id, owner_id, title, source_md, now):
    cur = conn.execute(
        "UPDATE question_sets SET title = ?, source_md = ?, updated_at = ?"
        " WHERE id = ? AND teacher_id = ?",
        (title, source_md, now, set_id, owner_id),
    )
    conn.commit()
    return cur.rowcount


def delete_set(conn, set_id, owner_id):
    cur = conn.execute(
        "DELETE FROM question_sets WHERE id = ? AND teacher_id = ?", (set_id, owner_id)
    )
    conn.commit()
    return cur.rowcount
```

- [ ] **Step 5: Run tests, confirm pass** — `python3 -m pytest tests/test_db.py -q` → all pass.

- [ ] **Step 6: Commit**

```bash
git add labs/live-quiz/db.py labs/live-quiz/schema.sql labs/live-quiz/tests/test_db.py
git commit -m "Add SQLite db layer: teachers + question_sets with owner-scoped queries"
```

---

### Task 2: Parse question sets from text (`quiz_loader.py`)

**Files:**
- Modify: `labs/live-quiz/quiz_loader.py`
- Test: `labs/live-quiz/tests/test_quiz_loader.py` (add cases; keep existing)

A stored set is markdown *text*, not a file. Add a text entry point; make the existing
`parse_topics(path)` read the file then delegate, so there's one parser.

- [ ] **Step 1: Write the failing test** (append to `tests/test_quiz_loader.py`)

```python
def test_parse_topics_from_text_matches_file(tmp_path):
    import quiz_loader
    md = "## Week 1\n1. Q? a) x ✓ · b) y · c) z · d) w\n"
    p = tmp_path / "s.md"; p.write_text(md, encoding="utf-8")
    assert quiz_loader.parse_topics_from_text(md) == quiz_loader.parse_topics(str(p))


def test_parse_topics_from_text_shape():
    import quiz_loader
    t = quiz_loader.parse_topics_from_text("## T\n1. Q? a) A ✓ · b) B · c) C · d) D\n")
    assert list(t) == ["T"]
    assert t["T"][0]["correct"] == 0 and t["T"][0]["options"][0] == "A"
```

- [ ] **Step 2: Run it, confirm it fails** — `AttributeError: parse_topics_from_text`.

- [ ] **Step 3: Refactor `quiz_loader.py`.** Locate the current `def parse_topics(path):` that opens
  the file and loops over lines. Split it: keep the per-line loop in a new
  `parse_topics_from_text(text)` that iterates `text.splitlines()`, and make `parse_topics(path)`
  read the file and call it. Concretely:

```python
def parse_topics(path):
    with open(path, encoding="utf-8") as f:
        return parse_topics_from_text(f.read())


def parse_topics_from_text(text):
    topics = {}
    topic = "?"
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        h = re.match(r"^##\s+(.*)", line)
        if h:
            topic = h.group(1).strip()
            continue
        if not re.match(r"^\d+\.\s", line) or "✓" not in line:
            continue
        # ... (MOVE the rest of the original per-line body here unchanged:
        #      the a)-boundary match, option split, ✓→correct index, append) ...
    return topics
```
  (Preserve the existing parsing body exactly — only its source changes from a file handle to
  `text.splitlines()`.)

- [ ] **Step 4: Run tests, confirm pass** — `python3 -m pytest tests/test_quiz_loader.py -q` all pass (old + new).

- [ ] **Step 5: Commit**

```bash
git add labs/live-quiz/quiz_loader.py labs/live-quiz/tests/test_quiz_loader.py
git commit -m "quiz_loader: parse a set's markdown text, not only a file path"
```

---

### Task 3: Auth core (`auth.py`)

**Files:**
- Create: `labs/live-quiz/auth.py`
- Modify: `labs/live-quiz/requirements.txt` (add `bcrypt>=4.1`)
- Test: `labs/live-quiz/tests/test_auth.py`

- [ ] **Step 1: Add `bcrypt>=4.1` to `requirements.txt`** and `pip install bcrypt` into the venv:
  `/tmp/lq-venv2/bin/pip install 'bcrypt>=4.1' -q`.

- [ ] **Step 2: Write the failing test** — `tests/test_auth.py`

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import auth


def test_password_roundtrip():
    h = auth.hash_password("s3cret-pw")
    assert h != "s3cret-pw"                       # not plaintext
    assert auth.verify_password("s3cret-pw", h)
    assert not auth.verify_password("wrong", h)


def test_invite_code_check():
    assert auth.invite_ok("LETMEIN", "LETMEIN")
    assert not auth.invite_ok("nope", "LETMEIN")
    assert not auth.invite_ok("anything", "")     # unset invite code => registration closed


def test_csrf_token_verify():
    tok = auth.new_csrf_token()
    assert auth.csrf_ok(tok, tok)
    assert not auth.csrf_ok(tok, "other")
    assert not auth.csrf_ok(tok, None)
```

- [ ] **Step 3: Run it, confirm it fails** — `ModuleNotFoundError: auth`.

- [ ] **Step 4: Write `auth.py`**

```python
# auth.py — password hashing, invite-code registration gate, CSRF tokens, and a
# login_required guard for the platform's teacher-facing routes.
import functools
import hmac
import secrets

import bcrypt
from flask import session, redirect, url_for, request, abort


def hash_password(pw):
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(pw, stored_hash):
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), stored_hash.encode("ascii"))
    except (ValueError, AttributeError):
        return False


def invite_ok(supplied, configured):
    # constant-time compare; an empty/unset configured code closes registration entirely
    if not configured:
        return False
    return hmac.compare_digest(str(supplied or ""), str(configured))


def new_csrf_token():
    return secrets.token_urlsafe(32)


def csrf_ok(session_token, form_token):
    if not session_token or not form_token:
        return False
    return hmac.compare_digest(str(session_token), str(form_token))


def current_teacher_id():
    return session.get("teacher_id")


def login_required(view):
    @functools.wraps(view)
    def wrapped(*a, **kw):
        if current_teacher_id() is None:
            return redirect(url_for("login_page", next=request.path))
        return view(*a, **kw)
    return wrapped
```

- [ ] **Step 5: Run tests, confirm pass** — `python3 -m pytest tests/test_auth.py -q`.

- [ ] **Step 6: Commit**

```bash
git add labs/live-quiz/auth.py labs/live-quiz/requirements.txt labs/live-quiz/tests/test_auth.py
git commit -m "Add auth core: bcrypt hashing, invite-code gate, CSRF tokens, login_required"
```

---

### Task 4: Auth routes + templates (register / login / logout)

**Files:**
- Modify: `labs/live-quiz/app.py`
- Create: `labs/live-quiz/templates/login.html`, `labs/live-quiz/templates/register.html`
- Test: `labs/live-quiz/tests/test_auth_routes.py`

- [ ] **Step 1: Wire DB + config into `app.py`.** After the `socketio = SocketIO(...)` line, add:

```python
import auth
import db as dbmod
from flask import session, redirect, url_for, g

DB_PATH = os.environ.get("DB_PATH", "/data/live-quiz.db")
INVITE_CODE = os.environ.get("INVITE_CODE", "")
_conn = dbmod.connect(DB_PATH)
dbmod.init_db(_conn)
if not INVITE_CODE:
    print("WARNING: INVITE_CODE is unset — teacher registration is CLOSED until you set it.", flush=True)
if app.config["SECRET_KEY"] == "dev-not-secret-override-in-prod":
    print("WARNING: SECRET_KEY is the insecure default — set a real one before any real use.", flush=True)


def get_db():
    return _conn


@app.after_request
def _secure_cookie_headers(resp):
    return resp


app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
# SESSION_COOKIE_SECURE is set from env so local http dev still works, TLS prod is hardened:
if os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes"):
    app.config["SESSION_COOKIE_SECURE"] = True


def _issue_csrf():
    if "csrf" not in session:
        session["csrf"] = auth.new_csrf_token()
    return session["csrf"]


def _check_csrf():
    if not auth.csrf_ok(session.get("csrf"), request.form.get("csrf_token")):
        abort(400)
```

  (Add `abort` to the Flask import line: `from flask import Flask, render_template, request, send_file, session, redirect, url_for, abort`.)

- [ ] **Step 2: Write the failing test** — `tests/test_auth_routes.py`

```python
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
```

- [ ] **Step 3: Run it, confirm it fails** (routes/templates absent → 404/500).

- [ ] **Step 4: Add the routes to `app.py`** (place above the socket handlers):

```python
import datetime


def _now():
    return datetime.datetime.utcnow().isoformat(timespec="seconds")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html", csrf_token=_issue_csrf(), error=None)
    _check_csrf()
    username = (request.form.get("username") or "").strip()[:40]
    password = request.form.get("password") or ""
    if not auth.invite_ok(request.form.get("invite"), INVITE_CODE):
        return render_template("register.html", csrf_token=_issue_csrf(), error="Invalid invite code."), 200
    if len(username) < 3 or len(password) < 8:
        return render_template("register.html", csrf_token=_issue_csrf(),
                               error="Username ≥ 3 chars, password ≥ 8 chars."), 200
    if dbmod.get_teacher_by_username(get_db(), username):
        return render_template("register.html", csrf_token=_issue_csrf(), error="Username taken."), 200
    tid = dbmod.create_teacher(get_db(), username, auth.hash_password(password), _now())
    session["teacher_id"] = tid
    return redirect(url_for("console_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html", csrf_token=_issue_csrf(), error=None)
    _check_csrf()
    t = dbmod.get_teacher_by_username(get_db(), (request.form.get("username") or "").strip())
    if t and auth.verify_password(request.form.get("password") or "", t["password_hash"]):
        session.clear()
        session["teacher_id"] = t["id"]
        session["csrf"] = auth.new_csrf_token()
        return redirect(url_for("console_page"))
    return render_template("login.html", csrf_token=_issue_csrf(), error="Wrong username or password."), 200


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))
```

  (A minimal `console_page` stub is needed for `url_for` to resolve — add it now, fleshed out in
  Task 5: `@app.route("/console")` + `@auth.login_required` returning
  `render_template("console.html", ...)`; if `console.html` doesn't exist yet, return a plain
  string placeholder so this task's tests pass, then replace in Task 5.)

- [ ] **Step 5: Write `templates/login.html` and `templates/register.html`** — reuse the brand
  shell + `static/style.css` (`.pjoin`/`.join-card` classes from the redesigned player page work
  well here). Each form MUST include the hidden CSRF field and render `{{ error }}` when set:

```html
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in — KOSEN·KMITL Live Quiz</title><link rel="stylesheet" href="/static/style.css"></head>
<body><div class="pwrap"><section class="pjoin">
  <div class="mark"><div class="word"><span class="k">KOSEN</span><span class="dot">·</span><span class="m">KMITL</span></div>
    <div class="sub">Live Quiz · Teacher sign-in</div></div>
  <form class="join-card" method="post" action="/login">
    <h1>Sign in</h1>
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    {% if error %}<div class="join-err">{{ error }}</div>{% endif %}
    <div class="field"><label for="username">Username</label>
      <input id="username" name="username" autocomplete="username"></div>
    <div class="field"><label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password"></div>
    <button class="btn blue" type="submit">Sign in ▸</button>
    <p class="pdpa">New teacher? <a href="/register">Register with your invite code</a>.</p>
  </form></section></div></body></html>
```
  `register.html` mirrors this with `action="/register"`, an extra `invite` field, and a link back
  to `/login`. (These forms are real session-authenticated POSTs, so a genuine `csrf_token` is
  present — the Semgrep django-csrf rule won't fire, and no `nosemgrep` is needed.)

- [ ] **Step 6: Run tests, confirm pass** — `python3 -m pytest tests/test_auth_routes.py -q`. Also
  run the whole suite to be sure the DB-init-on-import didn't break existing tests:
  `python3 -m pytest tests/ -q` (set `DB_PATH` to a temp path via conftest or an env default so
  import doesn't try to write `/data`). **NOTE:** add a `tests/conftest.py` that sets
  `os.environ.setdefault("DB_PATH", "/tmp/lq-test.db")` and `INVITE_CODE`/`SECRET_KEY` defaults
  before app import, so existing socket tests that `import app` still load cleanly.

- [ ] **Step 7: Commit**

```bash
git add labs/live-quiz/app.py labs/live-quiz/templates/login.html labs/live-quiz/templates/register.html labs/live-quiz/tests/test_auth_routes.py labs/live-quiz/tests/conftest.py
git commit -m "Add teacher register/login/logout with CSRF + secure session cookies"
```

---

### Task 5: Teacher console — question-set CRUD + preview

**Files:**
- Modify: `labs/live-quiz/app.py`
- Create: `labs/live-quiz/templates/console.html`, `labs/live-quiz/static/console.js`
- Test: `labs/live-quiz/tests/test_console.py`

- [ ] **Step 1: Write the failing test** — `tests/test_console.py`

```python
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
    r = bob.get(f"/console/sets/{set_id}/edit")
    assert r.status_code == 404                                 # not bob's set
    r = bob.post(f"/console/sets/{set_id}/delete", data={"csrf_token": _tok(bob)})
    assert r.status_code == 404
    assert appmod.dbmod.get_set(appmod.get_db(), set_id,
             appmod.dbmod.get_teacher_by_username(appmod.get_db(), "alice")["id"]) is not None  # survives


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
```

- [ ] **Step 2: Run it, confirm it fails.**

- [ ] **Step 3: Add console routes to `app.py`** (replace the Task-4 `console_page` stub):

```python
import json as _json
import quiz_loader


def _parse_or_none(source_md):
    topics = quiz_loader.parse_topics_from_text(source_md or "")
    total = sum(len(v) for v in topics.values())
    return topics if total > 0 else None


@app.route("/console")
@auth.login_required
def console_page():
    sets = dbmod.list_sets(get_db(), auth.current_teacher_id())
    return render_template("console.html", sets=sets, csrf_token=_issue_csrf())


@app.route("/console/preview", methods=["POST"])
@auth.login_required
def console_preview():
    _check_csrf()
    topics = quiz_loader.parse_topics_from_text(request.form.get("source_md") or "")
    return app.response_class(
        _json.dumps({"topics": [{"topic": k, "count": len(v)} for k, v in topics.items()]}),
        mimetype="application/json",
    )


@app.route("/console/sets/new", methods=["POST"])
@auth.login_required
def console_set_new():
    _check_csrf()
    title = (request.form.get("title") or "").strip()[:120] or "Untitled set"
    source_md = _read_source(request)
    if _parse_or_none(source_md) is None:
        return _console_with_error("That set has no questions the parser can read — check the format."), 200
    dbmod.create_set(get_db(), auth.current_teacher_id(), title, source_md, _now())
    return redirect(url_for("console_page"))


@app.route("/console/sets/<int:set_id>/edit", methods=["GET", "POST"])
@auth.login_required
def console_set_edit(set_id):
    s = dbmod.get_set(get_db(), set_id, auth.current_teacher_id())
    if s is None:
        abort(404)                                   # not this teacher's set (IDOR-safe)
    if request.method == "GET":
        return render_template("console.html", sets=dbmod.list_sets(get_db(), auth.current_teacher_id()),
                               editing=s, csrf_token=_issue_csrf())
    _check_csrf()
    title = (request.form.get("title") or "").strip()[:120] or s["title"]
    source_md = _read_source(request)
    if _parse_or_none(source_md) is None:
        return _console_with_error("That set has no questions the parser can read — check the format."), 200
    dbmod.update_set(get_db(), set_id, auth.current_teacher_id(), title, source_md, _now())
    return redirect(url_for("console_page"))


@app.route("/console/sets/<int:set_id>/delete", methods=["POST"])
@auth.login_required
def console_set_delete(set_id):
    _check_csrf()
    if dbmod.delete_set(get_db(), set_id, auth.current_teacher_id()) == 0:
        abort(404)
    return redirect(url_for("console_page"))


def _read_source(req):
    # accept either a pasted textarea or an uploaded .md file (cap size to 256 KB)
    f = req.files.get("source_file")
    if f and f.filename:
        return f.read(256 * 1024).decode("utf-8", errors="replace")
    return req.form.get("source_md") or ""


def _console_with_error(msg):
    return render_template("console.html", sets=dbmod.list_sets(get_db(), auth.current_teacher_id()),
                           csrf_token=_issue_csrf(), error=msg)
```

- [ ] **Step 4: Write `templates/console.html`** — brand shell; list the teacher's sets (each with
  Edit / Delete[POST form] / "Start game" button that POSTs to `/host/create` with `set_id`);
  a create/edit form with a title, a `<textarea name="source_md">`, an optional
  `<input type="file" name="source_file">`, a hidden `csrf_token`, a "Preview" button (calls
  `/console/preview` via `console.js` and shows topic+count), and `{{ error }}`. Escape all
  user-supplied text with Jinja's autoescaping (don't use `|safe` on titles/markdown).

- [ ] **Step 5: Write `static/console.js`** — on "Preview" click, POST the textarea + csrf to
  `/console/preview`, render the returned `[{topic,count}]` into a preview box. Use the same
  `escapeHtml` helper pattern as the other static files for any interpolated text.

- [ ] **Step 6: Run tests, confirm pass** — `python3 -m pytest tests/test_console.py -q`, then the
  full suite.

- [ ] **Step 7: Commit**

```bash
git add labs/live-quiz/app.py labs/live-quiz/templates/console.html labs/live-quiz/static/console.js labs/live-quiz/tests/test_console.py
git commit -m "Add teacher console: create/edit/delete/preview question sets (owner-scoped)"
```

---

### Task 6: Wire game creation to an owned set + gate host/export

**Files:**
- Modify: `labs/live-quiz/app.py`, `labs/live-quiz/templates/host.html`
- Test: `labs/live-quiz/tests/test_platform_game.py`

- [ ] **Step 1: Write the failing test** — `tests/test_platform_game.py`

```python
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


def test_export_owner_only(tmp_path, monkeypatch):
    appmod = _app(tmp_path, monkeypatch)
    c_a, sid_a, csrf_a = _reg_with_set(appmod, "alice")
    c_a.post("/host/create", data={"set_id": sid_a, "topic": "Week 1", "csrf_token": csrf_a})
    pin = list(appmod.GAMES)[0]
    c_b, _, _ = _reg_with_set(appmod, "bob")
    assert c_b.get(f"/host/{pin}/export").status_code == 404        # not bob's game
    assert c_a.get(f"/host/{pin}/export").status_code == 200        # alice owns it
```

- [ ] **Step 2: Run it, confirm it fails.**

- [ ] **Step 3: Rewrite the host/export routes in `app.py`.** Remove the old file-mount source
  (`_DEFAULT_ITEM_BANKS`, `resolve_item_bank_paths`, `ITEM_BANK_PATHS`, `_topics`, and their
  startup warning) OR leave them only behind the optional `IMPORT_ITEM_BANKS` seed (Task 7).
  Replace the routes:

```python
GAME_OWNER = {}  # pin -> teacher_id, so only the creating teacher can export a game's results


@app.route("/host", methods=["GET"])
@auth.login_required
def host_page():
    # the set+topic are chosen in the console, which POSTs straight to /host/create;
    # a bare GET /host just sends the teacher to their console to pick one.
    return redirect(url_for("console_page"))


@app.route("/host/create", methods=["POST"])
@auth.login_required
def host_create():
    _check_csrf()
    tid = auth.current_teacher_id()
    s = dbmod.get_set(get_db(), int(request.form.get("set_id", 0) or 0), tid)
    if s is None:
        abort(404)                                   # not this teacher's set
    topics = quiz_loader.parse_topics_from_text(s["source_md"])
    topic = request.form.get("topic") or next(iter(topics), None)
    questions = topics.get(topic, [])
    if not questions:
        abort(400)
    pin = generate_pin()
    while pin in GAMES:
        pin = generate_pin()
    GAMES[pin] = GameSession(pin, questions)
    GAME_OWNER[pin] = tid
    return render_template("host.html", created_pin=pin)


@app.route("/host/<pin>/export")
@auth.login_required
def host_export(pin):
    game = GAMES.get(pin)
    if game is None or GAME_OWNER.get(pin) != auth.current_teacher_id():
        return "not found", 404                      # unknown OR not this teacher's game
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["nickname", "total_score", "correct_count", "avg_response_time_ms"])
    writer.writeheader(); writer.writerows(game.export_results())
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"quiz-{pin}-results.csv")
```

- [ ] **Step 4: Update `templates/host.html`** — delete the `{% if not created_pin %}` topic-form
  branch entirely (the console now owns set/topic selection); keep only the `created_pin` game/
  lobby/question/results/podium view. The page is only ever rendered with a `created_pin`.

- [ ] **Step 5: Add a per-set "Start game" control to `console.html`** (if not already in Task 5):
  for each set, a small form `POST /host/create` with a `topic` `<select>` populated from that
  set's parsed topics + hidden `set_id` + `csrf_token`. (The console route already has the parsed
  topics available; pass them to the template.)

- [ ] **Step 6: Run the full suite, confirm all green** — `python3 -m pytest tests/ -q` (old game/
  socket tests + all new ones).

- [ ] **Step 7: Commit**

```bash
git add labs/live-quiz/app.py labs/live-quiz/templates/host.html labs/live-quiz/templates/console.html labs/live-quiz/tests/test_platform_game.py
git commit -m "Games are created from an owned question set; host + export are login/owner gated"
```

---

### Task 7: Deploy config + docs (volume, env, README)

**Files:**
- Modify: `labs/live-quiz/docker-compose.yml`, `labs/live-quiz/Dockerfile`, `labs/live-quiz/README.md`

- [ ] **Step 1: Update `docker-compose.yml`**

```yaml
services:
  live-quiz:
    build: .
    ports: ["5050:5000"]
    environment:
      - SECRET_KEY=${SECRET_KEY:-change-me-in-real-deployment}
      - INVITE_CODE=${INVITE_CODE:-}        # unset => registration closed; set to open it
      - DB_PATH=/data/live-quiz.db
      - COOKIE_SECURE=${COOKIE_SECURE:-}    # set to 1 when served over TLS
    volumes:
      - live-quiz-data:/data                # teachers + question sets persist here
volumes:
  live-quiz-data:
```

- [ ] **Step 2: Ensure `/data` exists in the image.** In `Dockerfile`, before `CMD`, add
  `RUN mkdir -p /data`. (The named volume mounts over it, but this lets a volume-less run still work.)

- [ ] **Step 3: Update `README.md`** — add a "Running as a shared platform (multiple teachers)"
  section: set a strong `SECRET_KEY` + an `INVITE_CODE`, share the code with teachers, each
  registers once at `/register`, signs in, builds question sets in `/console`, and starts games
  from them; students still join at `/` by PIN. Note: back up the `live-quiz-data` volume (it holds
  accounts + sets); set `COOKIE_SECURE=1` behind TLS. **Remove** the "host endpoints have no
  authentication" bullet from Known limitations (now resolved) and note that host/console/export
  all require a teacher login.

- [ ] **Step 4: Full suite green + a real browser smoke run** (see Verification below). Commit:

```bash
git add labs/live-quiz/docker-compose.yml labs/live-quiz/Dockerfile labs/live-quiz/README.md
git commit -m "Deploy: DB volume + INVITE_CODE/SECRET_KEY/COOKIE_SECURE; document shared-platform mode"
```

---

## Verification (before finishing the branch)

1. `python3 -m pytest tests/ -q` — all green (existing 40 + new db/auth/console/platform tests).
2. Real browser run (Docker or `DB_PATH=./dev.db INVITE_CODE=letmein SECRET_KEY=dev python app.py`):
   register a teacher → create a set by pasting markdown (see preview count) → also try a `.md`
   upload → start a game → a second browser joins at `/` by PIN and plays a full round → export
   CSV as the owner → confirm a *second* teacher can't see/host/export the first's set/game →
   logout returns to `/login`.
3. Security sanity: anonymous `GET /console` and `GET /host` both redirect to `/login`; a POST
   without `csrf_token` is rejected (400); passwords are bcrypt in the DB (`sqlite3 dev.db
   'select password_hash from teachers'` shows `$2b$...`, never plaintext).

---

## Self-review

- **Spec coverage:** accounts (Task 3–4) · invite-code gate (Task 3–4) · per-teacher question sets
  + console CRUD + preview (Task 1, 5) · parse-from-text (Task 2) · game from owned set + host/
  export auth closing the old known-limitation (Task 6) · persistence volume + deploy docs +
  optional import (Task 7). All design sections map to a task.
- **Type/name consistency:** `dbmod` is the module alias in `app.py`; `db` is the module name the
  tests import directly — both point at `db.py` (tests `import db`, app does `import db as dbmod`).
  `auth.current_teacher_id()` reads `session["teacher_id"]`, set by both register and login.
  `get_set(..., owner_id=...)` is the single IDOR chokepoint used by edit/delete/host_create.
- **No placeholders:** every code step shows real code; the one intentional stub (`console_page`
  in Task 4) is explicitly replaced in Task 5, called out in both tasks.
- **Deferred to Task 7 (documented, not silent):** the optional `IMPORT_ITEM_BANKS` one-time seed
  is described in the spec but only wired if wanted — the plan removes the file-mount source in
  Task 6 and the README documents DB-only as the steady state, so nothing depends on the seed.
