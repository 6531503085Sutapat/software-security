"""
routes_content.py — the public course content plane (`/learn`).

Replaces Classroom's *distribute the material* role. Read-only, no auth, no
student data, no upload: the safest surface on the platform, and deliberately so
— it is the only part students hit before they have any credential.

Content is rendered by `content.py`, which escapes every byte before recognising
any markdown. That ordering matters here more than anywhere else on the platform:
`labs/week05-xss-client-side/worksheet.md` ships `<script>alert(document.cookie)
</script>` as course content, and these routes share an origin with the teacher's
authenticated grading session.

Belt and braces on top of the renderer: a per-response CSP that forbids inline
and remote script outright, so even a renderer regression cannot execute
anything. `X-Content-Type-Options: nosniff` stops a browser deciding a response
is script on its own.
"""

from __future__ import annotations

from flask import (Blueprint, abort, make_response, redirect, render_template,
                   url_for)

import content as C

bp = Blueprint("learn", __name__)

# No script at all on the worksheet pages. This is where markdown containing
# live XSS payloads gets rendered, so `script-src` is never widened here —
# `frame-src 'self'` is the only addition, and it exists so a worksheet can
# embed a simulation that runs in its OWN document under its own policy.
CSP = ("default-src 'none'; style-src 'self'; img-src 'self' data:; "
       "font-src 'self'; frame-src 'self'; base-uri 'none'; "
       "form-action 'none'; frame-ancestors 'none'")

# Simulations are OUR code, shipped in static/, and are the only pages on this
# blueprint allowed to execute anything. `'self'` only: no inline (so a template
# cannot grow a <script> block), no eval, no remote origin. They are additionally
# framed with `sandbox="allow-scripts"` and WITHOUT `allow-same-origin` — see
# content.py's fence handler for why that omission is load-bearing.
SIM_CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; "
           "img-src 'self' data:; font-src 'self'; base-uri 'none'; "
           "form-action 'none'")


def _harden(resp, csp=None):
    resp.headers["Content-Security-Policy"] = csp or CSP
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@bp.after_request
def _headers(resp):
    # A simulation response sets its own policy in the view; don't overwrite it.
    if resp.headers.get("Content-Security-Policy"):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        return resp
    return _harden(resp)


@bp.route("/sim/<slug>")
def simulation(slug):
    """One interactive simulation, in its own document under its own CSP.

    Kept off the worksheet page deliberately: `/learn` renders course markdown
    that contains real XSS payloads, so it must stay script-free. A simulation
    is code we wrote, so it gets exactly the privilege it needs and no more.
    """
    if slug not in C.SIMS:
        abort(404)
    resp = make_response(render_template(f"sim_{slug.replace('-', '_')}.html",
                                         slug=slug, title=C.SIMS[slug]))
    return _harden(resp, SIM_CSP)


@bp.route("/sim")
def simulations():
    return render_template("sim_index.html", sims=sorted(C.SIMS.items()))


@bp.route("/learn")
def index():
    """The front door.

    With one course this shows that course's weeks directly — a list of one
    course would be a pointless extra click for the only cohort that exists
    today. With several, it becomes the course list, which is the thing that
    answers "which course am I in" before "which week".
    """
    courses = C.list_courses()
    if len(courses) == 1:
        c = courses[0]
        return render_template("learn_index.html", course=c,
                               weeks=C.list_weeks(c["slug"]),
                               modules=C.list_modules(c["slug"]),
                               nav_courses=C.nav_courses(), only_course=True)
    return render_template("learn_courses.html", courses=courses,
                           nav_courses=C.nav_courses())


# ── URL shapes under /learn ────────────────────────────────────────────────
# Canonical:  /learn/<course>/<week>[/<kind>]
# Legacy:     /learn/<week>[/<kind>]          — pre-dates courses
#
# `/learn/<a>/<b>` is the SAME SHAPE in both: it is either course+week or
# week+kind. Registering two Flask rules of the same shape and hoping the right
# one matches is how this first broke — Werkzeug matched the course rule for a
# legacy URL and it 404'd. So the segment count picks the handler and the
# handler decides, explicitly, by asking whether the first segment names a
# course. COURSES rejects any slug matching WEEK_RE, so "course" and "week" are
# disjoint sets and the decision is never ambiguous.

def _render_doc(course_slug, slug, kind):
    doc = C.render_document(slug, kind, course_slug)
    if doc is None:
        # 404 for a bad slug, a bad kind, and a non-public file alike — the
        # response must not tell the difference between "no such week" and
        # "that file exists but isn't yours to read" (solution_app.py).
        abort(404)
    week = next((w for w in C.list_weeks(course_slug) if w["slug"] == slug), None)
    return render_template("learn_doc.html", doc=doc, week=week,
                           course=C.course(course_slug), nav_courses=C.nav_courses())


def _legacy(slug, kind=None):
    """301 to the canonical course-scoped URL, so links converge instead of two
    shapes living side by side forever. Anything already printed or already
    linked from a worksheet keeps working.

    The kind is validated BEFORE redirecting. Without that, this handler 301s any
    second segment at all — `/learn/week04-injection/solution`,
    `/answers`, `/pptx` all returned a redirect instead of a 404. No content
    leaked (the canonical route then refuses the kind), but a 301 confirms the
    path shape to anyone probing for answer keys, and the two routes disagreeing
    about what exists is exactly the drift this indirection was meant to avoid.
    Caught by readiness_check.py's "instructor material is NOT reachable" probe,
    which is there for precisely this.
    """
    if kind is not None and kind not in C.PUBLIC_FILES and kind != "slides":
        abort(404)
    default = C.COURSES[0]["slug"]
    target = (url_for("learn.doc_kind", course_slug=default, slug=slug, kind=kind)
              if kind else
              url_for("learn.doc", course_slug=default, slug=slug))
    return redirect(target, code=301)


@bp.route("/learn/<a>")
@bp.route("/learn/<a>/")
def course_index(a):
    """Either a course's week list, or a legacy bare week URL."""
    c = C.course(a)
    if c is not None:
        return render_template("learn_index.html", course=c,
                               weeks=C.list_weeks(a),
                               modules=C.list_modules(a),
                               nav_courses=C.nav_courses(),
                               only_course=len(C.COURSES) == 1)
    if C.WEEK_RE.match(a or ""):
        return _legacy(a)
    abort(404)


@bp.route("/learn/<course_slug>/<slug>")
def doc(course_slug, slug):
    """Either /learn/<course>/<week>, or legacy /learn/<week>/<kind>."""
    if C.course(course_slug) is not None:
        # Not hardcoded to "worksheet": six weeks have none — the exam weeks are
        # the paper, the review weeks a mock CTF, the practical weeks a CTF brief.
        # See content.PRIMARY_ORDER.
        kind = C.primary_kind(slug, course_slug)
        if kind is None:
            abort(404)
        return _render_doc(course_slug, slug, kind)
    if C.WEEK_RE.match(course_slug or ""):
        return _legacy(course_slug, slug)   # first segment is the week, second the kind
    abort(404)


@bp.route("/learn/<course_slug>/<slug>/<kind>")
def doc_kind(course_slug, slug, kind):
    if C.course(course_slug) is None:
        abort(404)
    return _render_doc(course_slug, slug, kind)
