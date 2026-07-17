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
