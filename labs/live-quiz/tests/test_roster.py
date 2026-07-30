"""tests/test_roster.py — the roster the platform now knows about itself.

`students` used to be dead: no code read or wrote it, zero rows, and keyed
(teacher_id, student_id) so the same person taking three of this instructor's
courses would be three unrelated rows. The real roster lived in a text file
outside the platform.

What is pinned here is mostly about NOT losing things:

  * the drop that re-keys the old table refuses to run if it holds data;
  * enrolling is idempotent, because it happens every time slips are issued and
    slips get re-issued for late enrolments — a second run must not wipe a name
    already filled in, and must not fail;
  * one person in several courses is ONE person, which is the whole reason the
    old shape had to go.
"""
from __future__ import annotations

import json
import importlib
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import content as C  # noqa: E402
import db as dbmod  # noqa: E402
import roster  # noqa: E402
import assessment as A  # noqa: E402
import submission as S  # noqa: E402

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QS = [{"stem": "q?", "options": ["a", "b"], "correct": 0}]


@pytest.fixture
def db(tmp_path):
    conn = dbmod.connect(str(tmp_path / "t.db"))
    dbmod.init_db(conn, default_course=C.COURSES[0]["slug"])
    conn.execute("INSERT INTO teachers (username, password_hash, created_at)"
                 " VALUES ('t','x','now')")
    conn.commit()
    return conn


def _tid(conn):
    return conn.execute("SELECT id FROM teachers").fetchone()["id"]


# ── the drop is guarded ────────────────────────────────────────────────────

def _old_shape_db(tmp_path, with_rows=False):
    conn = sqlite3.connect(tmp_path / "old.db")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE teachers (id INTEGER PRIMARY KEY, username TEXT,
                               password_hash TEXT, created_at TEXT);
        CREATE TABLE students (
          id INTEGER PRIMARY KEY,
          teacher_id INTEGER NOT NULL REFERENCES teachers(id),
          student_id TEXT NOT NULL, name TEXT DEFAULT '', email TEXT DEFAULT '',
          created_at TEXT NOT NULL, UNIQUE (teacher_id, student_id));
    """)
    if with_rows:
        conn.execute("INSERT INTO teachers (username) VALUES ('t')")
        conn.execute("INSERT INTO students (teacher_id, student_id, name, created_at)"
                     " VALUES (1,'65310001','Somchai','now')")
    conn.commit()
    return conn


def test_the_old_empty_table_is_replaced(tmp_path):
    conn = _old_shape_db(tmp_path)
    dbmod._replace_dead_students_table(conn)
    assert not dbmod._column_names(conn, "students"), "old table should be gone"


def test_the_old_table_is_NOT_dropped_if_it_holds_data(tmp_path):
    """Dropping a table is the one migration that destroys data irrecoverably.
    It was safe here only because the table was provably dead — so the guard has
    to be the thing that proves it, every time, not a note in a commit message."""
    conn = _old_shape_db(tmp_path, with_rows=True)
    with pytest.raises(RuntimeError, match="holds 1 rows|1 rows"):
        dbmod._replace_dead_students_table(conn)
    kept = conn.execute("SELECT student_id FROM students").fetchone()
    assert kept["student_id"] == "65310001", "the row must still be there"


def test_replacing_is_idempotent(tmp_path):
    conn = _old_shape_db(tmp_path)
    dbmod._replace_dead_students_table(conn)
    dbmod._replace_dead_students_table(conn)      # no table now — must not raise


# ── enrolling ──────────────────────────────────────────────────────────────

def test_enroll_registers_person_and_enrolment(db):
    added = roster.enroll(db, course_slug=None, teacher_id=_tid(db),
                          student_ids=["65310001", "65310002"], now="now")
    assert added == ["65310001", "65310002"]
    assert [r["student_id"] for r in roster.enrolled(db, None)] == \
        ["65310001", "65310002"]


def test_enroll_is_idempotent(db):
    roster.enroll(db, course_slug=None, teacher_id=_tid(db),
                  student_ids=["65310001"], now="now")
    added = roster.enroll(db, course_slug=None, teacher_id=_tid(db),
                          student_ids=["65310001", "65310003"], now="later")
    assert added == ["65310003"], "only the newcomer is new"
    assert len(roster.enrolled(db, None)) == 2


def test_re_enrolling_does_not_erase_a_name_already_filled_in(db):
    """Slips are re-issued for late enrolments. If that overwrote the registrar
    details it would quietly blank the roster the second time it ran."""
    roster.enroll(db, course_slug=None, teacher_id=_tid(db),
                  student_ids=["65310001"], now="now")
    roster.set_details(db, "65310001", name="Somchai", email="s@mfu.ac.th")
    roster.enroll(db, course_slug=None, teacher_id=_tid(db),
                  student_ids=["65310001"], now="later")
    row = roster.enrolled(db, None)[0]
    assert row["name"] == "Somchai" and row["email"] == "s@mfu.ac.th"


def test_blank_and_whitespace_ids_are_skipped(db):
    """A pasted class list ends with a newline, and often a stray blank line."""
    roster.enroll(db, course_slug=None, teacher_id=_tid(db),
                  student_ids=["65310001", "", "   ", None], now="now")
    assert [r["student_id"] for r in roster.enrolled(db, None)] == ["65310001"]


def test_ids_are_trimmed(db):
    roster.enroll(db, course_slug=None, teacher_id=_tid(db),
                  student_ids=["  65310001  "], now="now")
    assert roster.enrolled(db, None)[0]["student_id"] == "65310001"


def test_enrolling_into_an_unknown_course_is_refused(db):
    with pytest.raises(ValueError, match="unknown course"):
        roster.enroll(db, course_slug="ghost", teacher_id=_tid(db),
                      student_ids=["65310001"], now="now")


# ── one person, several courses — the point of the re-key ───────────────────

@pytest.fixture
def two_courses(tmp_path, monkeypatch):
    for slug in ("alpha", "beta"):
        d = tmp_path / slug / "week01-x"
        d.mkdir(parents=True)
        (d / "worksheet.md").write_text("# x\n")
    monkeypatch.setenv("COURSES", json.dumps([
        {"slug": "alpha", "title": "Alpha", "root": str(tmp_path / "alpha")},
        {"slug": "beta", "title": "Beta", "root": str(tmp_path / "beta")},
    ]))
    importlib.reload(C)
    yield
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C)


def test_one_student_in_two_courses_is_one_person(db, two_courses):
    """The old (teacher_id, student_id) key made this two unrelated rows, so no
    query could ever total one student's work across courses."""
    roster.enroll(db, course_slug="alpha", teacher_id=_tid(db),
                  student_ids=["65310001"], now="now")
    roster.enroll(db, course_slug="beta", teacher_id=_tid(db),
                  student_ids=["65310001"], now="now")
    assert db.execute("SELECT COUNT(*) c FROM students").fetchone()["c"] == 1
    assert roster.courses_of(db, "65310001") == ["alpha", "beta"]


def test_each_course_roster_is_separate(db, two_courses):
    roster.enroll(db, course_slug="alpha", teacher_id=_tid(db),
                  student_ids=["65310001", "65310002"], now="now")
    roster.enroll(db, course_slug="beta", teacher_id=_tid(db),
                  student_ids=["65310003"], now="now")
    assert [r["student_id"] for r in roster.enrolled(db, "alpha")] == \
        ["65310001", "65310002"]
    assert [r["student_id"] for r in roster.enrolled(db, "beta")] == ["65310003"]
    assert roster.counts(db) == {"alpha": 2, "beta": 1}


# ── issuing slips is what writes the roster ────────────────────────────────

def test_issuing_quiz_codes_enrols_the_class(db):
    aid = A.publish(db, teacher_id=_tid(db), title="Q", questions=QS, now="now")
    A.issue_codes(db, aid, ["65310001", "65310002"], "now")
    assert [r["student_id"] for r in roster.enrolled(db, None)] == \
        ["65310001", "65310002"]


def test_issuing_worksheet_codes_enrols_the_class(db):
    aid = S.create_assignment(db, teacher_id=_tid(db), title="W", now="now")
    S.issue_codes(db, aid, ["65310009"], "now")
    assert [r["student_id"] for r in roster.enrolled(db, None)] == ["65310009"]


def test_slips_enrol_into_the_artifacts_own_course_not_a_guess(db, two_courses):
    """The course is read off the assessment, so a slip cannot enrol someone into
    a course other than the one they are being assessed in."""
    aid = A.publish(db, teacher_id=_tid(db), title="Beta Q", questions=QS,
                    now="now", course_slug="beta")
    A.issue_codes(db, aid, ["65310007"], "now")
    assert roster.courses_of(db, "65310007") == ["beta"]
    assert roster.enrolled(db, "alpha") == []


def test_re_issuing_slips_does_not_duplicate_enrolment(db):
    aid = A.publish(db, teacher_id=_tid(db), title="Q", questions=QS, now="now")
    A.issue_codes(db, aid, ["65310001"], "now")
    A.issue_codes(db, aid, ["65310001", "65310002"], "later")
    assert len(roster.enrolled(db, None)) == 2
    assert db.execute("SELECT COUNT(*) c FROM enrollments").fetchone()["c"] == 2
