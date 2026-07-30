# db.py — SQLite access for the live-quiz platform (teachers + question_sets).
import os
import sqlite3

_HERE = os.path.dirname(os.path.abspath(__file__))
# Both are CREATE TABLE IF NOT EXISTS, applied in order on every startup, so an
# existing deployment picks up the assessment tables without a migration step.
_SCHEMAS = [os.path.join(_HERE, "schema.sql"),
            os.path.join(_HERE, "schema_assess.sql"),
            os.path.join(_HERE, "schema_submit.sql")]


def connect(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Migrations ─────────────────────────────────────────────────────────────
# The schema files are CREATE TABLE IF NOT EXISTS, which is idempotent for NEW
# tables and does nothing at all for a new COLUMN on an existing one. So an added
# column needs an explicit, guarded ALTER: SQLite has no ADD COLUMN IF NOT
# EXISTS, and a bare ALTER raises "duplicate column name" on the second boot.
#
# WHY course_slug IS A STRING AND NOT A FOREIGN KEY
# Courses are configured outside this database — $COURSES / the curriculum
# monorepo's courses/*.yml — because a course is an ordering over content
# directories, not a row someone maintains twice. A `courses` table here would
# be a second source of truth that drifts the first time a slug is renamed in one
# place and not the other. The write path validates the slug against the live
# course registry instead (see assessment.create_assessment /
# submission.create_assignment), so a bad value is rejected at the boundary
# rather than tolerated in storage.
_ADDED_COLUMNS = (
    # (table, column, type) — graded artifacts must know which course they belong
    # to. Without this a teacher of several courses gets one flat list of every
    # quiz they have ever set, and per-course grades cannot be totalled at all.
    ("assessments", "course_slug", "TEXT"),
    ("assignments", "course_slug", "TEXT"),
    ("question_sets", "course_slug", "TEXT"),
)


def _column_names(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _replace_dead_students_table(conn):
    """Re-key `students` from (teacher_id, student_id) to student_id.

    CREATE TABLE IF NOT EXISTS cannot change an existing table's shape, so the old
    one has to go — and dropping a table is the one migration that can destroy
    data irrecoverably. It is therefore guarded on being EMPTY. The table was
    dead when this was written (no code path read or wrote it, zero rows in
    production), so the guard should always pass; if it ever does not, something
    started using it and a silent drop would take that with it. Leave it and
    complain instead.
    """
    cols = _column_names(conn, "students")
    if not cols or "student_id" not in cols:
        return                                  # not created yet, or unrecognised
    if "teacher_id" not in cols:
        return                                  # already the new shape
    rows = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    if rows:
        raise RuntimeError(
            f"students still has the old (teacher_id, student_id) shape and holds "
            f"{rows} rows. Migrate them into students+enrollments by hand — this "
            f"will not drop data. See roster.py.")
    conn.execute("DROP TABLE students")
    conn.commit()

def migrate(conn, default_course=None):
    """Add columns the schema files cannot, and backfill them.

    Backfill matters: rows written before this existed have course_slug NULL, and
    a NULL would silently drop them out of every per-course query — a teacher's
    existing quiz would just vanish from the console. They are assigned
    `default_course` instead, which is the only course that existed when they
    were created.
    """
    for table, column, coltype in _ADDED_COLUMNS:
        existing = _column_names(conn, table)
        if not existing:
            continue                      # table not created yet; schema runs first
        if column in existing:
            continue
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
    if default_course:
        for table, column, _ in _ADDED_COLUMNS:
            if column in _column_names(conn, table):
                conn.execute(
                    f"UPDATE {table} SET {column} = ? WHERE {column} IS NULL",
                    (default_course,))
    conn.commit()


def init_db(conn, default_course=None):
    # Before the schema files run: a `students` table left over in the old shape
    # would satisfy CREATE TABLE IF NOT EXISTS and silently keep the wrong keys.
    _replace_dead_students_table(conn)
    for schema in _SCHEMAS:
        with open(schema, encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()
    migrate(conn, default_course)


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
