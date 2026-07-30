"""
submission.py — worksheet submission and rubric grading.

Replaces Google Classroom's collect-and-grade role, completing the move off
Google. Identity is the same one-time code used by the graded quiz: no student
password exists anywhere on this platform.

THE TWO THINGS THAT MAKE FILE UPLOAD SAFE HERE

1. **A student never influences a filesystem path.** `store_file` generates the
   on-disk name from `secrets.token_hex` and records the student's own filename
   in the database for display only. Traversal, collisions and
   extension-confusion (`report.pdf.php`, `..%2f`, NUL bytes, Windows reserved
   names) are all impossible by construction rather than filtered — there is no
   filter to bypass because the input never reaches the path.

2. **Uploads are never served inline.** `open_file` hands back bytes and a
   display name; the route sets `Content-Disposition: attachment` and a
   sandbox CSP. This matters more here than on most platforms: an uploaded HTML
   or SVG rendered inline from this origin is stored XSS straight into the
   teacher's authenticated grading session — the account that holds every
   student's marks. The deliverables are screenshots and PDFs, so nothing is
   lost by refusing to render them.

WHAT IS DELIBERATELY *NOT* DONE
   No content sniffing, no image re-encoding, no antivirus. Those are defences
   for platforms that display what they receive. This one doesn't. Adding them
   would suggest inline rendering is safe if only the checks were good enough,
   which is the argument that loses.

MARKS
   A criterion with `points = NULL` is UNMARKED, which is not zero. `score()`
   reports `complete=False` while any criterion is unmarked, so a half-graded
   worksheet cannot be exported as a finished mark.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import string
import unicodedata

# Same alphabet as the quiz codes: printed on paper, read aloud, typed under
# time pressure — `I/O/0/1` cost support time.
CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits
                        if c not in "IO01")
CODE_LEN = 8

# A worksheet PDF with a dozen embedded screenshots. Bounded, but not so tight
# that a legitimate submission bounces at 23:50 on a deadline.
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_FILES_PER_SUBMISSION = 10

# The rubric the worksheets actually carry (see any labs/weekNN/worksheet.md
# "Criterion | Points" table).
DEFAULT_RUBRIC = [
    {"criterion": "Lecture questions (conceptual accuracy)", "max": 20.0},
    {"criterion": "Exploitation + evidence (payloads + screenshots)", "max": 40.0},
    {"criterion": "Defense (fixes proven, lines cited)", "max": 25.0},
    {"criterion": "Reflection (CWE/OWASP mapping, mitigation)", "max": 15.0},
]


class SubmitError(Exception):
    """Refusal with a student-safe message."""


def safe_display_name(raw: str) -> str:
    """Sanitise a filename for DISPLAY. Never used to build a path.

    Even though the on-disk name is generated, the student's name is rendered
    back to them and to the teacher, so it still gets stripped of control
    characters, path separators and direction-override marks (which can make
    `exe.txt` display as `txt.exe`).
    """
    s = unicodedata.normalize("NFKC", str(raw or ""))
    s = "".join(c for c in s if c.isprintable() and unicodedata.category(c) != "Cf")
    s = s.replace("\\", "/").split("/")[-1]          # drop any path part
    s = re.sub(r"\s+", " ", s).strip(" .")           # no leading/trailing dots
    return s[:120] or "unnamed"


# --- assignments -----------------------------------------------------------

def create_assignment(conn, *, teacher_id, title, now, week_slug=None,
                      instructions="", due_at=None, rubric=None,
                      course_slug=None):
    rubric = rubric or DEFAULT_RUBRIC
    if not rubric:
        raise ValueError("an assignment needs a rubric")
    for r in rubric:
        if "criterion" not in r or float(r.get("max", 0)) <= 0:
            raise ValueError(f"bad rubric row: {r!r}")
    import course_scope
    course = course_scope.check(course_slug)
    cur = conn.execute(
        "INSERT INTO assignments (teacher_id, course_slug, title, week_slug,"
        " instructions, due_at, rubric_json, released, created_at)"
        " VALUES (?,?,?,?,?,?,?,0,?)",
        (teacher_id, course, title, week_slug, instructions, due_at,
         json.dumps(rubric, ensure_ascii=False), now))
    conn.commit()
    return cur.lastrowid


def get_assignment(conn, assignment_id):
    return conn.execute("SELECT * FROM assignments WHERE id = ?",
                        (assignment_id,)).fetchone()


def rubric_of(row) -> list[dict]:
    return json.loads(row["rubric_json"])


def total_points(row) -> float:
    return sum(float(r["max"]) for r in rubric_of(row))


def issue_codes(conn, assignment_id, student_ids, now):
    """Idempotent, like the quiz: adding a late enrolment must not invalidate
    slips already handed out."""
    out = {}
    for sid in student_ids:
        row = conn.execute(
            "SELECT code FROM submit_codes WHERE assignment_id = ? AND student_id = ?",
            (assignment_id, sid)).fetchone()
        if row:
            out[sid] = row["code"]
            continue
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))
            if not conn.execute("SELECT 1 FROM submit_codes WHERE code = ?",
                                (code,)).fetchone():
                break
        conn.execute("INSERT INTO submit_codes (code, assignment_id, student_id,"
                     " issued_at) VALUES (?,?,?,?)", (code, assignment_id, sid, now))
        out[sid] = code
    conn.commit()
    return out


# --- the student side ------------------------------------------------------

def redeem(conn, code, now):
    """Open (or reopen) this student's submission. Returns the submission row.

    Unlike a quiz code this does not burn: a student must be able to come back
    and replace a bad upload before the deadline. After the deadline the row is
    still returned so they can read their feedback — `can_upload` is what gates
    writing.
    """
    row = conn.execute("SELECT * FROM submit_codes WHERE code = ?",
                       ((code or "").strip().upper(),)).fetchone()
    if row is None:
        raise SubmitError("That code isn't valid.")

    sub = conn.execute(
        "SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?",
        (row["assignment_id"], row["student_id"])).fetchone()
    if sub is not None:
        return sub

    cur = conn.execute(
        "INSERT INTO submissions (assignment_id, student_id, created_at)"
        " VALUES (?,?,?)", (row["assignment_id"], row["student_id"], now))
    conn.commit()
    return conn.execute("SELECT * FROM submissions WHERE id = ?",
                        (cur.lastrowid,)).fetchone()


def can_upload(conn, submission, now) -> bool:
    a = get_assignment(conn, submission["assignment_id"])
    return not a["due_at"] or now <= a["due_at"]


def is_late(conn, submission) -> bool:
    a = get_assignment(conn, submission["assignment_id"])
    return bool(a["due_at"] and submission["submitted_at"]
                and submission["submitted_at"] > a["due_at"])


def store_file(conn, submission, *, display_name, data: bytes, now, upload_dir):
    """Persist one uploaded file. The student names nothing on disk.

    Returns the row. Refuses oversize, empty, and over-count uploads with
    messages a student can act on.
    """
    if not can_upload(conn, submission, now):
        raise SubmitError("The deadline has passed.")
    if not data:
        raise SubmitError("That file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise SubmitError(
            f"That file is {len(data) // (1024*1024)} MB — the limit is "
            f"{MAX_FILE_BYTES // (1024*1024)} MB.")
    n = conn.execute("SELECT COUNT(*) c FROM submission_files WHERE submission_id = ?",
                     (submission["id"],)).fetchone()["c"]
    if n >= MAX_FILES_PER_SUBMISSION:
        raise SubmitError(f"You can attach at most {MAX_FILES_PER_SUBMISSION} files. "
                          f"Remove one first.")

    # The on-disk name is ours alone: random, flat, no extension. Nothing a
    # student sends can reach the filesystem.
    stored = secrets.token_hex(24)
    os.makedirs(upload_dir, mode=0o700, exist_ok=True)
    path = os.path.join(upload_dir, stored)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)

    cur = conn.execute(
        "INSERT INTO submission_files (submission_id, display_name, stored_name,"
        " size_bytes, sha256, uploaded_at) VALUES (?,?,?,?,?,?)",
        (submission["id"], safe_display_name(display_name), stored, len(data),
         hashlib.sha256(data).hexdigest(), now))
    conn.execute("UPDATE submissions SET submitted_at = ? WHERE id = ?",
                 (now, submission["id"]))
    conn.commit()
    return conn.execute("SELECT * FROM submission_files WHERE id = ?",
                        (cur.lastrowid,)).fetchone()


def list_files(conn, submission_id):
    return conn.execute(
        "SELECT * FROM submission_files WHERE submission_id = ? ORDER BY id",
        (submission_id,)).fetchall()


def delete_file(conn, submission, file_id, now, upload_dir):
    """Let a student replace a wrong upload before the deadline."""
    if not can_upload(conn, submission, now):
        raise SubmitError("The deadline has passed.")
    row = conn.execute(
        "SELECT * FROM submission_files WHERE id = ? AND submission_id = ?",
        (file_id, submission["id"])).fetchone()
    if row is None:
        raise SubmitError("No such file.")
    try:
        os.remove(os.path.join(upload_dir, row["stored_name"]))
    except OSError:
        pass                      # already gone; the row still goes
    conn.execute("DELETE FROM submission_files WHERE id = ?", (file_id,))
    conn.commit()


def open_file(conn, file_id, upload_dir):
    """(display_name, bytes) for download. Callers MUST serve as an attachment.

    `stored_name` came from `secrets.token_hex`, so it is hex-only by
    construction — re-checked here anyway, because this function turns a
    database value into a filesystem path and that is exactly the place a future
    change could go wrong quietly.
    """
    row = conn.execute("SELECT * FROM submission_files WHERE id = ?",
                       (file_id,)).fetchone()
    if row is None:
        return None
    stored = row["stored_name"]
    if not re.fullmatch(r"[0-9a-f]{48}", stored):
        return None
    path = os.path.join(upload_dir, stored)
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return row["display_name"], fh.read()


def set_note(conn, submission, note, now):
    if not can_upload(conn, submission, now):
        raise SubmitError("The deadline has passed.")
    conn.execute("UPDATE submissions SET note = ? WHERE id = ?",
                 (str(note or "")[:4000], submission["id"]))
    conn.commit()


# --- grading + export ------------------------------------------------------

def grade(conn, submission_id, criterion, points, comment, now):
    conn.execute(
        "INSERT INTO rubric_scores (submission_id, criterion, points, comment,"
        " graded_at) VALUES (?,?,?,?,?)"
        " ON CONFLICT(submission_id, criterion) DO UPDATE SET"
        " points = excluded.points, comment = excluded.comment,"
        " graded_at = excluded.graded_at",
        (submission_id, criterion, None if points is None else float(points),
         str(comment or "")[:2000], now))
    conn.commit()


def score(conn, submission_id):
    """(earned, possible, complete). `complete` is False while any criterion is
    unmarked — an unmarked criterion is not a zero."""
    sub = conn.execute("SELECT * FROM submissions WHERE id = ?",
                       (submission_id,)).fetchone()
    if sub is None:
        return 0.0, 0.0, False
    a = get_assignment(conn, sub["assignment_id"])
    marks = {r["criterion"]: r["points"] for r in conn.execute(
        "SELECT criterion, points FROM rubric_scores WHERE submission_id = ?",
        (submission_id,)).fetchall()}

    earned, possible, complete = 0.0, 0.0, True
    for row in rubric_of(a):
        possible += float(row["max"])
        got = marks.get(row["criterion"])
        if got is None:
            complete = False
        else:
            earned += got
    return earned, possible, complete


def gradebook_rows(conn, assignment_id):
    """Per-student results in the shape instructor/gradebook/ consumes.

    A student who never submitted appears with `submitted=False` and no percent
    — never a 0. "Didn't hand it in" and "handed in and scored nothing" are
    different facts, and the late penalty (SUBMISSION.md: -10%/day up to 3 days)
    is the teacher's to apply, so `late` travels alongside rather than being
    silently deducted here.
    """
    codes = conn.execute(
        "SELECT student_id FROM submit_codes WHERE assignment_id = ? ORDER BY student_id",
        (assignment_id,)).fetchall()
    out = []
    for c in codes:
        sub = conn.execute(
            "SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?",
            (assignment_id, c["student_id"])).fetchone()
        if sub is None or not sub["submitted_at"]:
            out.append({"student_id": c["student_id"], "submission_id": None,
                        "submitted": False, "late": False, "files": 0,
                        "earned": None, "possible": None, "percent": None,
                        "fully_graded": False})
            continue
        earned, possible, complete = score(conn, sub["id"])
        out.append({
            "student_id": c["student_id"],
            "submission_id": sub["id"],
            "submitted": True,
            "late": is_late(conn, sub),
            "files": len(list_files(conn, sub["id"])),
            "earned": earned,
            "possible": possible,
            "percent": (earned / possible * 100) if possible else None,
            "fully_graded": complete,
        })
    return out
