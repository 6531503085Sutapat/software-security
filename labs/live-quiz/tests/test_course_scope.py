"""tests/test_course_scope.py — graded work must know which course it belongs to.

Before this, `assessments`, `assignments` and `question_sets` were scoped to a
TEACHER and nothing else. With one course that is indistinguishable from being
scoped correctly. With three on the platform — and ten planned — it means a
teacher's console is one flat list of every quiz they have ever set, and grades
cannot be totalled per course at all.

The two things pinned here are the ones that fail silently:

  * **The migration must not lose rows.** A column added to a live table starts
    NULL, and NULL drops out of every `WHERE course_slug = ?`. An existing quiz
    would simply vanish from the console with no error anywhere.
  * **An unknown course must be REJECTED, not defaulted.** Filing a quiz under
    the first course would list it exactly where the teacher expected while
    putting it in front of the wrong cohort.
"""
from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import content as C  # noqa: E402
import course_scope  # noqa: E402
import db as dbmod  # noqa: E402
import assessment as A  # noqa: E402
import submission as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)


# ── the validator ──────────────────────────────────────────────────────────

def test_none_means_the_default_course():
    """Every caller that predates courses passes nothing and must keep working."""
    assert course_scope.check(None) == C.COURSES[0]["slug"]


def test_a_configured_course_passes_through():
    assert course_scope.check(C.COURSES[0]["slug"]) == C.COURSES[0]["slug"]


def test_an_unknown_course_is_rejected_not_defaulted():
    with pytest.raises(ValueError, match="unknown course"):
        course_scope.check("not-a-course")


def test_rejection_names_what_is_configured():
    """The error has to be actionable — a typo'd slug is the likely cause and the
    valid list is what tells the operator that."""
    with pytest.raises(ValueError) as e:
        course_scope.check("typo-here")
    assert C.COURSES[0]["slug"] in str(e.value)


# ── the migration, against a database built WITHOUT the column ──────────────

def _pre_migration_db(tmp_path):
    """A database exactly as production had it before course_slug existed:
    schema applied, then the column stripped back out."""
    p = tmp_path / "old.db"
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    for name in ("schema.sql", "schema_assess.sql", "schema_submit.sql"):
        with open(os.path.join(APP, name), encoding="utf-8") as fh:
            conn.executescript(fh.read())
    # SQLite can drop a column since 3.35; this reproduces the real old shape
    # rather than trusting a hand-written copy of it to stay in sync.
    for table in ("assessments", "assignments", "question_sets"):
        conn.execute(f"ALTER TABLE {table} DROP COLUMN course_slug")
    conn.commit()
    return conn


def test_migration_adds_the_column_to_an_existing_database(tmp_path):
    conn = _pre_migration_db(tmp_path)
    assert "course_slug" not in dbmod._column_names(conn, "assessments")
    dbmod.migrate(conn, default_course="software-security")
    assert "course_slug" in dbmod._column_names(conn, "assessments")
    assert "course_slug" in dbmod._column_names(conn, "assignments")
    assert "course_slug" in dbmod._column_names(conn, "question_sets")


def test_migration_is_idempotent(tmp_path):
    """It runs on every boot. SQLite has no ADD COLUMN IF NOT EXISTS, so an
    unguarded ALTER raises "duplicate column name" the second time."""
    conn = _pre_migration_db(tmp_path)
    dbmod.migrate(conn, default_course="software-security")
    dbmod.migrate(conn, default_course="software-security")   # must not raise
    dbmod.migrate(conn, default_course="software-security")


def test_migration_backfills_existing_rows_so_they_do_not_vanish(tmp_path):
    """The row-loss case. A pre-existing quiz gets course_slug NULL, and NULL
    fails `WHERE course_slug = ?` — the teacher's quiz would disappear from the
    console with nothing logged and nothing to notice."""
    conn = _pre_migration_db(tmp_path)
    conn.execute("INSERT INTO teachers (username, password_hash, created_at)"
                 " VALUES ('t','x','now')")
    tid = conn.execute("SELECT id FROM teachers").fetchone()["id"]
    conn.execute("INSERT INTO assessments (teacher_id, title, variant,"
                 " shuffle_questions, shuffle_options, time_limit_sec, opens_at,"
                 " closes_at, released, created_at)"
                 " VALUES (?,'Old quiz','A',1,1,600,NULL,NULL,0,'now')", (tid,))
    conn.commit()

    dbmod.migrate(conn, default_course="software-security")

    row = conn.execute("SELECT course_slug FROM assessments").fetchone()
    assert row["course_slug"] == "software-security", (
        "a row written before the column existed must be adopted by the course "
        "that was the only one at the time, not left NULL")
    scoped = conn.execute(
        "SELECT COUNT(*) c FROM assessments WHERE course_slug = ?",
        ("software-security",)).fetchone()["c"]
    assert scoped == 1, "the backfilled row must survive a per-course query"


def test_migration_does_not_touch_rows_that_already_have_a_course(tmp_path):
    conn = _pre_migration_db(tmp_path)
    dbmod.migrate(conn, default_course="software-security")
    conn.execute("INSERT INTO teachers (username, password_hash, created_at)"
                 " VALUES ('t','x','now')")
    tid = conn.execute("SELECT id FROM teachers").fetchone()["id"]
    conn.execute("INSERT INTO assessments (teacher_id, course_slug, title, variant,"
                 " shuffle_questions, shuffle_options, time_limit_sec, opens_at,"
                 " closes_at, released, created_at)"
                 " VALUES (?,'cryptography','Crypto quiz','A',1,1,600,NULL,NULL,0,'n')",
                 (tid,))
    conn.commit()
    dbmod.migrate(conn, default_course="software-security")
    assert conn.execute("SELECT course_slug FROM assessments"
                        ).fetchone()["course_slug"] == "cryptography"


# ── the write path ─────────────────────────────────────────────────────────

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


QS = [{"stem": "q?", "options": ["a", "b"], "correct": 0}]


def test_published_assessment_records_its_course(db):
    aid = A.publish(db, teacher_id=_tid(db), title="Q", questions=QS, now="now")
    row = db.execute("SELECT course_slug FROM assessments WHERE id=?", (aid,)).fetchone()
    assert row["course_slug"] == C.COURSES[0]["slug"]


def test_publishing_into_an_unknown_course_raises_and_writes_nothing(db):
    before = db.execute("SELECT COUNT(*) c FROM assessments").fetchone()["c"]
    with pytest.raises(ValueError, match="unknown course"):
        A.publish(db, teacher_id=_tid(db), title="Q", questions=QS, now="now",
                  course_slug="ghost-course")
    after = db.execute("SELECT COUNT(*) c FROM assessments").fetchone()["c"]
    assert after == before, "a rejected course must not leave a partial row"


def test_assignment_records_its_course(db):
    aid = S.create_assignment(db, teacher_id=_tid(db), title="W", now="now")
    row = db.execute("SELECT course_slug FROM assignments WHERE id=?", (aid,)).fetchone()
    assert row["course_slug"] == C.COURSES[0]["slug"]


def test_assignment_into_an_unknown_course_raises_and_writes_nothing(db):
    before = db.execute("SELECT COUNT(*) c FROM assignments").fetchone()["c"]
    with pytest.raises(ValueError, match="unknown course"):
        S.create_assignment(db, teacher_id=_tid(db), title="W", now="now",
                            course_slug="ghost-course")
    assert db.execute("SELECT COUNT(*) c FROM assignments"
                      ).fetchone()["c"] == before


# ── with several courses configured, they stay apart ────────────────────────

@pytest.fixture
def three_courses(tmp_path, monkeypatch):
    roots = {}
    for slug in ("alpha", "beta"):
        d = tmp_path / slug / "week01-x"
        d.mkdir(parents=True)
        (d / "worksheet.md").write_text("# x\n")
        roots[slug] = str(tmp_path / slug)
    monkeypatch.setenv("COURSES", json.dumps(
        [{"slug": s, "title": s.title(), "root": r} for s, r in roots.items()]))
    importlib.reload(C)
    yield
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C)


def test_two_courses_quizzes_do_not_mix(db, three_courses):
    tid = _tid(db)
    a = A.publish(db, teacher_id=tid, title="Alpha Q", questions=QS, now="n",
                  course_slug="alpha")
    b = A.publish(db, teacher_id=tid, title="Beta Q", questions=QS, now="n",
                  course_slug="beta")
    alpha = db.execute("SELECT id FROM assessments WHERE course_slug='alpha'"
                       ).fetchall()
    beta = db.execute("SELECT id FROM assessments WHERE course_slug='beta'"
                      ).fetchall()
    assert [r["id"] for r in alpha] == [a]
    assert [r["id"] for r in beta] == [b]


def test_the_default_course_is_the_first_configured(db, three_courses):
    """With no slug given, a quiz lands in the first course — which is why
    passing None must stay an explicit, documented choice rather than a guess."""
    assert course_scope.check(None) == "alpha"
