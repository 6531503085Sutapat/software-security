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

from flask import Blueprint, abort, render_template

import content as C

bp = Blueprint("learn", __name__)

# No script at all. The content plane has zero JS by design, so this is a real
# ceiling rather than an aspiration — if someone later adds a script tag here,
# it fails visibly in development instead of quietly widening the policy.
CSP = ("default-src 'none'; style-src 'self'; img-src 'self' data:; "
       "font-src 'self'; base-uri 'none'; form-action 'none'; "
       "frame-ancestors 'none'")


def _harden(resp):
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@bp.after_request
def _headers(resp):
    return _harden(resp)


@bp.route("/learn")
def index():
    return render_template("learn_index.html", weeks=C.list_weeks())


@bp.route("/learn/<slug>")
@bp.route("/learn/<slug>/<kind>")
def document(slug, kind="worksheet"):
    doc = C.render_document(slug, kind)
    if doc is None:
        # 404 for a bad slug, a bad kind, and a non-public file alike — the
        # response must not tell the difference between "no such week" and
        # "that file exists but isn't yours to read" (solution_app.py).
        abort(404)
    week = next((w for w in C.list_weeks() if w["slug"] == slug), None)
    return render_template("learn_doc.html", doc=doc, week=week)
