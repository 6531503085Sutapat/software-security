"""Tests for codes.py — the one module that knows both attempt_codes and
submit_codes exist. A quiz code and a submit code share an alphabet and a
length by convention, not by any constraint that stops them colliding; this
module is what makes that cross-table check happen instead of each flow only
ever checking its own table."""

import contextlib
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import assessment as A  # noqa: E402
import codes as C  # noqa: E402
import submission as S  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T0 = "2026-08-15T08:00:00"


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


def _quiz_code(conn, sid="65310001"):
    qs = [{"stem": "q?", "options": ["a", "b"], "correct": 0}]
    aid = A.publish(conn, teacher_id=1, title="Q", questions=qs, now=T0)
    return A.issue_codes(conn, aid, [sid], T0)[sid]


def _submit_code(conn, sid="65310001"):
    wid = S.create_assignment(conn, teacher_id=1, title="W", now=T0)
    return S.issue_codes(conn, wid, [sid], T0)[sid]


@contextlib.contextmanager
def _fixed_choices(chars):
    """Make secrets.choice() deterministically yield `chars` in order, one per
    call. assessment.py and submission.py both do `import secrets` (the same
    stdlib singleton), so patching it here affects issue_codes() in either
    module regardless of which one the test is exercising.

    monkeypatch.setattr() does not reliably patch secrets.choice in this
    environment (verified: the patched attribute reads back correctly but the
    real generator still runs) — plain assignment does, so this restores the
    original by hand rather than relying on monkeypatch's teardown. Restoring
    matters: every OTHER test in the process shares this same secrets module,
    and a leaked deterministic choice() would make their "random" codes
    predictable too.
    """
    import secrets
    it = iter(chars)
    original = secrets.choice
    secrets.choice = lambda alphabet: next(it)
    try:
        yield
    finally:
        secrets.choice = original


# --- is_taken ----------------------------------------------------------------

def test_is_taken_false_for_an_unused_code(conn):
    assert C.is_taken(conn, "AAAAAAAA") is False


def test_is_taken_true_for_a_real_quiz_code(conn):
    assert C.is_taken(conn, _quiz_code(conn)) is True


def test_is_taken_true_for_a_real_submit_code(conn):
    assert C.is_taken(conn, _submit_code(conn)) is True


# --- find_kind -----------------------------------------------------------

def test_find_kind_identifies_a_quiz_code(conn):
    assert C.find_kind(conn, _quiz_code(conn)) == "quiz"


def test_find_kind_identifies_a_submit_code(conn):
    assert C.find_kind(conn, _submit_code(conn)) == "submit"


def test_find_kind_is_none_for_an_unknown_code(conn):
    assert C.find_kind(conn, "AAAAAAAA") is None


def test_find_kind_normalizes_like_redeem_does(conn):
    # both A.redeem() and S.redeem() do (code or "").strip().upper() before
    # lookup — find_kind must classify the same string the same way, or a
    # lowercase-typed code would be findable here but then fail to redeem.
    code = _quiz_code(conn)
    assert C.find_kind(conn, f"  {code.lower()}  ") == "quiz"


def test_find_kind_raises_if_a_code_exists_in_both_tables(conn):
    # Should be unreachable once issue_codes() uses is_taken() for generation —
    # this is the fail-loud backstop, not the primary defense, so it has to be
    # provoked by hand rather than through the real issuance path.
    qs = [{"stem": "q?", "options": ["a", "b"], "correct": 0}]
    aid = A.publish(conn, teacher_id=1, title="Q", questions=qs, now=T0)
    wid = S.create_assignment(conn, teacher_id=1, title="W", now=T0)
    conn.execute("INSERT INTO attempt_codes (code, assessment_id, student_id, issued_at)"
                 " VALUES ('COLLIDE1', ?, 'x', ?)", (aid, T0))
    conn.execute("INSERT INTO submit_codes (code, assignment_id, student_id, issued_at)"
                 " VALUES ('COLLIDE1', ?, 'x', ?)", (wid, T0))
    conn.commit()
    with pytest.raises(RuntimeError):
        C.find_kind(conn, "COLLIDE1")


def test_find_kind_collision_error_does_not_leak_the_code(conn):
    # The RuntimeError above gets logged server-side (see routes_assess.py,
    # routes_submit.py, routes_code.py) — its message must not hand a live
    # credential to whatever reads those logs.
    qs = [{"stem": "q?", "options": ["a", "b"], "correct": 0}]
    aid = A.publish(conn, teacher_id=1, title="Q", questions=qs, now=T0)
    wid = S.create_assignment(conn, teacher_id=1, title="W", now=T0)
    conn.execute("INSERT INTO attempt_codes (code, assessment_id, student_id, issued_at)"
                 " VALUES ('COLLIDE2', ?, 'x', ?)", (aid, T0))
    conn.execute("INSERT INTO submit_codes (code, assignment_id, student_id, issued_at)"
                 " VALUES ('COLLIDE2', ?, 'x', ?)", (wid, T0))
    conn.commit()
    with pytest.raises(RuntimeError) as exc_info:
        C.find_kind(conn, "COLLIDE2")
    assert "COLLIDE2" not in str(exc_info.value)


# --- cross-table collision guard at generation --------------------------------

def test_issuing_a_quiz_code_never_collides_with_an_existing_submit_code(conn):
    existing = _submit_code(conn, sid="11110001")
    # Force the first 8-character candidate to be exactly `existing` (guaranteed
    # collision against submit_codes), then a distinct one on retry. Proves
    # assessment.issue_codes() checks BOTH tables, not just attempt_codes.
    qs = [{"stem": "q?", "options": ["a", "b"], "correct": 0}]
    aid = A.publish(conn, teacher_id=1, title="Q", questions=qs, now=T0)
    with _fixed_choices(list(existing) + list("BBBBBBBB")):
        code = A.issue_codes(conn, aid, ["99990001"], T0)["99990001"]
    assert code == "BBBBBBBB"
    assert code != existing


def test_issuing_a_submit_code_never_collides_with_an_existing_quiz_code(conn):
    existing = _quiz_code(conn, sid="11110001")
    wid = S.create_assignment(conn, teacher_id=1, title="W", now=T0)
    with _fixed_choices(list(existing) + list("BBBBBBBB")):
        code = S.issue_codes(conn, wid, ["99990001"], T0)["99990001"]
    assert code == "BBBBBBBB"
    assert code != existing
