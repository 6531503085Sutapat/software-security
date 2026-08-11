"""Route tests for the unified /code entry point.

/quiz and /submit still exist and still work on their own (test_assess_routes.py,
test_submit_routes.py); this is the one page that accepts either a quiz code or
a submission code without the student knowing in advance which kind they hold.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

INVITE = "LETMEIN"


def _csrf(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert m, "no CSRF token in the rendered form"
    return m.group(1)


@pytest.fixture
def appmod(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("INVITE_CODE", INVITE)
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    import importlib
    import app as _a
    importlib.reload(_a)
    _a.app.config["TESTING"] = True
    return _a


@pytest.fixture
def client(appmod):
    return appmod.app.test_client()


@pytest.fixture
def teacher(client):
    html = client.get("/register").get_data(as_text=True)
    client.post("/register", data={
        "csrf_token": _csrf(html), "username": "teach1",
        "password": "correct horse battery", "invite": INVITE})
    return client


@pytest.fixture
def quiz_code(teacher, appmod):
    import assessment as A
    conn = appmod.get_db()
    tid = conn.execute("SELECT id FROM teachers WHERE username='teach1'").fetchone()["id"]
    aid = A.publish(conn, teacher_id=tid, title="Q",
                    questions=[{"stem": "q?", "options": ["a", "b"], "correct": 0}],
                    now="2026-08-15T08:00:00")
    return A.issue_codes(conn, aid, ["65310001"], "2026-08-15T08:00:00")["65310001"]


@pytest.fixture
def submit_code(teacher, appmod):
    import submission as S
    conn = appmod.get_db()
    tid = conn.execute("SELECT id FROM teachers WHERE username='teach1'").fetchone()["id"]
    wid = S.create_assignment(conn, teacher_id=tid, title="W", now="2026-08-15T08:00:00")
    return S.issue_codes(conn, wid, ["65310002"], "2026-08-15T08:00:00")["65310002"]


def test_get_renders_a_form(client):
    html = client.get("/code").get_data(as_text=True)
    assert 'name="code"' in html and 'name="csrf_token"' in html


def test_a_valid_quiz_code_redirects_into_the_quiz(client, quiz_code):
    html = client.get("/code").get_data(as_text=True)
    r = client.post("/code", data={"csrf_token": _csrf(html), "code": quiz_code},
                    follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/quiz/take" in r.headers["Location"]
    assert client.get("/quiz/take").status_code == 200   # session really set


def test_a_valid_submit_code_redirects_into_the_workspace(client, submit_code):
    html = client.get("/code").get_data(as_text=True)
    r = client.post("/code", data={"csrf_token": _csrf(html), "code": submit_code},
                    follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/submit/work" in r.headers["Location"]
    assert client.get("/submit/work").status_code == 200


def test_an_unknown_code_is_refused_without_leaking(client, quiz_code):
    html = client.get("/code").get_data(as_text=True)
    page = client.post("/code", data={"csrf_token": _csrf(html),
                                      "code": "ZZZZZZZZ"}).get_data(as_text=True)
    assert "valid" in page.lower()
    assert quiz_code not in page


def test_an_already_submitted_quiz_code_shows_its_real_message(client, appmod, quiz_code):
    # find_kind() correctly says "quiz" — the redeem-then-catch ordering must
    # not swallow the real reason into a generic "not valid".
    import assessment as A
    conn = appmod.get_db()
    att = A.redeem(conn, quiz_code, "2026-08-15T08:05:00")
    A.submit(conn, att, "2026-08-15T08:10:00")

    html = client.get("/code").get_data(as_text=True)
    r = client.post("/code", data={"csrf_token": _csrf(html), "code": quiz_code})
    assert r.status_code == 200
    assert "already submitted" in r.get_data(as_text=True).lower()


def test_missing_csrf_is_rejected(client, quiz_code):
    r = client.post("/code", data={"code": quiz_code})
    assert r.status_code == 400


def test_a_code_in_both_tables_is_refused_not_a_500(client, appmod, quiz_code):
    # Pathological cross-table collision (the generation-time guard prevents
    # this for new codes — see test_codes.py — so it's fabricated by hand).
    # find_kind() raises RuntimeError; /code calls it unconditionally before
    # either redeem(), so this must not turn into a 500.
    import submission as S
    conn = appmod.get_db()
    tid = conn.execute("SELECT id FROM teachers WHERE username='teach1'").fetchone()["id"]
    wid = S.create_assignment(conn, teacher_id=tid, title="W", now="2026-08-15T08:00:00")
    conn.execute(
        "INSERT INTO submit_codes (code, assignment_id, student_id, issued_at)"
        " VALUES (?, ?, 'x', ?)", (quiz_code, wid, "2026-08-15T08:00:00"))
    conn.commit()

    html = client.get("/code").get_data(as_text=True)
    r = client.post("/code", data={"csrf_token": _csrf(html), "code": quiz_code})
    assert r.status_code == 200
    assert "valid" in r.get_data(as_text=True).lower()
