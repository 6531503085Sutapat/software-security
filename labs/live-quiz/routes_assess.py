"""
routes_assess.py — HTTP surface for the graded weekly quiz.

Registered as a blueprint by app.py. Kept out of app.py because the live game and
the graded quiz are different modes that happen to share a process: the game is
synchronous/anonymous/in-memory, this is asynchronous/identified/persisted and
its numbers become someone's grade. Mixing their routes into one 500-line module
is how the identity models get mixed up too.

Two audiences, two guards:
  * teacher routes  -> @login_required, and every query is scoped by teacher_id
                       (a teacher must never reach another teacher's assessment)
  * student routes  -> no account at all; the one-time code IS the credential,
                       exchanged once for a server-side session
"""

from __future__ import annotations

import csv
import io

from flask import (Blueprint, abort, current_app, redirect, render_template,
                   request, session, url_for, Response)

import assessment as A
import auth
import quiz_loader

def _courses():
    import content as C
    return C.list_courses()


bp = Blueprint("assess", __name__)


def _db():
    return current_app.config["GET_DB"]()


def _now():
    return current_app.config["NOW"]()


def _csrf():
    return current_app.config["ISSUE_CSRF"]()


def _check_csrf():
    current_app.config["CHECK_CSRF"]()


def _owned(assessment_id):
    """Fetch an assessment or 404 — never 403. A teacher probing IDs shouldn't
    learn which ones exist."""
    a = A.get_assessment(_db(), assessment_id)
    if a is None or a["teacher_id"] != auth.current_teacher_id():
        abort(404)
    return a


# --- teacher ---------------------------------------------------------------

@bp.route("/assess")
@auth.login_required
def index():
    rows = _db().execute(
        "SELECT a.*,"
        " (SELECT COUNT(*) FROM attempt_codes c WHERE c.assessment_id = a.id) AS issued,"
        " (SELECT COUNT(*) FROM attempts t WHERE t.assessment_id = a.id"
        "    AND t.submitted_at IS NOT NULL) AS submitted"
        " FROM assessments a WHERE a.teacher_id = ? ORDER BY a.course_slug, a.id DESC",
        (auth.current_teacher_id(),)).fetchall()
    return render_template("assess_index.html", assessments=rows, csrf_token=_csrf())


@bp.route("/assess/new", methods=["GET", "POST"])
@auth.login_required
def new():
    if request.method == "GET":
        sets = _db().execute(
            "SELECT id, title FROM question_sets WHERE teacher_id = ? ORDER BY updated_at DESC",
            (auth.current_teacher_id(),)).fetchall()
        return render_template("assess_new.html", sets=sets, csrf_token=_csrf(),
                               courses=_courses(), error=None)

    _check_csrf()
    f = request.form
    src = _db().execute("SELECT * FROM question_sets WHERE id = ? AND teacher_id = ?",
                        (f.get("set_id"), auth.current_teacher_id())).fetchone()
    if src is None:
        abort(404)

    topics = quiz_loader.parse_topics_from_text(src["source_md"])
    questions = [q for qs in topics.values() for q in qs]
    if not questions:
        return render_template("assess_new.html", sets=[], csrf_token=_csrf(),
                               courses=_courses(),
                               error="That question set has no parsable questions."), 200

    # The course's weekly quiz is 5 MCQ + one personal short answer worth 3
    # (quizzes/weekly/README.md §Grading). The short answer is what makes the
    # quiz AI-resistant, so it is opt-out rather than opt-in.
    limit = f.get("mcq_count", type=int)
    if limit:
        questions = questions[:limit]
    if f.get("short_stem", "").strip():
        questions.append({"kind": A.KIND_SHORT,
                          "stem": f["short_stem"].strip(),
                          "points": f.get("short_points", type=float) or 3.0})

    aid = A.publish(
        _db(), teacher_id=auth.current_teacher_id(),
        title=f.get("title", "").strip() or src["title"],
        questions=questions, now=_now(),
        variant=(f.get("variant") or "A").strip()[:8],
        shuffle_questions=bool(f.get("shuffle_questions")),
        shuffle_options=bool(f.get("shuffle_options")),
        time_limit_sec=f.get("time_limit_min", type=int) and
        f.get("time_limit_min", type=int) * 60,
        opens_at=(f.get("opens_at") or "").strip() or None,
        closes_at=(f.get("closes_at") or "").strip() or None,
        # None when the form omitted the field (single course) — course_scope
        # resolves that to the default rather than guessing here.
        course_slug=(f.get("course_slug") or "").strip() or None,
    )
    return redirect(url_for("assess.detail", assessment_id=aid))


@bp.route("/assess/<int:assessment_id>")
@auth.login_required
def detail(assessment_id):
    a = _owned(assessment_id)
    return render_template(
        "assess_detail.html", a=a,
        questions=A.snapshot(_db(), assessment_id),
        rows=A.gradebook_rows(_db(), assessment_id),
        shorts=A.short_answers(_db(), assessment_id),
        csrf_token=_csrf())


@bp.route("/assess/<int:assessment_id>/codes", methods=["POST"])
@auth.login_required
def codes(assessment_id):
    """Issue one code per student ID. Idempotent — safe to re-run for a late
    enrolment without invalidating sheets already printed."""
    _owned(assessment_id)
    _check_csrf()
    ids = [s.strip() for s in (request.form.get("student_ids") or "").replace(",", "\n").split("\n")]
    ids = [s for s in ids if s and not s.startswith("#")]
    if not ids:
        return redirect(url_for("assess.detail", assessment_id=assessment_id))
    A.issue_codes(_db(), assessment_id, ids, _now())
    return redirect(url_for("assess.detail", assessment_id=assessment_id))


@bp.route("/assess/<int:assessment_id>/codes.csv")
@auth.login_required
def codes_csv(assessment_id):
    """The print-and-cut sheet. One row per student — hand them their own row.

    A working credential: distribute per-student, never as a shared list."""
    _owned(assessment_id)
    rows = _db().execute(
        "SELECT student_id, code, redeemed_at FROM attempt_codes"
        " WHERE assessment_id = ? ORDER BY student_id", (assessment_id,)).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["student_id", "code", "redeemed_at"])
    for r in rows:
        w.writerow([r["student_id"], r["code"], r["redeemed_at"] or ""])
    return Response(buf.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": f'attachment; filename="codes-{assessment_id}.csv"'})


@bp.route("/assess/<int:assessment_id>/grade", methods=["POST"])
@auth.login_required
def grade(assessment_id):
    _owned(assessment_id)
    _check_csrf()
    A.grade_short(_db(), request.form.get("attempt_id", type=int),
                  request.form.get("question_id", type=int),
                  request.form.get("points", type=float) or 0.0, _now())
    return redirect(url_for("assess.detail", assessment_id=assessment_id) + "#grading")


@bp.route("/assess/<int:assessment_id>/results.csv")
@auth.login_required
def results_csv(assessment_id):
    """Feeds instructor/gradebook/ — percent is 0-100, per GRADEBOOK.md.

    `fully_graded` travels with the row on purpose: a partially-graded quiz has a
    real earned total that is NOT a final mark, and an importer that ignores this
    column will quietly enter a partial score as a whole one.
    """
    _owned(assessment_id)
    rows = A.gradebook_rows(_db(), assessment_id)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["student_id", "attempted", "submitted", "earned", "possible",
                "percent", "fully_graded"])
    for r in rows:
        w.writerow([r["student_id"], int(r["attempted"]), int(r["submitted"]),
                    "" if r["earned"] is None else f"{r['earned']:.2f}",
                    "" if r["possible"] is None else f"{r['possible']:.2f}",
                    "" if r["percent"] is None else f"{r['percent']:.2f}",
                    int(r["fully_graded"])])
    return Response(buf.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": f'attachment; filename="results-{assessment_id}.csv"'})


@bp.route("/assess/<int:assessment_id>/q6.csv")
@auth.login_required
def q6_csv(assessment_id):
    """Short answers in the shape instructor/quizzes/weekly/verify_q6.py consumes,
    so Q6 keeps being checked against each student's own CTFd capture rather than
    becoming a second, unverified path."""
    _owned(assessment_id)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["student_id", "answer", "points"])
    for r in A.short_answers(_db(), assessment_id):
        w.writerow([r["student_id"], r["text"] or "",
                    "" if r["manual_points"] is None else f"{r['manual_points']:.2f}"])
    return Response(buf.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": f'attachment; filename="q6-{assessment_id}.csv"'})


@bp.route("/assess/<int:assessment_id>/release", methods=["POST"])
@auth.login_required
def release(assessment_id):
    _owned(assessment_id)
    _check_csrf()
    _db().execute("UPDATE assessments SET released = NOT released WHERE id = ?",
                  (assessment_id,))
    _db().commit()
    return redirect(url_for("assess.detail", assessment_id=assessment_id))


# --- student ---------------------------------------------------------------
#
# No account. The one-time code is the credential; redeeming it puts the attempt
# id in the session, and every subsequent request is authorised against that —
# never against an id in the URL.

def _current_attempt():
    aid = session.get("attempt_id")
    if aid is None:
        return None
    return A.get_attempt(_db(), aid)


@bp.route("/quiz", methods=["GET", "POST"])
def quiz_entry():
    if request.method == "GET":
        return render_template("quiz_entry.html", csrf_token=_csrf(), error=None)
    _check_csrf()
    raw = request.form.get("code")
    # Classify BEFORE attempting either table's redeem() — not after, and not
    # only on failure. A code that collides across attempt_codes and
    # submit_codes (a pre-existing data-integrity bug the generation-time
    # guard in issue_codes() only prevents going forward, not retroactively)
    # would otherwise authenticate silently as whichever side's redeem() this
    # route happens to call — a real student could land in another student's
    # attempt this way. Mirrors routes_code.py's /code, which never had this
    # bug because it already classified first.
    import codes
    try:
        kind = codes.find_kind(_db(), raw)
    except RuntimeError:
        # A code in both tables is a data-integrity bug, not something this
        # student did. Log it for us; refuse rather than trust either side.
        current_app.logger.exception("codes.find_kind: code in both tables")
        kind = None
    if kind == "submit":
        # A submit code typed into this box by mistake — the two look
        # identical (same alphabet, same length) and a student's slip carries
        # both. submission.redeem() cannot itself fail once find_kind() has
        # confirmed the code is there — see codes.py.
        import submission as S
        sub = S.redeem(_db(), raw, _now())
        session["submission_id"] = sub["id"]
        return redirect(url_for("submit.workspace"))
    if kind != "quiz":
        return render_template("quiz_entry.html", csrf_token=_csrf(),
                               error="That code isn't valid."), 200
    try:
        att = A.redeem(_db(), raw, _now())
    except A.AttemptError as exc:
        return render_template("quiz_entry.html", csrf_token=_csrf(), error=str(exc)), 200
    session["attempt_id"] = att["id"]
    return redirect(url_for("assess.quiz_take"))


@bp.route("/quiz/take", methods=["GET", "POST"])
def quiz_take():
    att = _current_attempt()
    if att is None:
        return redirect(url_for("assess.quiz_entry"))

    if request.method == "POST":
        _check_csrf()
        try:
            att = A.answer(
                _db(), att, request.form.get("question_id", type=int),
                choice=request.form.get("choice", type=int),
                text=(request.form.get("text") or "").strip() or None, now=_now())
        except A.StaleAnswer:
            # The POST is for a question that is no longer open — a double-click,
            # a back-button re-submit, a second tab, a request the phone retried.
            # Drop the write and show whatever question IS open. This branch used
            # to fall into the handler below, which SUBMITTED the attempt: one
            # double-click ended a graded quiz with every remaining question
            # unanswered, under the message "Time is up." Reproduced against a
            # real attempt before this fix, which is the only way it shows up —
            # nothing errors, the student simply loses the rest of their quiz.
            return redirect(url_for("assess.quiz_take"))
        except A.AttemptError:
            # Time-up is the expected way a timed quiz ends — close it out and
            # show the student their state rather than an error page.
            #
            # The exception's own text used to become the page's <h1>. That
            # string is written for a developer reading a log, and this is the
            # last thing a student sees at the end of a graded attempt; whatever
            # went wrong, the true and useful thing to tell them is the same.
            A.submit(_db(), att, _now())
            return render_template("quiz_done.html",
                                   message="Time is up — your quiz was submitted.",
                                   released=False, score=None)
        return redirect(url_for("assess.quiz_take"))

    now = _now()
    q = A.question_for_student(_db(), att, now=now)
    if q is None:
        att = A.submit(_db(), att, now)
        a = A.get_assessment(_db(), att["assessment_id"])
        earned, possible, complete = A.score(_db(), att["id"])
        return render_template(
            "quiz_done.html", message="Submitted. Thank you.",
            released=bool(a["released"]),
            score=(earned, possible, complete) if a["released"] else None)

    return render_template("quiz_take.html", q=q, csrf_token=_csrf(),
                           time_left=A.time_left(_db(), att, now))
