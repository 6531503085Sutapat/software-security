"""
assessment.py — graded weekly quizzes: publish, take, auto-grade, export.

Replaces the Google Form path in instructor/quizzes/weekly/README.md. That
README's anti-copying controls are *Form settings*; here they are server-side
invariants, which is a stronger position on every axis it lists:

    Form setting                     here
    ------------------------------   --------------------------------------------
    shuffle question order           per-student permutation frozen at attempt start
    shuffle option order             same, and answers are stored in CANONICAL index
                                     space so grading never depends on what they saw
    one question per page            `cursor` lives on the server
    disable "back"                   `cursor` is advance-only — not a browser hint
    limit 1 response per account     UNIQUE(assessment_id, student_id) + a one-time
                                     code that is burned on redemption
    collect email                    the roster's student_id IS the identity, and it
                                     is the same handle as CTFd / WireGuard / gradebook
    release scores later             `assessments.released`

The one real trade: we own the access path instead of Google. That is the point
of the exercise, not a regression.

WHAT MUST NEVER LEAK
    `correct` lives in the frozen snapshot and must not reach the client before
    submission. `question_for_student()` is the only rendering path and it does
    not carry it; `test_assessment.py` asserts that.

TIME
    Every timestamp is ISO-8601 UTC and is passed in by the caller rather than
    read from the clock here, so the whole module is testable without freezing
    time and a replayed sequence produces identical results.
"""

from __future__ import annotations

import json
import random
import secrets
import string

# Ambiguous glyphs dropped — these codes get printed on paper, read aloud, and
# typed by a room of students under time pressure.
CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits
                        if c not in "IO01")
CODE_LEN = 8

KIND_MCQ = "mcq"
KIND_SHORT = "short"


# --- publish ---------------------------------------------------------------

def publish(conn, *, teacher_id, title, questions, now, variant="A",
            shuffle_questions=True, shuffle_options=True,
            time_limit_sec=None, opens_at=None, closes_at=None,
            course_slug=None):
    """Freeze `questions` into a new assessment and return its id.

    `questions` is the shape `quiz_loader.parse_topics_from_text` produces —
    `{"stem", "options", "correct"}` — optionally with `kind` and `points`. A
    short-answer item (the course's Q6, the AI-resistant one) is
    `{"kind": "short", "stem": ..., "points": 3}` with no options.

    The snapshot is the whole point: after this returns, editing the source item
    bank cannot change what any student sees or how they are graded.
    """
    if not questions:
        raise ValueError("an assessment needs at least one question")

    import course_scope
    course = course_scope.check(course_slug)
    cur = conn.execute(
        "INSERT INTO assessments (teacher_id, course_slug, title, variant,"
        " shuffle_questions, shuffle_options, time_limit_sec, opens_at, closes_at,"
        " released, created_at) VALUES (?,?,?,?,?,?,?,?,?,0,?)",
        (teacher_id, course, title, variant, int(bool(shuffle_questions)),
         int(bool(shuffle_options)), time_limit_sec, opens_at, closes_at, now),
    )
    aid = cur.lastrowid

    for pos, q in enumerate(questions):
        kind = q.get("kind", KIND_MCQ)
        options = list(q.get("options") or [])
        correct = q.get("correct")
        if kind == KIND_MCQ:
            if len(options) < 2:
                raise ValueError(f"question {pos}: an MCQ needs at least 2 options")
            if correct is None or not 0 <= correct < len(options):
                raise ValueError(f"question {pos}: `correct` out of range")
        else:
            options, correct = [], None
        conn.execute(
            "INSERT INTO assessment_questions (assessment_id, position, kind, stem,"
            " options_json, correct, points) VALUES (?,?,?,?,?,?,?)",
            (aid, pos, kind, q["stem"], json.dumps(options, ensure_ascii=False),
             correct, float(q.get("points", 1.0))),
        )
    conn.commit()
    return aid


def issue_codes(conn, assessment_id, student_ids, now):
    """One single-use code per student. Idempotent — re-running keeps existing
    codes, so a late enrolment can be added without invalidating the sheets
    already printed for everyone else."""
    out = {}
    for sid in student_ids:
        row = conn.execute(
            "SELECT code FROM attempt_codes WHERE assessment_id = ? AND student_id = ?",
            (assessment_id, sid)).fetchone()
        if row:
            out[sid] = row["code"]
            continue
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))
            if not conn.execute("SELECT 1 FROM attempt_codes WHERE code = ?",
                                (code,)).fetchone():
                break
        conn.execute(
            "INSERT INTO attempt_codes (code, assessment_id, student_id, issued_at)"
            " VALUES (?,?,?,?)", (code, assessment_id, sid, now))
        out[sid] = code
    conn.commit()
    return out


def get_assessment(conn, assessment_id):
    return conn.execute("SELECT * FROM assessments WHERE id = ?",
                        (assessment_id,)).fetchone()


def snapshot(conn, assessment_id):
    return conn.execute(
        "SELECT * FROM assessment_questions WHERE assessment_id = ? ORDER BY position",
        (assessment_id,)).fetchall()


# --- taking ----------------------------------------------------------------

class AttemptError(Exception):
    """Refusal with a student-safe message — no internals, no hints."""


def redeem(conn, code, now, rng=None):
    """Exchange a one-time code for an attempt. Returns the attempt row.

    Re-entering the same code returns the SAME in-progress attempt (a dropped
    connection or a closed tab must not cost a student their quiz), but never
    reopens a submitted one.
    """
    row = conn.execute("SELECT * FROM attempt_codes WHERE code = ?",
                       ((code or "").strip().upper(),)).fetchone()
    if row is None:
        raise AttemptError("That code isn't valid.")

    existing = conn.execute(
        "SELECT * FROM attempts WHERE assessment_id = ? AND student_id = ?",
        (row["assessment_id"], row["student_id"])).fetchone()
    if existing is not None:
        if existing["submitted_at"]:
            raise AttemptError("You've already submitted this quiz.")
        return existing        # resume — deliberately not an error

    a = get_assessment(conn, row["assessment_id"])
    if a["opens_at"] and now < a["opens_at"]:
        raise AttemptError("This quiz hasn't opened yet.")
    if a["closes_at"] and now > a["closes_at"]:
        raise AttemptError("This quiz has closed.")

    qs = snapshot(conn, a["id"])
    rng = rng or random.Random()
    order = [q["position"] for q in qs]
    if a["shuffle_questions"]:
        rng.shuffle(order)

    opts = {}
    for q in qs:
        n = len(json.loads(q["options_json"]))
        perm = list(range(n))
        if a["shuffle_options"] and n:
            rng.shuffle(perm)
        opts[str(q["position"])] = perm

    cur = conn.execute(
        "INSERT INTO attempts (assessment_id, student_id, code, order_json,"
        " options_json, cursor, started_at) VALUES (?,?,?,?,?,0,?)",
        (a["id"], row["student_id"], row["code"], json.dumps(order),
         json.dumps(opts), now))
    conn.execute("UPDATE attempt_codes SET redeemed_at = ? WHERE code = ?",
                 (now, row["code"]))
    conn.commit()
    return conn.execute("SELECT * FROM attempts WHERE id = ?", (cur.lastrowid,)).fetchone()


def get_attempt(conn, attempt_id):
    return conn.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,)).fetchone()


def time_left(conn, attempt, now):
    """Seconds remaining, or None if untimed. Server-side; a browser countdown
    is decoration."""
    a = get_assessment(conn, attempt["assessment_id"])
    if not a["time_limit_sec"]:
        return None
    from datetime import datetime
    started = datetime.fromisoformat(attempt["started_at"])
    elapsed = (datetime.fromisoformat(now) - started).total_seconds()
    return max(0, a["time_limit_sec"] - elapsed)


def expired(conn, attempt, now):
    left = time_left(conn, attempt, now)
    return left is not None and left <= 0


def question_for_student(conn, attempt, now=None):
    """The current question, as this student sees it. Returns None when done.

    **Never carries `correct`.** This is the only path that renders a question to
    a student, so keeping the answer out of it here keeps it out everywhere.
    Options come back already permuted, each tagged with the CANONICAL index the
    answer will be stored under — so the shuffle is presentation-only and never
    reaches the grading path.
    """
    order = json.loads(attempt["order_json"])
    if attempt["submitted_at"] or attempt["cursor"] >= len(order):
        return None
    if now is not None and expired(conn, attempt, now):
        return None

    position = order[attempt["cursor"]]
    q = conn.execute(
        "SELECT * FROM assessment_questions WHERE assessment_id = ? AND position = ?",
        (attempt["assessment_id"], position)).fetchone()

    canonical = json.loads(q["options_json"])
    perm = json.loads(attempt["options_json"]).get(str(position), list(range(len(canonical))))
    return {
        "question_id": q["id"],
        "kind": q["kind"],
        "stem": q["stem"],
        "points": q["points"],
        "options": [{"canonical": i, "text": canonical[i]} for i in perm],
        "index": attempt["cursor"] + 1,
        "total": len(order),
    }


def answer(conn, attempt, question_id, *, choice=None, text=None, now):
    """Record an answer and advance. Advance-only: the cursor never goes back.

    A repeat POST for the same question (double-click, refresh) overwrites that
    answer but does not advance twice — otherwise one stray click silently skips
    the next question unanswered.
    """
    if attempt["submitted_at"]:
        raise AttemptError("You've already submitted this quiz.")
    if expired(conn, attempt, now):
        raise AttemptError("Time is up.")

    order = json.loads(attempt["order_json"])
    if attempt["cursor"] >= len(order):
        raise AttemptError("No question is open.")

    expected = conn.execute(
        "SELECT id FROM assessment_questions WHERE assessment_id = ? AND position = ?",
        (attempt["assessment_id"], order[attempt["cursor"]])).fetchone()
    if expected is None or expected["id"] != question_id:
        # Out-of-order POST: a stale form, a duplicate tab, or someone trying to
        # revisit. Refuse rather than record it against the wrong question.
        raise AttemptError("That question is no longer open.")

    already = conn.execute(
        "SELECT 1 FROM answers WHERE attempt_id = ? AND question_id = ?",
        (attempt["id"], question_id)).fetchone()
    conn.execute(
        "INSERT INTO answers (attempt_id, question_id, choice, text)"
        " VALUES (?,?,?,?) ON CONFLICT(attempt_id, question_id)"
        " DO UPDATE SET choice = excluded.choice, text = excluded.text",
        (attempt["id"], question_id, choice, text))
    if not already:
        conn.execute("UPDATE attempts SET cursor = cursor + 1 WHERE id = ?",
                     (attempt["id"],))
    conn.commit()
    return get_attempt(conn, attempt["id"])


def submit(conn, attempt, now):
    """Close the attempt and auto-grade the MCQs.

    Short answers get `manual_points = NULL` and wait for the teacher — an
    ungraded short answer must stay distinguishable from one graded zero, which
    is why this doesn't default it to 0.
    """
    if attempt["submitted_at"]:
        return get_attempt(conn, attempt["id"])

    rows = conn.execute(
        "SELECT a.id AS aid, a.choice, q.kind, q.correct, q.points"
        " FROM answers a JOIN assessment_questions q ON q.id = a.question_id"
        " WHERE a.attempt_id = ?", (attempt["id"],)).fetchall()
    for r in rows:
        if r["kind"] != KIND_MCQ:
            continue
        pts = r["points"] if (r["choice"] is not None and r["choice"] == r["correct"]) else 0.0
        conn.execute("UPDATE answers SET auto_points = ?, graded_at = ? WHERE id = ?",
                     (pts, now, r["aid"]))
    conn.execute("UPDATE attempts SET submitted_at = ? WHERE id = ?",
                 (now, attempt["id"]))
    conn.commit()
    return get_attempt(conn, attempt["id"])


# --- grading + export ------------------------------------------------------

def grade_short(conn, attempt_id, question_id, points, now):
    """Teacher-side grading of a short answer (the course's Q6)."""
    conn.execute(
        "UPDATE answers SET manual_points = ?, graded_at = ?"
        " WHERE attempt_id = ? AND question_id = ?",
        (float(points), now, attempt_id, question_id))
    conn.commit()


def score(conn, attempt_id):
    """(earned, possible, fully_graded) for one attempt.

    `fully_graded` is False while any short answer is still ungraded — the
    earned total is real but not final, and a caller that exports it as a grade
    without checking would be exporting a partial mark as a whole one.
    """
    rows = conn.execute(
        "SELECT a.auto_points, a.manual_points, q.kind, q.points"
        " FROM assessment_questions q"
        " LEFT JOIN answers a ON a.question_id = q.id AND a.attempt_id = ?"
        " WHERE q.assessment_id = (SELECT assessment_id FROM attempts WHERE id = ?)",
        (attempt_id, attempt_id)).fetchall()

    earned, possible, complete = 0.0, 0.0, True
    for r in rows:
        possible += r["points"]
        if r["kind"] == KIND_MCQ:
            earned += r["auto_points"] or 0.0
        else:
            if r["manual_points"] is None:
                complete = False
            else:
                earned += r["manual_points"]
    return earned, possible, complete


def gradebook_rows(conn, assessment_id):
    """Per-student results, in the shape instructor/gradebook/ consumes.

    `percent` is 0–100 because that is what the gradebook's quiz columns take
    (GRADEBOOK.md: "all inputs are 0–100%"). Students on the roster who never
    attempted appear with `attempted=False` and no score, rather than a 0 —
    "didn't sit it" and "sat it and scored nothing" are different facts, and
    only the teacher can decide which one a missing row means.
    """
    codes = conn.execute(
        "SELECT student_id FROM attempt_codes WHERE assessment_id = ? ORDER BY student_id",
        (assessment_id,)).fetchall()
    out = []
    for c in codes:
        att = conn.execute(
            "SELECT * FROM attempts WHERE assessment_id = ? AND student_id = ?",
            (assessment_id, c["student_id"])).fetchone()
        if att is None:
            out.append({"student_id": c["student_id"], "attempted": False,
                        "submitted": False, "earned": None, "possible": None,
                        "percent": None, "fully_graded": False})
            continue
        earned, possible, complete = score(conn, att["id"])
        out.append({
            "student_id": c["student_id"],
            "attempted": True,
            "submitted": bool(att["submitted_at"]),
            "earned": earned,
            "possible": possible,
            "percent": (earned / possible * 100) if possible else None,
            "fully_graded": complete,
        })
    return out


def short_answers(conn, assessment_id):
    """Every short answer awaiting (or holding) a mark — the teacher's grading
    queue, and the export that instructor/quizzes/weekly/verify_q6.py consumes
    to check each Q6 against that student's own CTFd capture."""
    return conn.execute(
        "SELECT t.student_id, t.id AS attempt_id, q.id AS question_id, q.stem,"
        "       q.points, a.text, a.manual_points"
        " FROM attempts t"
        " JOIN answers a ON a.attempt_id = t.id"
        " JOIN assessment_questions q ON q.id = a.question_id"
        " WHERE t.assessment_id = ? AND q.kind = ?"
        " ORDER BY t.student_id", (assessment_id, KIND_SHORT)).fetchall()
