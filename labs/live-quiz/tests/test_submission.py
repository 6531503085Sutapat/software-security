"""Tests for submission.py.

Weighted toward file upload, because that is the one place in this repo where a
security finding is a real finding rather than a lesson (CLAUDE.md: security-ci
gates labs/live-quiz), and toward the marks that must not silently become zero.
"""

import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import submission as S  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T0 = "2026-08-15T08:00:00"
DUE = "2026-08-20T23:59:00"
LATE = "2026-08-21T00:30:00"


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for f in ("schema.sql", "schema_assess.sql", "schema_submit.sql"):
        with open(os.path.join(HERE, f), encoding="utf-8") as fh:
            c.executescript(fh.read())
    c.execute("INSERT INTO teachers (id, username, password_hash, created_at)"
              " VALUES (1,'t','x',?)", (T0,))
    c.commit()
    yield c
    c.close()


@pytest.fixture
def uploads(tmp_path):
    return str(tmp_path / "uploads")


def make(conn, **kw):
    kw.setdefault("title", "Week 4 worksheet")
    kw.setdefault("due_at", DUE)
    return S.create_assignment(conn, teacher_id=1, now=T0, **kw)


def open_sub(conn, aid, sid="65310001"):
    codes = S.issue_codes(conn, aid, [sid], T0)
    return S.redeem(conn, codes[sid], T0), codes[sid]


# --- a student never names a file on disk ---------------------------------

EVIL_NAMES = [
    "../../etc/passwd", "..\\..\\windows\\system32\\cmd.exe",
    "/etc/shadow", "report.pdf\x00.php", "....//....//secret",
    "con.txt", "aux", ".htaccess", "shell.php", "x.pdf.php",
    "a" * 500 + ".pdf", "‮gnp.exe", "", "   ", "..", ".",
]


@pytest.mark.parametrize("name", EVIL_NAMES)
def test_no_student_filename_ever_reaches_the_filesystem(conn, uploads, name):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    row = S.store_file(conn, sub, display_name=name, data=b"x", now=T0,
                       upload_dir=uploads)
    # on-disk name is ours: 48 hex chars, nothing else
    assert len(row["stored_name"]) == 48
    assert all(c in "0123456789abcdef" for c in row["stored_name"])
    # and the directory contains exactly that, at the top level
    entries = os.listdir(uploads)
    assert entries == [row["stored_name"]]
    assert os.path.isfile(os.path.join(uploads, row["stored_name"]))


@pytest.mark.parametrize("name,expect_absent", [
    ("../../etc/passwd", "/"),
    ("..\\..\\win\\cmd.exe", "\\"),
    ("report.pdf\x00.php", "\x00"),
    ("‮gnp.exe", "‮"),
])
def test_display_name_is_sanitised_for_rendering(name, expect_absent):
    out = S.safe_display_name(name)
    assert expect_absent not in out
    assert out and len(out) <= 120


def test_display_name_keeps_something_readable():
    assert S.safe_display_name("Wk04_65310001.pdf") == "Wk04_65310001.pdf"
    assert S.safe_display_name("รายงาน สัปดาห์4.pdf") == "รายงาน สัปดาห์4.pdf"
    assert S.safe_display_name("") == "unnamed"


def test_two_students_uploading_the_same_filename_do_not_collide(conn, uploads):
    aid = make(conn)
    a, _ = open_sub(conn, aid, "65310001")
    b, _ = open_sub(conn, aid, "65310002")
    f1 = S.store_file(conn, a, display_name="Wk04.pdf", data=b"AAA", now=T0,
                      upload_dir=uploads)
    f2 = S.store_file(conn, b, display_name="Wk04.pdf", data=b"BBB", now=T0,
                      upload_dir=uploads)
    assert f1["stored_name"] != f2["stored_name"]
    assert len(os.listdir(uploads)) == 2
    assert S.open_file(conn, f1["id"], uploads)[1] == b"AAA"
    assert S.open_file(conn, f2["id"], uploads)[1] == b"BBB"


def test_files_are_0600_in_a_0700_directory(conn, uploads):
    import stat
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    row = S.store_file(conn, sub, display_name="a.pdf", data=b"x", now=T0,
                       upload_dir=uploads)
    p = os.path.join(uploads, row["stored_name"])
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(uploads).st_mode) == 0o700


def test_open_file_refuses_a_tampered_stored_name(conn, uploads):
    """The only place a DB value becomes a path. If someone later writes a
    non-generated name into that column, this must fail closed."""
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    row = S.store_file(conn, sub, display_name="a.pdf", data=b"x", now=T0,
                       upload_dir=uploads)
    conn.execute("UPDATE submission_files SET stored_name = ? WHERE id = ?",
                 ("../../../etc/passwd", row["id"]))
    conn.commit()
    assert S.open_file(conn, row["id"], uploads) is None


def test_missing_file_on_disk_is_none_not_a_crash(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    row = S.store_file(conn, sub, display_name="a.pdf", data=b"x", now=T0,
                       upload_dir=uploads)
    os.remove(os.path.join(uploads, row["stored_name"]))
    assert S.open_file(conn, row["id"], uploads) is None


# --- upload limits ---------------------------------------------------------

def test_oversize_upload_is_refused_with_a_usable_message(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    with pytest.raises(S.SubmitError, match="limit is 20 MB"):
        S.store_file(conn, sub, display_name="big.pdf",
                     data=b"x" * (S.MAX_FILE_BYTES + 1), now=T0, upload_dir=uploads)
    assert not os.path.isdir(uploads) or os.listdir(uploads) == []


def test_empty_upload_is_refused(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    with pytest.raises(S.SubmitError, match="empty"):
        S.store_file(conn, sub, display_name="a.pdf", data=b"", now=T0,
                     upload_dir=uploads)


def test_file_count_is_capped(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    for i in range(S.MAX_FILES_PER_SUBMISSION):
        S.store_file(conn, sub, display_name=f"{i}.png", data=b"x", now=T0,
                     upload_dir=uploads)
    with pytest.raises(S.SubmitError, match="at most"):
        S.store_file(conn, sub, display_name="extra.png", data=b"x", now=T0,
                     upload_dir=uploads)


def test_a_student_can_replace_a_wrong_upload(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    row = S.store_file(conn, sub, display_name="wrong.pdf", data=b"x", now=T0,
                       upload_dir=uploads)
    S.delete_file(conn, sub, row["id"], T0, uploads)
    assert S.list_files(conn, sub["id"]) == []
    assert os.listdir(uploads) == [], "the bytes must go too, not just the row"


def test_a_student_cannot_delete_another_students_file(conn, uploads):
    aid = make(conn)
    a, _ = open_sub(conn, aid, "65310001")
    b, _ = open_sub(conn, aid, "65310002")
    theirs = S.store_file(conn, b, display_name="b.pdf", data=b"x", now=T0,
                          upload_dir=uploads)
    with pytest.raises(S.SubmitError, match="No such file"):
        S.delete_file(conn, a, theirs["id"], T0, uploads)
    assert len(S.list_files(conn, b["id"])) == 1


# --- deadline --------------------------------------------------------------

def test_uploads_close_at_the_deadline(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    assert S.can_upload(conn, sub, DUE)
    assert not S.can_upload(conn, sub, LATE)
    with pytest.raises(S.SubmitError, match="deadline"):
        S.store_file(conn, sub, display_name="a.pdf", data=b"x", now=LATE,
                     upload_dir=uploads)


def test_no_deadline_means_always_open(conn, uploads):
    aid = make(conn, due_at=None)
    sub, _ = open_sub(conn, aid)
    assert S.can_upload(conn, sub, "2099-01-01T00:00:00")


def test_lateness_is_computed_not_stored(conn, uploads):
    """A stored late flag goes stale the moment a deadline is extended."""
    aid = make(conn, due_at="2026-08-15T07:00:00")     # already past
    sub, _ = open_sub(conn, aid)
    conn.execute("UPDATE submissions SET submitted_at = ? WHERE id = ?",
                 ("2026-08-15T09:00:00", sub["id"]))
    conn.commit()
    sub = conn.execute("SELECT * FROM submissions WHERE id=?", (sub["id"],)).fetchone()
    assert S.is_late(conn, sub)
    conn.execute("UPDATE assignments SET due_at = ? WHERE id = ?",
                 ("2026-08-30T23:59:00", aid))         # deadline extended
    conn.commit()
    assert not S.is_late(conn, sub), "extending the deadline must un-late everyone"


def test_a_student_can_still_read_feedback_after_the_deadline(conn, uploads):
    aid = make(conn)
    codes = S.issue_codes(conn, aid, ["65310001"], T0)
    sub = S.redeem(conn, codes["65310001"], LATE)      # redeeming still works
    assert sub is not None
    assert not S.can_upload(conn, sub, LATE)           # but writing does not


# --- codes -----------------------------------------------------------------

def test_a_code_reopens_the_same_submission(conn, uploads):
    aid = make(conn)
    sub, code = open_sub(conn, aid)
    assert S.redeem(conn, code, T0)["id"] == sub["id"]


def test_codes_are_idempotent_and_avoid_misread_glyphs(conn):
    aid = make(conn)
    first = S.issue_codes(conn, aid, ["65310001"], T0)
    second = S.issue_codes(conn, aid, ["65310001", "65319999"], T0)
    assert second["65310001"] == first["65310001"]
    all_codes = S.issue_codes(conn, aid, [f"6531{i:04d}" for i in range(60)], T0)
    assert not (set("".join(all_codes.values())) & set("IO01"))


def test_a_bogus_code_is_refused(conn):
    make(conn)
    with pytest.raises(S.SubmitError, match="isn't valid"):
        S.redeem(conn, "NOPENOPE", T0)


# --- rubric + marks --------------------------------------------------------

def test_default_rubric_matches_the_worksheets(conn):
    a = S.get_assignment(conn, make(conn))
    assert S.total_points(a) == pytest.approx(100.0)
    assert [r["max"] for r in S.rubric_of(a)] == [20.0, 40.0, 25.0, 15.0]


def test_a_partially_marked_worksheet_is_not_complete(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    S.store_file(conn, sub, display_name="a.pdf", data=b"x", now=T0, upload_dir=uploads)
    rubric = S.rubric_of(S.get_assignment(conn, aid))
    S.grade(conn, sub["id"], rubric[0]["criterion"], 18, "good", T0)
    earned, possible, complete = S.score(conn, sub["id"])
    assert earned == pytest.approx(18.0) and possible == pytest.approx(100.0)
    assert complete is False, "an unmarked criterion is not a zero"


def test_a_fully_marked_worksheet_totals_correctly(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    for r, pts in zip(S.rubric_of(S.get_assignment(conn, aid)), (18, 35, 20, 12)):
        S.grade(conn, sub["id"], r["criterion"], pts, "", T0)
    assert S.score(conn, sub["id"]) == (pytest.approx(85.0), pytest.approx(100.0), True)


def test_a_zero_is_a_mark_and_none_is_not(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    for r in S.rubric_of(S.get_assignment(conn, aid)):
        S.grade(conn, sub["id"], r["criterion"], 0, "", T0)
    assert S.score(conn, sub["id"])[2] is True
    S.grade(conn, sub["id"], S.rubric_of(S.get_assignment(conn, aid))[0]["criterion"],
            None, "needs re-check", T0)
    assert S.score(conn, sub["id"])[2] is False


def test_regrading_overwrites_rather_than_duplicating(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    crit = S.rubric_of(S.get_assignment(conn, aid))[0]["criterion"]
    S.grade(conn, sub["id"], crit, 10, "first", T0)
    S.grade(conn, sub["id"], crit, 20, "revised", T0)
    rows = conn.execute("SELECT points, comment FROM rubric_scores"
                        " WHERE submission_id=?", (sub["id"],)).fetchall()
    assert len(rows) == 1 and rows[0]["points"] == 20 and rows[0]["comment"] == "revised"


# --- export ----------------------------------------------------------------

def test_a_student_who_never_submitted_is_not_a_zero(conn, uploads):
    aid = make(conn)
    S.issue_codes(conn, aid, ["65310001", "65310002"], T0)
    sub = S.redeem(conn, S.issue_codes(conn, aid, ["65310001"], T0)["65310001"], T0)
    S.store_file(conn, sub, display_name="a.pdf", data=b"x", now=T0, upload_dir=uploads)

    rows = {r["student_id"]: r for r in S.gradebook_rows(conn, aid)}
    assert rows["65310002"]["submitted"] is False
    assert rows["65310002"]["percent"] is None
    assert rows["65310001"]["submitted"] is True and rows["65310001"]["files"] == 1


def test_late_travels_with_the_row_rather_than_being_deducted(conn, uploads):
    """SUBMISSION.md's -10%/day is the teacher's call, applied once, not silently
    baked into the exported percentage."""
    aid = make(conn, due_at="2026-08-15T07:00:00")
    sub, _ = open_sub(conn, aid)
    conn.execute("UPDATE submissions SET submitted_at=? WHERE id=?",
                 ("2026-08-15T09:00:00", sub["id"]))
    conn.commit()
    for r in S.rubric_of(S.get_assignment(conn, aid)):
        S.grade(conn, sub["id"], r["criterion"], r["max"], "", T0)
    (row,) = S.gradebook_rows(conn, aid)
    assert row["late"] is True
    assert row["percent"] == pytest.approx(100.0), "no silent deduction"


def test_partial_grading_is_flagged_in_the_export(conn, uploads):
    aid = make(conn)
    sub, _ = open_sub(conn, aid)
    S.store_file(conn, sub, display_name="a.pdf", data=b"x", now=T0, upload_dir=uploads)
    (row,) = S.gradebook_rows(conn, aid)
    assert row["fully_graded"] is False
