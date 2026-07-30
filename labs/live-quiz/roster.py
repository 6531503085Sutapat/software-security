"""roster.py — who is enrolled in which course.

WHY THIS EXISTS, AND WHY IT REPLACES A TABLE RATHER THAN EXTENDING ONE

There was already a `students` table. Nothing read it, nothing wrote it, and it
held zero rows — the platform's real notion of a student was a bare text
`student_id` sitting in `attempt_codes` and `submit_codes`. So a student existed
only as a side effect of having been handed a code, and only within the one
assessment that code belonged to.

Its shape said as much: `UNIQUE (teacher_id, student_id)` makes a person a
property of a teacher. That is wrong in both directions once there is more than
one course. The same human taking three of this instructor's courses would be
three unrelated rows, so nothing could ever total their work across courses; and
a co-taught course (Cloud Infrastructure has two instructors) has no single
teacher to hang the roster on.

The shape here separates the two facts that were conflated:

    students     a PERSON. `student_id` is the registrar's own identifier, so it
                 is the natural key — there is no reason to mint a surrogate one
                 and then spend forever mapping back to it.
    enrollments  a person being IN a course, and which teacher owns that pairing.

That makes "the roster" a first-class thing the platform knows, rather than a
`students.txt` file living beside it, and it is the join that lets one student's
grades be totalled per course and across them.

It is written from the one place that already knows a real cohort: issuing code
slips. A teacher pasting their class list to generate slips IS the enrolment
event, so the roster stops being a separate chore that can drift.
"""
from __future__ import annotations

import course_scope


def enroll(conn, *, course_slug, teacher_id, student_ids, now):
    """Register people and their enrolment. Idempotent.

    Idempotence is the whole contract: this runs every time codes are issued, and
    codes are re-issued for late enrolments. A second run must add the newcomer
    and leave everyone else — including any name/email already filled in — alone.
    """
    course = course_scope.check(course_slug)
    added = []
    for raw in student_ids:
        sid = (raw or "").strip()
        if not sid:
            continue
        conn.execute(
            "INSERT INTO students (student_id, name, email, created_at)"
            " VALUES (?,'','',?) ON CONFLICT(student_id) DO NOTHING", (sid, now))
        cur = conn.execute(
            "INSERT INTO enrollments (course_slug, student_id, teacher_id, created_at)"
            " VALUES (?,?,?,?) ON CONFLICT(course_slug, student_id) DO NOTHING",
            (course, sid, teacher_id, now))
        if cur.rowcount:
            added.append(sid)
    conn.commit()
    return added


def enrolled(conn, course_slug):
    """Every student in one course, in the registrar's own ID order."""
    course = course_scope.check(course_slug)
    return conn.execute(
        "SELECT s.student_id, s.name, s.email, e.created_at"
        " FROM enrollments e JOIN students s ON s.student_id = e.student_id"
        " WHERE e.course_slug = ? ORDER BY s.student_id", (course,)).fetchall()


def courses_of(conn, student_id):
    """Which courses one person is in — the query the old shape made impossible."""
    return [r["course_slug"] for r in conn.execute(
        "SELECT course_slug FROM enrollments WHERE student_id = ?"
        " ORDER BY course_slug", (student_id,))]


def set_details(conn, student_id, *, name=None, email=None):
    """Fill in a name/email from the registrar export without disturbing enrolment."""
    if name is not None:
        conn.execute("UPDATE students SET name = ? WHERE student_id = ?",
                     (name, student_id))
    if email is not None:
        conn.execute("UPDATE students SET email = ? WHERE student_id = ?",
                     (email, student_id))
    conn.commit()


def counts(conn):
    """Enrolment per course, for the teacher console."""
    return {r["course_slug"]: r["n"] for r in conn.execute(
        "SELECT course_slug, COUNT(*) n FROM enrollments GROUP BY course_slug")}
