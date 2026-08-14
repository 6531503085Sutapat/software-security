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


def test_a_submit_code_typed_into_quiz_rescues_into_the_workspace(client, appmod, published):
    # A student's slip carries both codes; typing the wrong one into this box
    # should land them where they meant to go, not just fail.
    import submission as S
    conn = appmod.get_db()
    tid = conn.execute("SELECT id FROM teachers WHERE username='teach1'").fetchone()["id"]
    wid = S.create_assignment(conn, teacher_id=tid, title="W", now="2026-08-15T08:00:00")
    subcodes = S.issue_codes(conn, wid, ["65310099"], "2026-08-15T08:00:00")

    html = client.get("/quiz").get_data(as_text=True)
    r = client.post("/quiz", data={"csrf_token": _csrf(html), "code": subcodes["65310099"]},
                    follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/submit/work" in r.headers["Location"]


def test_an_already_submitted_quiz_code_keeps_its_real_message_not_a_rescue(client, published):
    # It IS a quiz code (find_kind says "quiz", not "submit") — just a terminal
    # one. The rescue-attempt logic must not swallow the real refusal.
    aid, codes = published
    code = codes["65310001"]
    html = client.get("/quiz").get_data(as_text=True)
    client.post("/quiz", data={"csrf_token": _csrf(html), "code": code})
    for _ in range(10):
        page = client.get("/quiz/take").get_data(as_text=True)
        if "Thank you" in page:
            break
        qid = re.search(r'name="question_id" value="(\d+)"', page).group(1)
        data = {"csrf_token": _csrf(page), "question_id": qid}
        if 'name="choice"' in page:
            data["choice"] = re.search(r'name="choice" value="(\d+)"', page).group(1)
        else:
            data["text"] = "FLAG{mine}"
        client.post("/quiz/take", data=data)

    html2 = client.get("/quiz").get_data(as_text=True)
    page = client.post("/quiz", data={"csrf_token": _csrf(html2), "code": code}).get_data(as_text=True)
    assert "already submitted" in page.lower()


def test_a_terminal_quiz_code_that_also_collides_with_submit_is_refused_generically(
        client, appmod, published):
    # Pathological: this code is genuinely a terminal quiz code, but ALSO
    # exists in submit_codes (the cross-table guard in issue_codes() prevents
    # this for new codes — see test_codes.py — so it's fabricated by hand
    # here). find_kind() now runs unconditionally, before either redeem() is
    # attempted (see the collision-bypass test above), so it catches the
    # ambiguity itself rather than A.redeem() failing first — the specific
    # "already submitted" message is no longer reachable here. That's a
    # deliberate tradeoff: any detected collision refuses the same way
    # regardless of which side would have failed, matching /code's behavior,
    # rather than leaking which side happened to be checked first. The
    # student still gets a clean refusal, not a crash.
    aid, codes = published
    code = codes["65310001"]
    html = client.get("/quiz").get_data(as_text=True)
    client.post("/quiz", data={"csrf_token": _csrf(html), "code": code})
    for _ in range(10):
        page = client.get("/quiz/take").get_data(as_text=True)
        if "Thank you" in page:
            break
        qid = re.search(r'name="question_id" value="(\d+)"', page).group(1)
        data = {"csrf_token": _csrf(page), "question_id": qid}
        if 'name="choice"' in page:
            data["choice"] = re.search(r'name="choice" value="(\d+)"', page).group(1)
        else:
            data["text"] = "FLAG{mine}"
        client.post("/quiz/take", data=data)

    import submission as S
    conn = appmod.get_db()
    tid = conn.execute("SELECT id FROM teachers WHERE username='teach1'").fetchone()["id"]
    wid = S.create_assignment(conn, teacher_id=tid, title="W", now="2026-08-15T08:00:00")
    conn.execute(
        "INSERT INTO submit_codes (code, assignment_id, student_id, issued_at)"
        " VALUES (?, ?, 'x', ?)", (code, wid, "2026-08-15T08:00:00"))
    conn.commit()

    html2 = client.get("/quiz").get_data(as_text=True)
    r = client.post("/quiz", data={"csrf_token": _csrf(html2), "code": code})
    assert r.status_code == 200
    assert "valid" in r.get_data(as_text=True).lower()


def test_a_fresh_colliding_code_does_not_silently_authenticate_into_the_quiz(
        client, appmod, published):
    # The case find_kind()'s RuntimeError guard doesn't catch: a code that is
    # a genuinely fresh, still-redeemable quiz code for one student AND
    # (fabricated, mirroring test_codes.py) a submit code for a DIFFERENT
    # student. A.redeem() alone has no way to know the submit_codes row
    # exists, so it succeeds outright on its own terms. POSTing it to /quiz
    # must not redirect into a live attempt — the ambiguity must be refused,
    # not resolved by "whichever table happened to get checked first."
    aid, codes = published
    quiz_code = codes["65310001"]

    import submission as S
    conn = appmod.get_db()
    tid = conn.execute("SELECT id FROM teachers WHERE username='teach1'").fetchone()["id"]
    wid = S.create_assignment(conn, teacher_id=tid, title="W", now="2026-08-15T08:00:00")
    conn.execute(
        "INSERT INTO submit_codes (code, assignment_id, student_id, issued_at)"
        " VALUES (?, ?, '65310099', ?)", (quiz_code, wid, "2026-08-15T08:00:00"))
    conn.commit()

    html = client.get("/quiz").get_data(as_text=True)
    r = client.post("/quiz", data={"csrf_token": _csrf(html), "code": quiz_code},
                    follow_redirects=False)
    assert r.status_code not in (302, 303), (
        "a colliding code must not silently redirect into a live quiz attempt")
    still_untouched = conn.execute(
        "SELECT 1 FROM attempts WHERE assessment_id = ? AND student_id = '65310001'",
        (aid,)).fetchone()
    assert still_untouched is None, "no attempt should have been created for the ambiguous code"


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


def test_q6_csv_neutralizes_formula_injection_in_student_answer(teacher, student, published):
    """The short-answer text is the one field in these exports a student fully
    controls. A teacher opens this CSV in Excel/Sheets to grade it, so a cell
    starting with `=`/`+`/`-`/`@` must not reach the file as a live formula
    (CWE-1236 / OWASP CSV injection)."""
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
            data["text"] = "=SUM(1+1)"
        student.post("/quiz/take", data=data)

    rows = list(csv.DictReader(io.StringIO(
        teacher.get(f"/assess/{aid}/q6.csv").get_data(as_text=True))))
    answer = rows[0]["answer"]
    assert not answer.startswith(("=", "+", "-", "@")), (
        f"formula-injection payload reached the exported cell unescaped: {answer!r}")


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


def test_a_double_click_does_not_end_a_graded_attempt(client, published):
    """The route half of the StaleAnswer distinction, and the reason this test
    lives HERE and not only in test_assessment.py: the model raised a distinct,
    recoverable error all along, and /quiz/take caught every AttemptError alike
    and SUBMITTED the attempt. Model-level tests cannot see that — deleting the
    route's handler left them all green.

    Posting the same form twice is not exotic: a double-click, Back-then-resend,
    a second tab, a phone that retried one POST on a flaky connection. Before the
    fix, any of those ended a graded quiz with every remaining question
    unanswered, under the message "Time is up."
    """
    _, codes = published
    html = client.get("/quiz").get_data(as_text=True)
    client.post("/quiz", data={"csrf_token": _csrf(html), "code": codes["65310001"]})

    page = client.get("/quiz/take").get_data(as_text=True)
    qid = re.search(r'name="question_id" value="(\d+)"', page).group(1)
    payload = {"csrf_token": _csrf(page), "question_id": qid}
    # Question order is shuffled per attempt, so question 1 is an MCQ or the
    # short answer depending on the seed. Build whichever this one is.
    if 'name="choice"' in page:
        payload["choice"] = re.search(r'name="choice" value="(\d+)"', page).group(1)
    else:
        payload["text"] = "FLAG{mine}"

    client.post("/quiz/take", data=payload)            # the honest answer
    assert "2 of 4" in client.get("/quiz/take").get_data(as_text=True)

    client.post("/quiz/take", data=payload)            # the double-click
    after = client.get("/quiz/take").get_data(as_text=True)
    assert "Submitted" not in after and "Thank you" not in after, (
        "a repeat POST ended the attempt — the student just lost the rest of a "
        "graded quiz")
    assert "2 of 4" in after, "the student must land back on the open question"

    # and they can still finish and be scored on everything
    for _ in range(10):
        page = client.get("/quiz/take").get_data(as_text=True)
        if "Thank you" in page or "Submitted" in page:
            break
        qid = re.search(r'name="question_id" value="(\d+)"', page).group(1)
        data = {"csrf_token": _csrf(page), "question_id": qid}
        if 'name="choice"' in page:
            data["choice"] = re.search(r'name="choice" value="(\d+)"', page).group(1)
        else:
            data["text"] = "FLAG{mine}"
        client.post("/quiz/take", data=data)
    assert "Thank you" in client.get("/quiz/take").get_data(as_text=True)
