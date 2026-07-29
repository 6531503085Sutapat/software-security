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

from flask import Blueprint, abort, make_response, render_template

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
