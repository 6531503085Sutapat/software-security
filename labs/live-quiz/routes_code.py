"""routes_code.py — one entry point for either a quiz code or a submission
code. /quiz and /submit still exist and still work on their own; this page
just removes the need to know in advance which kind of code you're holding.
Routes by table membership (codes.find_kind), then lets the matching domain
module's own redeem() apply its own rules — the two codes keep their separate
semantics (burn vs. no-burn, timed window vs. none) underneath.
"""
from __future__ import annotations

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

bp = Blueprint("code", __name__)


def _db():
    return current_app.config["GET_DB"]()


def _now():
    return current_app.config["NOW"]()


def _csrf():
    return current_app.config["ISSUE_CSRF"]()


def _check_csrf():
    current_app.config["CHECK_CSRF"]()


@bp.route("/code", methods=["GET", "POST"])
def entry():
    if request.method == "GET":
        return render_template("code_entry.html", csrf_token=_csrf(), error=None)
    _check_csrf()
    raw = request.form.get("code")

    import codes
    try:
        kind = codes.find_kind(_db(), raw)
    except RuntimeError:
        # A code in both tables is a data-integrity bug, not something this
        # student did. Log it for us; the student still gets a plain refusal
        # rather than a 500.
        current_app.logger.exception("codes.find_kind: code in both tables")
        kind = None

    if kind == "quiz":
        import assessment as A
        try:
            att = A.redeem(_db(), raw, _now())
        except A.AttemptError as exc:
            return render_template("code_entry.html", csrf_token=_csrf(), error=str(exc)), 200
        session["attempt_id"] = att["id"]
        return redirect(url_for("assess.quiz_take"))

    if kind == "submit":
        import submission as S
        sub = S.redeem(_db(), raw, _now())   # cannot itself fail once find_kind
                                              # confirms the code is there — see
                                              # codes.py.
        session["submission_id"] = sub["id"]
        return redirect(url_for("submit.workspace"))

    return render_template("code_entry.html", csrf_token=_csrf(),
                           error="That code isn't valid."), 200
