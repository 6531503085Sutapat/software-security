"""codes.py — the one module that knows both attempt_codes (quiz) and
submit_codes (worksheet) exist.

The two flows mint codes from the identical alphabet at the identical length
(see CODE_ALPHABET/CODE_LEN in assessment.py and submission.py) but each only
ever checked its own table for uniqueness. Nothing stopped the same 8-character
string existing as a valid code in both tables at once — harmless while /quiz
and /submit are the only ways to redeem one, but not once a code can be
redeemed without knowing in advance which kind it is.
"""
from __future__ import annotations


def is_taken(conn, code: str) -> bool:
    """True if `code` already exists as either kind of code. issue_codes() in
    both assessment.py and submission.py retries generation against this
    instead of their own table alone, so a fresh code can never collide with
    the other flow's."""
    return bool(
        conn.execute("SELECT 1 FROM attempt_codes WHERE code = ?", (code,)).fetchone()
        or conn.execute("SELECT 1 FROM submit_codes WHERE code = ?", (code,)).fetchone()
    )


def find_kind(conn, code: str) -> str | None:
    """"quiz", "submit", or None if `code` isn't a real code of either kind.

    Normalizes the same way assessment.redeem()/submission.redeem() do, so a
    code classified here will look up the same way when those functions
    actually redeem it.

    Raises if `code` exists in both tables at once — is_taken() at generation
    is supposed to make that impossible; this is the fail-loud backstop, not
    the primary defense, so it never silently picks one.
    """
    normalized = (code or "").strip().upper()
    in_quiz = conn.execute("SELECT 1 FROM attempt_codes WHERE code = ?",
                           (normalized,)).fetchone()
    in_submit = conn.execute("SELECT 1 FROM submit_codes WHERE code = ?",
                             (normalized,)).fetchone()
    if in_quiz and in_submit:
        raise RuntimeError("a code exists in both attempt_codes and submit_codes")
    if in_quiz:
        return "quiz"
    if in_submit:
        return "submit"
    return None
