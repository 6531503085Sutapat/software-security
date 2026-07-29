"""End-to-end route tests for the graded quiz.

`test_assessment.py` covers the rules; this covers the HTTP surface — the guards
(auth, CSRF, cross-teacher access), the student journey through real requests,
and the exports. The one that matters most is
`test_correct_answer_is_not_in_the_rendered_page`: everything else can be right
and the quiz is still worthless if the answer ships in the HTML.
"""

import csv
import io
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
    """A freshly-reloaded app on its own throwaway DB — the pattern the rest of
    this suite uses (see test_auth_routes.py)."""
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
def student(appmod):
    """A SECOND client. `teacher` and `client` are the same object, so a student
    who clears the session would otherwise log the teacher out mid-test."""
    return appmod.app.test_client()


@pytest.fixture
def teacher(client):
    """Register a teacher; the returned client stays logged in as them."""
    html = client.get("/register").get_data(as_text=True)
    client.post("/register", data={
        "csrf_token": _csrf(html), "username": "teach1",
        "password": "correct horse battery", "invite": INVITE})
    return client


@pytest.fixture
def published(teacher, appmod):
    """A published 3-MCQ + 1-short quiz, with codes for two students."""
    import assessment as A
    conn = appmod.get_db()
    tid = conn.execute("SELECT id FROM teachers WHERE username='teach1'").fetchone()["id"]
    aid = A.publish(conn, teacher_id=tid, title="W4", now="2026-08-15T08:00:00",
                    questions=[
                        {"stem": "Q1", "options": ["a", "b", "c", "d"], "correct": 2},
                        {"stem": "Q2", "options": ["a", "b", "c", "d"], "correct": 0},
                        {"stem": "Q3", "options": ["a", "b", "c", "d"], "correct": 3},
                        {"kind": "short", "stem": "Your flag?", "points": 3.0},
                    ])
    codes = A.issue_codes(conn, aid, ["65310001", "65310002"], "2026-08-15T08:00:00")
    return aid, codes


# --- guards ----------------------------------------------------------------

@pytest.mark.parametrize("path", ["/assess", "/assess/new", "/assess/1",
                                  "/assess/1/codes.csv", "/assess/1/results.csv",
                                  "/assess/1/q6.csv"])
def test_teacher_routes_require_login(client, path):
    r = client.get(path)
    assert r.status_code in (302, 308) and "/login" in r.headers.get("Location", "")


def test_a_teacher_cannot_reach_another_teachers_quiz(client, published):
    aid, _ = published
    client.get("/logout")
    html = client.get("/register").get_data(as_text=True)
    client.post("/register", data={"csrf_token": _csrf(html), "username": "teach2",
                                   "password": "another good passphrase",
                                   "invite": INVITE})
    # 404, not 403 — probing IDs must not reveal which ones exist.
    assert client.get(f"/assess/{aid}").status_code == 404
    assert client.get(f"/assess/{aid}/results.csv").status_code == 404


def test_state_changing_posts_need_a_valid_csrf_token(teacher, published):
    aid, _ = published
    r = teacher.post(f"/assess/{aid}/codes",
                     data={"student_ids": "65319999", "csrf_token": "wrong"})
    assert r.status_code == 400


# --- the student journey ---------------------------------------------------

def test_a_student_walks_the_whole_quiz(client, published):
    aid, codes = published
    html = client.get("/quiz").get_data(as_text=True)
    r = client.post("/quiz", data={"csrf_token": _csrf(html),
                                   "code": codes["65310001"]})
    assert r.status_code == 302

    seen = 0
    for _ in range(10):
        page = client.get("/quiz/take").get_data(as_text=True)
        if "Submitted" in page or "Thank you" in page:
            break
        seen += 1
        qid = re.search(r'name="question_id" value="(\d+)"', page).group(1)
        data = {"csrf_token": _csrf(page), "question_id": qid}
        if 'name="choice"' in page:
            data["choice"] = re.search(r'name="choice" value="(\d+)"', page).group(1)
        else:
            data["text"] = "FLAG{mine}"
        client.post("/quiz/take", data=data)
    assert seen == 4, "should have seen exactly 3 MCQ + 1 short answer"
    assert "Thank you" in client.get("/quiz/take").get_data(as_text=True)


def test_correct_answer_is_not_in_the_rendered_page(client, appmod, published):
    """Everything else can be right and the quiz is still worthless if the
    answer ships in the HTML."""
    aid, codes = published
    html = client.get("/quiz").get_data(as_text=True)
    client.post("/quiz", data={"csrf_token": _csrf(html), "code": codes["65310001"]})

    # Question order is shuffled per student, so the short answer can come first.
    # Walk forward until an MCQ appears rather than assuming position 1 is one.
    checked = 0
    for _ in range(8):
        page = client.get("/quiz/take").get_data(as_text=True)
        if "Thank you" in page:
            break
        qid = int(re.search(r'name="question_id" value="(\d+)"', page).group(1))
        data = {"csrf_token": _csrf(page), "question_id": qid}
        if 'name="choice"' in page:
            conn = appmod.get_db()
            row = conn.execute("SELECT correct FROM assessment_questions"
                               " WHERE id = ?", (qid,)).fetchone()
            # All four canonical indices appear, in some order — which reveals
            # nothing about which is right. And nothing is pre-selected.
            values = sorted(int(v) for v in
                            re.findall(r'name="choice" value="(\d+)"', page))
            assert values == [0, 1, 2, 3]
            assert "checked" not in page
            assert f'>{row["correct"]}<' not in page   # never printed as a value
            checked += 1
            data["choice"] = "0"
        else:
            data["text"] = "x"
        client.post("/quiz/take", data=data)
    assert checked == 3, "should have inspected all three MCQ"


def test_an_unknown_code_is_refused_without_leaking(client, published):
    html = client.get("/quiz").get_data(as_text=True)
    page = client.post("/quiz", data={"csrf_token": _csrf(html),
                                      "code": "ZZZZZZZZ"}).get_data(as_text=True)
    assert "valid" in page and "Start" in page   # the refusal re-renders the entry form
    assert "65310001" not in page


def test_take_without_a_session_bounces_to_the_entry_form(client):
    r = client.get("/quiz/take")
    assert r.status_code == 302 and "/quiz" in r.headers["Location"]


def test_a_second_student_gets_their_own_attempt(client, appmod, published):
    aid, codes = published
    for sid in ("65310001", "65310002"):
        with client.session_transaction() as s:
            s.clear()
        html = client.get("/quiz").get_data(as_text=True)
        client.post("/quiz", data={"csrf_token": _csrf(html), "code": codes[sid]})
        assert client.get("/quiz/take").status_code == 200
    conn = appmod.get_db()
    n = conn.execute("SELECT COUNT(*) c FROM attempts WHERE assessment_id=?",
                     (aid,)).fetchone()["c"]
    assert n == 2


# --- teacher exports -------------------------------------------------------

def test_codes_csv_lists_every_student(teacher, published):
    aid, codes = published
    body = teacher.get(f"/assess/{aid}/codes.csv").get_data(as_text=True)
    rows = list(csv.DictReader(io.StringIO(body)))
    assert {r["student_id"] for r in rows} == {"65310001", "65310002"}
    assert {r["code"] for r in rows} == set(codes.values())


def test_results_csv_carries_fully_graded_so_a_partial_isnt_imported_as_final(
        teacher, student, published):
    aid, codes = published
    html = student.get("/quiz").get_data(as_text=True)
    student.post("/quiz", data={"csrf_token": _csrf(html), "code": codes["65310001"]})
    for _ in range(6):
        page = student.get("/quiz/take").get_data(as_text=True)
        if "Thank you" in page:
            break
        qid = re.search(r'name="question_id" value="(\d+)"', page).group(1)
        data = {"csrf_token": _csrf(page), "question_id": qid}
        if 'name="choice"' in page:
            data["choice"] = "0"
        else:
            data["text"] = "FLAG{mine}"
        student.post("/quiz/take", data=data)

    rows = {r["student_id"]: r for r in csv.DictReader(io.StringIO(
        teacher.get(f"/assess/{aid}/results.csv").get_data(as_text=True)))}
    assert rows["65310001"]["fully_graded"] == "0", "short answer isn't marked yet"
    assert rows["65310002"]["attempted"] == "0"
    assert rows["65310002"]["percent"] == "", "never sat it is not a zero"


def test_q6_csv_is_the_shape_verify_q6_consumes(teacher, student, published):
    aid, codes = published
    html = student.get("/quiz").get_data(as_text=True)
    student.post("/quiz", data={"csrf_token": _csrf(html), "code": codes["65310001"]})
    for _ in range(6):
        page = student.get("/quiz/take").get_data(as_text=True)
        if "Thank you" in page:
            break
        qid = re.search(r'name="question_id" value="(\d+)"', page).group(1)
        data = {"csrf_token": _csrf(page), "question_id": qid}
        if 'name="choice"' in page:
            data["choice"] = "0"
        else:
            data["text"] = "FLAG{sqli_ab12cd34}"
        student.post("/quiz/take", data=data)

    rows = list(csv.DictReader(io.StringIO(
        teacher.get(f"/assess/{aid}/q6.csv").get_data(as_text=True))))
    assert rows[0]["student_id"] == "65310001"
    assert rows[0]["answer"] == "FLAG{sqli_ab12cd34}"


def test_issuing_codes_is_idempotent_over_http(teacher, published):
    aid, codes = published
    page = teacher.get(f"/assess/{aid}").get_data(as_text=True)
    teacher.post(f"/assess/{aid}/codes",
                 data={"csrf_token": _csrf(page),
                       "student_ids": "65310001\n65310002\n65319999"})
    body = teacher.get(f"/assess/{aid}/codes.csv").get_data(as_text=True)
    rows = {r["student_id"]: r["code"] for r in csv.DictReader(io.StringIO(body))}
    assert rows["65310001"] == codes["65310001"], "printed sheets must stay valid"
    assert "65319999" in rows
