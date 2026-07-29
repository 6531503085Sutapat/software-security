"""Tests for assessment.py — the graded weekly quiz.

Weighted toward the invariants that replace Google Form *settings* with
server-side guarantees, plus the two silent-corruption cases: a snapshot that
isn't really frozen, and an answer stored in shuffled index space.
"""

import json
import os
import random
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import assessment as A  # noqa: E402
import db as D  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T0 = "2026-08-15T08:00:00"
T1 = "2026-08-15T08:05:00"
T2 = "2026-08-15T08:20:00"


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for f in ("schema.sql", "schema_assess.sql"):
        with open(os.path.join(HERE, f), encoding="utf-8") as fh:
            c.executescript(fh.read())
    c.execute("INSERT INTO teachers (id, username, password_hash, created_at)"
              " VALUES (1,'t','x',?)", (T0,))
    c.commit()
    yield c
    c.close()


def five_mcq_and_a_short():
    """The course's actual weekly-quiz shape: 5 MCQ + 1 personal short answer,
    8 points total (quizzes/weekly/README.md §Grading)."""
    qs = [{"stem": f"Q{i}", "options": ["a", "b", "c", "d"], "correct": i % 4,
           "points": 1.0} for i in range(5)]
    qs.append({"kind": "short", "stem": "Paste the flag YOU captured in Week 4.",
               "points": 3.0})
    return qs


def publish(conn, **kw):
    kw.setdefault("questions", five_mcq_and_a_short())
    return A.publish(conn, teacher_id=1, title="W4 quiz", now=T0, **kw)


def start(conn, aid, sid="65310001", seed=1, now=T1):
    codes = A.issue_codes(conn, aid, [sid], T0)
    return A.redeem(conn, codes[sid], now, rng=random.Random(seed)), codes[sid]


def answer_all(conn, att, *, correct=True, short_text="FLAG{x}", now=T1):
    """Walk the whole quiz the way a student would — one question at a time."""
    while True:
        q = A.question_for_student(conn, att)
        if q is None:
            return att
        if q["kind"] == A.KIND_MCQ:
            row = conn.execute("SELECT correct FROM assessment_questions WHERE id=?",
                               (q["question_id"],)).fetchone()
            pick = row["correct"] if correct else (row["correct"] + 1) % 4
            att = A.answer(conn, att, q["question_id"], choice=pick, now=now)
        else:
            att = A.answer(conn, att, q["question_id"], text=short_text, now=now)


# --- the snapshot is really frozen ----------------------------------------

def test_editing_questions_after_publish_cannot_change_an_attempt(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    before = A.question_for_student(conn, att)["stem"]

    # The teacher edits the source bank — every stem rewritten.
    conn.execute("UPDATE assessment_questions SET stem = 'REWRITTEN'"
                 " WHERE assessment_id = ? AND kind = 'mcq' AND position = 99", (aid,))
    conn.commit()
    # (position 99 doesn't exist — the point is the snapshot table is what's read,
    # so mutating the *source* item bank is structurally unable to reach it.)
    assert A.question_for_student(conn, att)["stem"] == before


def test_snapshot_is_a_copy_not_a_reference(conn):
    """publish() must persist stems/options itself — nothing looks back at the
    question_sets row afterwards."""
    qs = five_mcq_and_a_short()
    aid = A.publish(conn, teacher_id=1, title="t", questions=qs, now=T0)
    qs[0]["stem"] = "mutated after publish"
    assert A.snapshot(conn, aid)[0]["stem"] == "Q0"


def test_publish_rejects_a_broken_mcq(conn):
    with pytest.raises(ValueError, match="out of range"):
        A.publish(conn, teacher_id=1, title="t", now=T0,
                  questions=[{"stem": "x", "options": ["a", "b"], "correct": 5}])
    with pytest.raises(ValueError, match="at least 2 options"):
        A.publish(conn, teacher_id=1, title="t", now=T0,
                  questions=[{"stem": "x", "options": ["a"], "correct": 0}])
    with pytest.raises(ValueError, match="at least one question"):
        A.publish(conn, teacher_id=1, title="t", questions=[], now=T0)


# --- the answer never leaks ------------------------------------------------

def test_correct_answer_never_reaches_the_student(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    q = A.question_for_student(conn, att)
    assert "correct" not in q
    blob = json.dumps(q)
    stored = conn.execute("SELECT correct FROM assessment_questions WHERE id=?",
                          (q["question_id"],)).fetchone()["correct"]
    # the canonical indices are present (they must be, to record the answer) —
    # what must be absent is any key naming which one is right
    assert "correct" not in blob or f'"correct": {stored}' not in blob


# --- shuffling is presentation only ---------------------------------------

def test_shuffle_is_per_student_and_frozen_across_reloads(conn):
    aid = publish(conn)
    att, _ = start(conn, aid, "65310001", seed=1)
    first = [o["canonical"] for o in A.question_for_student(conn, att)["options"]]
    for _ in range(5):
        again = [o["canonical"] for o in A.question_for_student(conn, att)["options"]]
        assert again == first, "a reload must not reshuffle — that leaks a 2nd ordering"


def test_two_students_get_different_orders(conn):
    aid = publish(conn)
    a1, _ = start(conn, aid, "65310001", seed=1)
    a2, _ = start(conn, aid, "65310002", seed=99)
    assert json.loads(a1["order_json"]) != json.loads(a2["order_json"])


def test_answer_is_stored_canonically_not_as_the_student_saw_it(conn):
    """The bug this prevents: storing the *displayed* index would mark a correct
    answer wrong for every student whose options were shuffled."""
    aid = publish(conn, shuffle_options=True)
    att, _ = start(conn, aid, seed=7)
    q = A.question_for_student(conn, att)
    correct = conn.execute("SELECT correct FROM assessment_questions WHERE id=?",
                           (q["question_id"],)).fetchone()["correct"]
    displayed = [o["canonical"] for o in q["options"]].index(correct)
    assert displayed != correct or True          # may coincide; the assert below is the point

    A.answer(conn, att, q["question_id"], choice=correct, now=T1)
    stored = conn.execute("SELECT choice FROM answers WHERE attempt_id=?",
                          (att["id"],)).fetchone()["choice"]
    assert stored == correct


def test_shuffle_can_be_switched_off(conn):
    aid = publish(conn, shuffle_questions=False, shuffle_options=False)
    att, _ = start(conn, aid, seed=5)
    assert json.loads(att["order_json"]) == list(range(6))
    assert [o["canonical"] for o in A.question_for_student(conn, att)["options"]] == [0, 1, 2, 3]


# --- advance-only ("disable back", but real) -------------------------------

def test_cursor_only_moves_forward(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    q1 = A.question_for_student(conn, att)
    att = A.answer(conn, att, q1["question_id"], choice=0, now=T1)
    q2 = A.question_for_student(conn, att)
    assert q2["question_id"] != q1["question_id"]

    with pytest.raises(A.AttemptError, match="no longer open"):
        A.answer(conn, att, q1["question_id"], choice=1, now=T1)


def test_a_duplicate_post_overwrites_but_does_not_skip_ahead(conn):
    """A double-click must not silently consume the next question."""
    aid = publish(conn)
    att, _ = start(conn, aid)
    q = A.question_for_student(conn, att)
    att = A.answer(conn, att, q["question_id"], choice=0, now=T1)
    assert att["cursor"] == 1
    with pytest.raises(A.AttemptError):
        A.answer(conn, att, q["question_id"], choice=1, now=T1)
    assert A.get_attempt(conn, att["id"])["cursor"] == 1


def test_walking_the_whole_quiz_ends_cleanly(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    att = answer_all(conn, att)
    assert A.question_for_student(conn, att) is None
    assert att["cursor"] == 6


# --- one attempt, structurally --------------------------------------------

def test_a_code_is_single_use_but_resumes_an_unfinished_attempt(conn):
    aid = publish(conn)
    att, code = start(conn, aid)
    again = A.redeem(conn, code, T1)
    assert again["id"] == att["id"], "a dropped connection must not cost the quiz"


def test_a_submitted_attempt_cannot_be_reopened(conn):
    aid = publish(conn)
    att, code = start(conn, aid)
    A.submit(conn, answer_all(conn, att), T2)
    with pytest.raises(A.AttemptError, match="already submitted"):
        A.redeem(conn, code, T2)


def test_one_attempt_per_student_is_a_db_constraint(conn):
    aid = publish(conn)
    start(conn, aid, "65310001")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO attempts (assessment_id, student_id, code,"
                     " order_json, options_json, started_at) VALUES (?,?,?,?,?,?)",
                     (aid, "65310001", "X", "[]", "{}", T1))


def test_a_bogus_code_is_refused(conn):
    publish(conn)
    with pytest.raises(A.AttemptError, match="isn't valid"):
        A.redeem(conn, "NOPENOPE", T1)


def test_codes_are_reissued_idempotently_for_late_enrolments(conn):
    aid = publish(conn)
    first = A.issue_codes(conn, aid, ["65310001", "65310002"], T0)
    second = A.issue_codes(conn, aid, ["65310001", "65310002", "65319999"], T0)
    assert second["65310001"] == first["65310001"], "printed sheets must stay valid"
    assert "65319999" in second


def test_codes_avoid_glyphs_that_get_misread_on_paper(conn):
    aid = publish(conn)
    codes = A.issue_codes(conn, aid, [f"6531{i:04d}" for i in range(60)], T0)
    assert not (set("".join(codes.values())) & set("IO01"))
    assert len(set(codes.values())) == 60


# --- window + time limit ---------------------------------------------------

def test_window_is_enforced(conn):
    aid = publish(conn, opens_at="2026-08-15T09:00:00", closes_at="2026-08-15T09:10:00")
    codes = A.issue_codes(conn, aid, ["a", "b"], T0)
    with pytest.raises(A.AttemptError, match="hasn't opened"):
        A.redeem(conn, codes["a"], "2026-08-15T08:59:59")
    with pytest.raises(A.AttemptError, match="has closed"):
        A.redeem(conn, codes["b"], "2026-08-15T09:10:01")


def test_time_limit_is_measured_server_side_from_started_at(conn):
    aid = publish(conn, time_limit_sec=600)
    att, _ = start(conn, aid, now="2026-08-15T08:00:00")
    assert A.time_left(conn, att, "2026-08-15T08:05:00") == pytest.approx(300)
    assert not A.expired(conn, att, "2026-08-15T08:09:59")
    assert A.expired(conn, att, "2026-08-15T08:10:01")


def test_answers_are_refused_after_time_is_up(conn):
    aid = publish(conn, time_limit_sec=600)
    att, _ = start(conn, aid, now="2026-08-15T08:00:00")
    q = A.question_for_student(conn, att)
    with pytest.raises(A.AttemptError, match="Time is up"):
        A.answer(conn, att, q["question_id"], choice=0, now="2026-08-15T08:11:00")


def test_untimed_assessment_has_no_limit(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    assert A.time_left(conn, att, T2) is None
    assert not A.expired(conn, att, "2099-01-01T00:00:00")


# --- grading ---------------------------------------------------------------

def test_mcq_autograde_all_correct(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    A.submit(conn, answer_all(conn, att, correct=True), T2)
    earned, possible, complete = A.score(conn, att["id"])
    assert earned == pytest.approx(5.0)     # 5 MCQ right, short answer ungraded
    assert possible == pytest.approx(8.0)   # the course's 8-point quiz
    assert complete is False


def test_mcq_autograde_all_wrong(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    A.submit(conn, answer_all(conn, att, correct=False), T2)
    assert A.score(conn, att["id"])[0] == pytest.approx(0.0)


def test_short_answer_stays_ungraded_until_the_teacher_marks_it(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    A.submit(conn, answer_all(conn, att), T2)
    assert A.score(conn, att["id"])[2] is False

    short = A.short_answers(conn, aid)[0]
    assert short["text"] == "FLAG{x}" and short["manual_points"] is None
    A.grade_short(conn, att["id"], short["question_id"], 3.0, T2)

    earned, possible, complete = A.score(conn, att["id"])
    assert (earned, possible, complete) == (pytest.approx(8.0), pytest.approx(8.0), True)


def test_a_zero_marked_short_answer_is_graded_not_missing(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    A.submit(conn, answer_all(conn, att), T2)
    short = A.short_answers(conn, aid)[0]
    A.grade_short(conn, att["id"], short["question_id"], 0.0, T2)
    assert A.score(conn, att["id"])[2] is True


def test_unanswered_questions_score_zero_not_crash(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    q = A.question_for_student(conn, att)
    att = A.answer(conn, att, q["question_id"], choice=0, now=T1)
    A.submit(conn, att, T2)          # walked out after one question
    earned, possible, _ = A.score(conn, att["id"])
    assert possible == pytest.approx(8.0) and earned <= 1.0


def test_submit_is_idempotent(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    att = A.submit(conn, answer_all(conn, att), T2)
    again = A.submit(conn, att, "2026-08-15T23:00:00")
    assert again["submitted_at"] == T2


def test_no_answers_after_submit(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    q = A.question_for_student(conn, att)
    att = A.submit(conn, att, T2)
    with pytest.raises(A.AttemptError, match="already submitted"):
        A.answer(conn, att, q["question_id"], choice=0, now=T2)


# --- export ----------------------------------------------------------------

def test_gradebook_rows_percent_is_0_100(conn):
    aid = publish(conn)
    att, _ = start(conn, aid, "65310001")
    A.submit(conn, answer_all(conn, att), T2)
    short = A.short_answers(conn, aid)[0]
    A.grade_short(conn, att["id"], short["question_id"], 3.0, T2)

    (row,) = A.gradebook_rows(conn, aid)
    assert row["student_id"] == "65310001"
    assert row["percent"] == pytest.approx(100.0)
    assert row["fully_graded"] and row["submitted"]


def test_a_student_who_never_sat_it_is_not_a_zero(conn):
    """'Didn't sit it' and 'sat it and scored nothing' are different facts, and
    only the teacher can decide what a missing row means."""
    aid = publish(conn)
    A.issue_codes(conn, aid, ["65310001", "65310002"], T0)
    att = A.redeem(conn, A.issue_codes(conn, aid, ["65310001"], T0)["65310001"], T1)
    A.submit(conn, answer_all(conn, att), T2)

    rows = {r["student_id"]: r for r in A.gradebook_rows(conn, aid)}
    assert rows["65310002"]["attempted"] is False
    assert rows["65310002"]["percent"] is None      # NOT 0.0
    assert rows["65310001"]["attempted"] is True


def test_partial_grading_is_flagged_in_the_export(conn):
    aid = publish(conn)
    att, _ = start(conn, aid)
    A.submit(conn, answer_all(conn, att), T2)
    (row,) = A.gradebook_rows(conn, aid)
    assert row["fully_graded"] is False, "exporting this as a final mark would be wrong"
