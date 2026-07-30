# app.py
import csv
import datetime
import io
import json
import mimetypes
import os

from flask import (
    Flask,
    make_response,
    render_template,
    request,
    send_file,
    session,
    redirect,
    url_for,
    abort,
)
from flask_socketio import SocketIO, join_room, emit

import auth
import db as dbmod
import quiz_loader
from game import GameSession, generate_pin

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-not-secret-override-in-prod")
socketio = SocketIO(app, async_mode="eventlet")

# --- Platform data + config (teachers, question sets, sessions) -------------------------------
# DB_PATH resolves from the env (tests point it at a tmp file; the container defaults to the
# persistent /data volume). The connection + schema are established once, at import time.
DB_PATH = os.environ.get("DB_PATH", "/data/live-quiz.db")
INVITE_CODE = os.environ.get("INVITE_CODE", "")
_conn = dbmod.connect(DB_PATH)
# The default course backfills rows written before assessments/assignments knew
# what a course was — see dbmod.migrate. content is imported here (not at the top)
# because it reads $COURSES at import time and the tests reload it.
import content as _content  # noqa: E402
dbmod.init_db(_conn, default_course=_content.COURSES[0]["slug"])
if not INVITE_CODE:
    print("WARNING: INVITE_CODE is unset — teacher registration is CLOSED until you set it.", flush=True)
if app.config["SECRET_KEY"] == "dev-not-secret-override-in-prod":
    print("WARNING: SECRET_KEY is the insecure default — set a real one before any real use.", flush=True)

# Harden the session cookie: never readable from JS, and not sent on cross-site requests.
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
# Request-body ceiling is set once, further down, next to the upload config that
# determines it — a second value here would silently lose to whichever assignment
# ran last. (It used to be 256 KB, sized for the markdown editor; worksheet
# uploads raised it.)
# SESSION_COOKIE_SECURE is opt-in via env so local http dev still works while TLS prod is hardened.
if os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes"):
    app.config["SESSION_COOKIE_SECURE"] = True


def get_db():
    return _conn


def _now():
    # utcnow() is deprecated (it returns a naive datetime that merely claims to be UTC).
    # Ask for UTC explicitly, then drop the tzinfo so the stored string keeps the exact
    # naive-UTC shape the existing created_at/updated_at rows already use — mixing
    # "...+00:00" into that column would break ordering against older rows.
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(tzinfo=None)
        .isoformat(timespec="seconds")
    )


def _issue_csrf():
    # One CSRF token per session, embedded as a hidden field in every state-changing form.
    if "csrf" not in session:
        session["csrf"] = auth.new_csrf_token()
    return session["csrf"]


def _check_csrf():
    if not auth.csrf_ok(session.get("csrf"), request.form.get("csrf_token")):
        abort(400)

GAMES = {}  # pin -> GameSession
GAME_OWNER = {}  # pin -> teacher_id, so only the creating teacher can export a game's results
HOST_SIDS = {}  # pin -> the socket id currently authorized to drive that game's host controls
SID_TO_PLAYER = {}  # socket id -> (pin, nickname), so a dropped socket can mark its player away
CURRENT_SID = {}    # (pin, nickname) -> latest socket id, to ignore a stale reconnect's disconnect


# The graded weekly quiz (routes_assess) is a separate mode from the live game:
# asynchronous, identified, persisted, and its scores become grades. It lives in
# its own blueprint so the two identity models can't get tangled — the game has
# no accounts at all, the quiz has one-time codes tied to real student IDs.
#
# The helpers are passed through config rather than imported, so routes_assess
# doesn't import app.py back (a cycle) and the test suite can swap them.
app.config.update(GET_DB=get_db, NOW=_now, ISSUE_CSRF=_issue_csrf,
                  CHECK_CSRF=_check_csrf)
import routes_assess  # noqa: E402  (after the helpers it binds to exist)
app.register_blueprint(routes_assess.bp)

# The course content plane (/learn) — read-only, no auth, no student data. It is
# the only surface students reach before they hold any credential, and it renders
# worksheets that contain live XSS payloads as course text, so it carries its own
# script-free CSP on top of content.py's escape-then-parse renderer.
import routes_content  # noqa: E402
app.register_blueprint(routes_content.bp)

# Worksheet submission + rubric grading (/work, /submit) — the last piece off
# Google. Uploads live on disk beside the DB, NOT inside it: worksheet PDFs with
# embedded screenshots would otherwise make the nightly SQLite dump enormous.
# That means backup-ctfd-db.sh must tar this directory — files on a volume are
# not in the database backup, and nothing would tell you until a restore.
app.config["UPLOAD_DIR"] = os.environ.get(
    "UPLOAD_DIR", os.path.join(os.path.dirname(DB_PATH) or ".", "uploads"))
# Bound request bodies at ingestion — Werkzeug 413s anything larger before a
# handler buffers it. 24 MB = submission.py's 20 MB per-file limit plus multipart
# overhead, so a legitimate worksheet PDF lands and submission.py is what refuses
# an oversize one, with a message a student can act on rather than a bare 413.
app.config["MAX_CONTENT_LENGTH"] = 24 * 1024 * 1024
import routes_submit  # noqa: E402
app.register_blueprint(routes_submit.bp)


@app.route("/")
def index():
    """The front door.

    This used to render the live-quiz join screen, because that is all the app
    was when it was written. It is now the smallest part of it — the same app
    serves 19 weeks of course documents, the graded weekly quiz, worksheet
    hand-in and the simulations. A student typing the bare hostname landed on a
    "Game PIN / Nickname" box with no way to reach any of that, which is the
    exact confusion that renaming the host to learn.* was meant to remove.

    So `/` is the course front door and the live game moved to `/play`. Both the
    host screen's projected join URL (static/host.js) and the front door's
    "Join a live game" link point there, so neither audience loses a step.

    This is its OWN page rather than a redirect to /learn. /learn is a list of 19
    weeks — a fine second click, a poor first one: it answers "which week?" when
    the student's actual question is "where do I go?", and it says nothing about
    the quiz, the hand-in or the arena until you scroll past every week. The home
    page answers the real question and, for each destination, says up front what
    it costs to walk in: nothing, a PIN, a code, or the class VPN.
    """
    import content as C
    courses = C.list_courses()
    # The arena is configured per course. Show the link here only when every
    # course that has one agrees — otherwise a student in course B would be sent
    # to course A's arena, which is worse than no link at all. When they differ,
    # the link lives on each course's own page instead.
    arenas = {c.get("arena_url") for c in courses if c.get("arena_url")}
    # The named modules a course declares, so its card can show the shape of the
    # course rather than a sentence identical to every other card's. Courses that
    # declare none map to [] and the card falls back to its composition line.
    outline = {c["slug"]: C.list_modules(c["slug"]) for c in courses}
    return render_template("home.html", courses=courses, one=len(courses) == 1,
                           outline=outline, nav_courses=C.nav_courses(),
                           arena_url=arenas.pop() if len(arenas) == 1 else None)


# ── Error pages a student can actually get out of ──────────────────────────
# Werkzeug's default 404 is 207 bytes of unstyled English with no link anywhere.
# Students DO hit it: a mistyped week slug, a stale bookmark, a URL read off a
# projector. Six weeks of them hit it for months because /learn/<week> 404'd for
# the exam blocks, and the page gave them nothing to do about it.
#
# The headers are set explicitly rather than left to the content blueprint's
# after_request: an error can be raised from any blueprint or from routing itself,
# before any blueprint owns the request, so relying on that hook would leave some
# error responses without a CSP.
_ERRORS = {
    404: ("Page not found",
          "That address does not exist on this site. It is usually a mistyped "
          "week name, or a link that has moved."),
    403: ("Not allowed",
          "You do not have access to that. If you were following a link from "
          "class, ask your teacher to check it."),
    500: ("Something broke on our side",
          "This is our fault, not yours. Tell your teacher what you were doing "
          "and try again in a minute."),
}


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(500)
def _error_page(exc):
    code = getattr(exc, "code", 500) or 500
    heading, message = _ERRORS.get(code, _ERRORS[500])
    resp = make_response(render_template("error.html", code=code,
                                         heading=heading, message=message), code)
    # Same script-free policy as the content plane — an error page is rendered on
    # the same origin as the teacher's authenticated session and has no reason to
    # execute anything.
    resp.headers["Content-Security-Policy"] = (
        "default-src 'none'; style-src 'self'; img-src 'self' data:; "
        "font-src 'self'; base-uri 'none'; form-action 'none'")
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


# The app-plane CSP. `/learn/*` and `/sim/*` set their own, stricter ones in
# routes_content.py and are left alone here; everything else — `/`, `/login`,
# `/quiz`, `/submit`, `/play`, the teacher console — had NO CSP at all, which
# meant the one public page carrying a password form was the least protected
# page on the site.
#
# It differs from the content plane's policy in exactly two ways, both required:
#   script-src 'self'  — /play and /host run first-party Socket.IO
#   form-action 'self' — these pages are the ones with real forms to submit
# Still no 'unsafe-inline' anywhere, so a stored payload cannot execute.
_APP_CSP = ("default-src 'none'; script-src 'self'; connect-src 'self'; "
            "style-src 'self'; img-src 'self' data:; font-src 'self'; "
            "frame-src 'self'; base-uri 'none'; form-action 'self'; "
            "frame-ancestors 'none'")


def _asset_version() -> str:
    """A cache-busting token derived from the stylesheet's own mtime.

    Long-lived caching and a URL that never changes are incompatible: the CSS
    was being revalidated on every navigation precisely because it had no
    fingerprint to make caching safe. `?v=<mtime>` gives it one, so the file can
    be cached hard and still change the instant a deploy rewrites it. Computed
    once at import — the file cannot change under a running container.
    """
    try:
        return str(int(os.path.getmtime(
            os.path.join(app.static_folder, "style.css"))))
    except OSError:
        return "0"


ASSET_V = _asset_version()


@app.context_processor
def _shell_context():
    """Give every template the course switcher without each route remembering to.

    base.html renders its tier-1 switcher only when `nav_courses` has more than
    one entry, so the four routes that forgot to pass it (quiz, submit, login,
    register) made the black bar appear and disappear as a student navigated —
    the header changed shape between clicks.

    Doing this app-wide was previously ruled out for cost, but that reasoning
    applied to list_courses(), which walks the content directories. nav_courses()
    is a projection over COURSES, a list built once at import: three dicts, no
    filesystem access. It is also deliberately a PROJECTION — the raw course
    dicts carry `root`, an absolute server path that must never reach a template.
    An explicit nav_courses= kwarg still wins, so nothing that passes its own is
    affected, and /host and /play simply never read the name.
    """
    return {"nav_courses": _content.nav_courses(),
            "kind_label": _content.kind_label,
            "asset_v": ASSET_V}


@app.after_request
def _app_headers(resp):
    # setdefault throughout: a blueprint that already chose a policy (the content
    # plane's stricter one, or /work/file's `sandbox`) keeps it. Duplicate
    # nosniff headers used to be emitted on /learn for exactly this reason.
    resp.headers.setdefault("Content-Security-Policy", _APP_CSP)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    # Static assets are content-addressed by name only, so they were revalidated
    # on every navigation — a 352 KB font and a 90 KB stylesheet, every page.
    # Immutable for a year for the fingerprinted font; the stylesheet gets a
    # shorter window because its URL never changes.
    if request.path.startswith("/static/"):
        # Fonts are content-stable and their names never change; the stylesheet
        # is cached just as hard because base.html appends ?v=<mtime>, so a
        # deploy changes the URL. Assignment, not setdefault: Flask's static
        # handler has already put `no-cache` here, which is the thing being fixed.
        if request.path.startswith(("/static/fonts/", "/static/style.css")):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


@app.route("/robots.txt")
def robots():
    """Crawl policy. The course material is deliberately public and we WANT it
    indexed; the graded surfaces and the teacher tools are noise at best and a
    login wall at worst, so they are excluded rather than left to be crawled and
    soft-404'd."""
    body = ("User-agent: *\n"
            "Allow: /learn\n"
            "Allow: /sim\n"
            "Disallow: /login\n"
            "Disallow: /register\n"
            "Disallow: /console\n"
            "Disallow: /host\n"
            "Disallow: /play\n"
            "Disallow: /quiz\n"
            "Disallow: /submit\n"
            "Disallow: /work\n"
            "Disallow: /assess\n"
            f"\nSitemap: {request.url_root.rstrip('/')}/sitemap.xml\n")
    resp = make_response(body)
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    return resp


@app.route("/sitemap.xml")
def sitemap():
    """Every publicly readable URL, built from the same content functions the
    pages use — so it cannot drift from what is actually served."""
    from xml.sax.saxutils import escape as _x
    base = request.url_root.rstrip("/")
    urls = [f"{base}/", f"{base}/learn", f"{base}/sim"]
    for c in _content.COURSES:
        urls.append(f"{base}/learn/{c['slug']}/")
        for d in _content.list_course_docs(c["slug"]):
            urls.append(f"{base}/learn/{c['slug']}/doc/{d['name']}")
        for w in _content.list_weeks(c["slug"]):
            urls.append(f"{base}/learn/{c['slug']}/{w['slug']}")
            for kind in w.get("available", ()):
                urls.append(f"{base}/learn/{c['slug']}/{w['slug']}/{kind}")
    for slug in _content.SIMS:
        urls.append(f"{base}/sim/{slug}")
    body = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{_x(u)}</loc></url>\n" for u in urls)
            + "</urlset>\n")
    resp = make_response(body)
    resp.headers["Content-Type"] = "application/xml; charset=utf-8"
    return resp


@app.route("/play")
def play():
    """The live-quiz join screen — Game PIN + nickname.

    Kept as its own path rather than at `/` so the bare hostname can mean
    "the course". The host screen shows this URL during a game.
    """
    return render_template("player.html")


@app.route("/host", methods=["GET"])
@auth.login_required
def host_page():
    # the set+topic are chosen in the console, which POSTs straight to /host/create;
    # a bare GET /host just sends the teacher to their console to pick one.
    return redirect(url_for("console_page"))


@app.route("/host/create", methods=["POST"])
@auth.login_required
def host_create():
    _check_csrf()
    tid = auth.current_teacher_id()
    try:
        set_id = int(request.form.get("set_id", ""))
    except ValueError:
        abort(404)                                   # malformed id -> same not-found as unowned
    if not (0 < set_id <= 2**63 - 1):
        abort(404)                                   # out of SQLite INTEGER range -> not-found, never a 500
    s = dbmod.get_set(get_db(), set_id, tid)
    if s is None:
        abort(404)                                   # not this teacher's set (IDOR-safe)
    topics = quiz_loader.parse_topics_from_text(s["source_md"])
    topic = request.form.get("topic") or next(iter(topics), None)
    questions = topics.get(topic, [])
    if not questions:
        abort(400)
    pin = generate_pin()
    while pin in GAMES:  # avoid an extremely unlikely PIN collision
        pin = generate_pin()
    GAMES[pin] = GameSession(pin, questions)
    GAME_OWNER[pin] = tid
    return render_template("host.html", created_pin=pin)


@app.route("/host/<pin>/export")
@auth.login_required
def host_export(pin):
    game = GAMES.get(pin)
    if game is None or GAME_OWNER.get(pin) != auth.current_teacher_id():
        return "not found", 404                      # unknown OR not this teacher's game
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=["nickname", "total_score", "correct_count", "avg_response_time_ms"]
    )
    writer.writeheader()
    writer.writerows(game.export_results())
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"quiz-{pin}-results.csv")


# --- Teacher auth: register / login / logout --------------------------------------------------


@app.route("/register", methods=["GET", "POST"])
def register_page():
    # HEAD is dispatched to this view too (Flask derives it from GET). Testing
    # `== "GET"` let it fall through to the POST branch and abort(400) on the
    # missing CSRF field, so every uptime monitor and link checker saw the
    # sign-up page as broken.
    if request.method in ("GET", "HEAD"):
        return render_template("register.html", csrf_token=_issue_csrf(),
                               error=None, nav_courses=_content.nav_courses())
    _check_csrf()
    username = (request.form.get("username") or "").strip()[:40]
    password = request.form.get("password") or ""
    if not auth.invite_ok(request.form.get("invite"), INVITE_CODE):
        return render_template("register.html", csrf_token=_issue_csrf(), nav_courses=_content.nav_courses(), error="Invalid invite code."), 200
    if len(username) < 3 or len(password) < 8:
        return render_template("register.html", csrf_token=_issue_csrf(),
                               nav_courses=_content.nav_courses(),
                               error="Username ≥ 3 chars, password ≥ 8 chars."), 200
    # DELIBERATE DEVIATION FROM PLAN: bcrypt 5.x RAISES `ValueError: password cannot be longer
    # than 72 bytes` (no silent truncation), so an over-long password would 500 hash_password.
    # Reject it here with a friendly 200 form error instead of letting the route crash.
    if len(password.encode("utf-8")) > 72:
        return render_template("register.html", csrf_token=_issue_csrf(),
                               nav_courses=_content.nav_courses(),
                               error="Password must be 8–72 characters."), 200
    if dbmod.get_teacher_by_username(get_db(), username):
        return render_template("register.html", csrf_token=_issue_csrf(), nav_courses=_content.nav_courses(), error="Username taken."), 200
    tid = dbmod.create_teacher(get_db(), username, auth.hash_password(password), _now())
    session["teacher_id"] = tid
    return redirect(url_for("console_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method in ("GET", "HEAD"):        # see register_page
        return render_template("login.html", csrf_token=_issue_csrf(),
                               error=None, nav_courses=_content.nav_courses())
    _check_csrf()
    t = dbmod.get_teacher_by_username(get_db(), (request.form.get("username") or "").strip())
    if t and auth.verify_password(request.form.get("password") or "", t["password_hash"]):
        session.clear()                              # anti session-fixation: drop any pre-login state
        session["teacher_id"] = t["id"]
        session["csrf"] = auth.new_csrf_token()      # a fresh token bound to the new session
        return redirect(url_for("console_page"))
    return render_template("login.html", csrf_token=_issue_csrf(), nav_courses=_content.nav_courses(), error="Wrong username or password."), 200


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# --- Teacher console: question-set CRUD + live parse preview ----------------------------------
# Every route below is login-gated AND owner-scoped: a set is only ever fetched/updated/deleted
# with owner_id = the logged-in teacher's id (db.get_set/update_set/delete_set enforce
# `teacher_id = owner_id` in SQL). A teacher poking at another teacher's set id therefore gets a
# 404 (get_set -> None -> abort) and update/delete no-op (rowcount 0 -> abort) — never a data leak
# or a cross-tenant write (IDOR-safe).

MAX_TITLE_LEN = 120            # a set title is capped, not a crash risk
MAX_SOURCE_BYTES = 100 * 1024  # 100 KB cap on a set's pasted/uploaded markdown


def _read_source(req):
    # Accept either a pasted textarea or an uploaded .md file. Read a little past the cap so
    # oversize input is *rejected* by _source_too_big below rather than silently truncated.
    f = req.files.get("source_file")
    if f and f.filename:
        raw = f.read(MAX_SOURCE_BYTES + 1024)
        return raw.decode("utf-8", errors="replace")
    return req.form.get("source_md") or ""


def _source_too_big(source_md):
    return len(source_md.encode("utf-8")) > MAX_SOURCE_BYTES


def _parse_or_none(source_md):
    # Returns the parsed topics only if at least one question was recognised, else None so the
    # route can refuse an empty/unparseable set with a friendly form error (never store junk).
    topics = quiz_loader.parse_topics_from_text(source_md or "")
    total = sum(len(v) for v in topics.values())
    return topics if total > 0 else None


def _set_form(error=None, editing=None, title="", source_md=""):
    # Render the create/edit form. `editing` (a set Row) switches the form to edit mode; when
    # re-rendering after a validation error we echo the submitted title/source so work isn't lost.
    return render_template(
        "set_form.html",
        csrf_token=_issue_csrf(),
        error=error,
        editing=editing,
        title=title,
        source_md=source_md,
    )


@app.route("/console")
@auth.login_required
def console_page():
    sets = dbmod.list_sets(get_db(), auth.current_teacher_id())
    # Per-set metadata for the console cards: the topic names (populate the "Start game" dropdown)
    # plus a question count so a teacher can see a set's size at a glance.
    set_meta = {}
    for s in sets:
        parsed = quiz_loader.parse_topics_from_text(s["source_md"])
        set_meta[s["id"]] = {"topics": list(parsed.keys()),
                             "count": sum(len(v) for v in parsed.values())}
    return render_template("console.html", sets=sets, set_meta=set_meta, csrf_token=_issue_csrf())


@app.route("/console/preview", methods=["POST"])
@auth.login_required
def console_preview():
    _check_csrf()
    # Bound the work: parse at most the size cap so a giant paste can't tie up the worker.
    source_md = (request.form.get("source_md") or "")[:MAX_SOURCE_BYTES]
    topics = quiz_loader.parse_topics_from_text(source_md)
    payload = {"topics": [{"topic": k, "count": len(v)} for k, v in topics.items()]}
    return app.response_class(json.dumps(payload), mimetype="application/json")


@app.route("/console/sets/new", methods=["GET", "POST"])
@auth.login_required
def console_set_new():
    if request.method == "GET":
        return _set_form()
    _check_csrf()
    title = (request.form.get("title") or "").strip()[:MAX_TITLE_LEN] or "Untitled set"
    source_md = _read_source(request)
    if _source_too_big(source_md):
        return _set_form(error="That set is too large (max 100 KB).", title=title, source_md=""), 200
    if _parse_or_none(source_md) is None:
        return _set_form(error="That set has no questions the parser can read — check the format.",
                         title=title, source_md=source_md), 200
    dbmod.create_set(get_db(), auth.current_teacher_id(), title, source_md, _now())
    return redirect(url_for("console_page"))


@app.route("/console/sets/<int:set_id>/edit", methods=["GET", "POST"])
@auth.login_required
def console_set_edit(set_id):
    s = dbmod.get_set(get_db(), set_id, auth.current_teacher_id())
    if s is None:
        abort(404)                                   # not this teacher's set (IDOR-safe)
    if request.method == "GET":
        return _set_form(editing=s, title=s["title"], source_md=s["source_md"])
    _check_csrf()
    title = (request.form.get("title") or "").strip()[:MAX_TITLE_LEN] or s["title"]
    source_md = _read_source(request)
    if _source_too_big(source_md):
        return _set_form(error="That set is too large (max 100 KB).",
                         editing=s, title=title, source_md=s["source_md"]), 200
    if _parse_or_none(source_md) is None:
        return _set_form(error="That set has no questions the parser can read — check the format.",
                         editing=s, title=title, source_md=source_md), 200
    dbmod.update_set(get_db(), set_id, auth.current_teacher_id(), title, source_md, _now())
    return redirect(url_for("console_page"))


@app.route("/console/sets/<int:set_id>/delete", methods=["POST"])
@auth.login_required
def console_set_delete(set_id):
    _check_csrf()
    if dbmod.delete_set(get_db(), set_id, auth.current_teacher_id()) == 0:
        abort(404)                                   # unknown OR not this teacher's set
    return redirect(url_for("console_page"))


@socketio.on("host_join")
def on_host_join(data):
    pin = data["pin"]
    # host and players share this Socket.IO room by design (broadcasts like question:show reach
    # everyone) — room membership is not the security boundary, HOST_SIDS below is. Only a socket
    # whose Flask session belongs to the game's actual owner gets bound as its authorized host;
    # `pin in GAME_OWNER` is required explicitly so an unauthenticated socket (current_teacher_id()
    # is None) can never bind to a pin that also happens to have no registered owner.
    join_room(pin)
    if pin in GAME_OWNER and auth.current_teacher_id() == GAME_OWNER[pin]:
        HOST_SIDS[pin] = request.sid


@socketio.on("player_join")
def on_player_join(data):
    game = GAMES.get(data["pin"])
    if game is None:
        emit("join_error", {"message": "unknown game PIN"})
        return
    # trust nothing from the socket: cap length and drop control chars server-side
    # (the client maxlength is cosmetic and bypassable), then require something left
    nickname = "".join(c for c in (data.get("nickname") or "") if c.isprintable()).strip()[:24]
    if not nickname:
        emit("join_error", {"message": "pick a nickname"})
        return
    game.join(nickname)
    join_room(data["pin"])
    SID_TO_PLAYER[request.sid] = (data["pin"], nickname)
    CURRENT_SID[(data["pin"], nickname)] = request.sid
    emit("join_ok", {"nickname": nickname})
    # if a question is already live, show it to this (re)joining player instead of a blank wait
    q = game.current_question()
    if q is not None and not getattr(game, "_revealed_this_round", False):
        emit(
            "question:show",
            {
                "stem": q["stem"],
                "options": q["options"],
                "time_limit": game.time_limit,
                "index": game.current_index,
                "total": len(game.questions),
                "players": _connected_count(game),
            },
        )
    _broadcast_lobby(game, data["pin"])


def _broadcast_lobby(game, pin):
    # let the host's lobby screen fill up (and thin out) live as players come and go
    socketio.emit(
        "lobby:update",
        {"count": _connected_count(game), "players": sorted(game.players)[:60]},
        to=pin,
    )


@socketio.on("disconnect")
def on_disconnect():
    info = SID_TO_PLAYER.pop(request.sid, None)
    if info is None:
        return  # e.g. the host socket — the game persists, nothing to do
    pin, nickname = info
    if CURRENT_SID.get((pin, nickname)) != request.sid:
        return  # the player already reconnected on a newer socket; ignore the stale drop
    CURRENT_SID.pop((pin, nickname), None)
    game = GAMES.get(pin)
    if game is None:
        return
    game.disconnect(nickname)
    _broadcast_lobby(game, pin)
    # We deliberately do NOT reveal the round here: a disconnect can be a brief wifi blip of the
    # last un-answered player, and revealing on it would prematurely end the round and rob that
    # player of their answer. The round stays bounded by the 20s timer and still ends early when
    # the remaining connected players all answer (handled in on_answer_submit).


@socketio.on("host_next")
def on_host_next(data):
    if HOST_SIDS.get(data["pin"]) != request.sid:
        return  # only the socket bound as this game's host in on_host_join may drive it
    game = GAMES.get(data["pin"])
    if game is None:
        return
    question = game.next_question()
    if question is None:
        emit("game:finished", {"leaderboard": game.leaderboard(top_n=len(game.players))}, to=data["pin"])
        return
    emit(
        "question:show",
        {
            "stem": question["stem"],
            "options": question["options"],
            "time_limit": game.time_limit,
            "index": game.current_index,
            "total": len(game.questions),
            "players": _connected_count(game),
        },
        to=data["pin"],
    )
    socketio.start_background_task(_auto_reveal_after_timeout, data["pin"], game.current_index)


def _connected_count(game):
    return sum(1 for p in game.players.values() if p.connected)


def _auto_reveal_after_timeout(pin, question_index):
    game = GAMES.get(pin)
    if game is None:
        return
    socketio.sleep(game.time_limit)
    # only reveal if the round is still the same one (host may have already advanced)
    # and results haven't already been sent because everyone answered early
    if game.current_index == question_index and not getattr(game, "_revealed_this_round", False):
        _reveal_results(pin)


def _reveal_results(pin):
    game = GAMES.get(pin)
    if game is None:
        return
    if getattr(game, "_revealed_this_round", False):
        return  # already revealed for this round (guards both the timeout path and the
                # all-answered path from double-firing regardless of which ran first)
    game._revealed_this_round = True
    q = game.current_question()
    socketio.emit(
        "question:results",
        {
            "distribution": game.answer_distribution(),
            "leaderboard": game.leaderboard(),
            "correct": q["correct"] if q else None,
        },
        to=pin,
    )


@socketio.on("answer_submit")
def on_answer_submit(data):
    # the answering identity comes from this socket's own join record, never from the payload —
    # otherwise any connected player could submit/score under another player's nickname
    info = SID_TO_PLAYER.get(request.sid)
    if info is None or info[0] != data["pin"]:
        return
    nickname = info[1]
    game = GAMES.get(data["pin"])
    if game is None:
        return
    if getattr(game, "_revealed_this_round", False):
        return  # the round is already revealed; a late tap must not score after the fact
    try:
        result = game.submit_answer(nickname, data["choice"])
    except ValueError:
        return
    if result is None:
        return
    # feedback carries the player's authoritative cumulative score so the phone never has to
    # guess it (client-side accumulation drifts across a reconnect)
    player = game.players.get(nickname)
    emit("answer:feedback", {**result, "score": player.score if player else 0})
    # keep the projector's "answered" counter climbing live — count only still-connected answerers
    answered = sum(1 for n in game.answers_this_round if game.players[n].connected)
    socketio.emit(
        "answer:tally",
        {"answered": answered, "total": _connected_count(game)},
        to=data["pin"],
    )
    if game.all_answered():
        _reveal_results(data["pin"])


if __name__ == "__main__":
    # PORT override is for local dev outside Docker (macOS AirPlay squats on 5000);
    # the container keeps the 5000 default and docker-compose maps it to host 5050.
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
