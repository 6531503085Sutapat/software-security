"""
content.py — serve the course's own markdown (worksheets, lab READMEs) as HTML.

This is the content plane: SP-3 in instructor/FULL-PLATFORM-DESIGN.md, and the
half of "no Google" that replaces Classroom's *distribute the material* role.
Read-only, no student data, no upload.

WHY THIS DOESN'T USE A MARKDOWN LIBRARY
    Because of what is actually in these files. `labs/week05-xss-client-side/
    worksheet.md` line 56 instructs students to POST:

        <script>alert(document.cookie)</script>

    and line 61 gives them a beacon that exfiltrates the cookie to a remote URL.
    Those are course content — the exercise — and they must render as *visible
    text a student can read and copy*, never as markup the browser executes.

    Every mainstream markdown renderer passes raw HTML through by default.
    Pointing one at this repo and serving the result from the same origin as the
    teacher's authenticated session would be stored XSS, delivered by our own
    teaching material, into the account that holds every student's grade. The
    Week 5 lab would have worked on the platform that teaches it.

    So: **escape the whole document first, then apply a small whitelist of
    markdown constructs to the already-escaped text.** Nothing can pass through,
    because by the time any construct is recognised there is no live markup left
    to recognise. That ordering is the entire security argument, and
    `test_content.py` holds it in place with the real Week 5 payloads.

    The cost is a deliberately limited dialect: headings, bold/italic/code,
    fenced code, lists, tables, links, blockquotes, rules. That covers what the
    worksheets use. It does not do footnotes, definition lists or inline HTML,
    and it should not grow to.

PATH SAFETY
    Content is addressed by a slug matched against a strict pattern and resolved
    against a fixed root, then verified to still be inside it after resolution —
    a slug never becomes a path fragment that `..` can walk out of.
"""

from __future__ import annotations

import html
import json
import os
import re

# Where the weekNN-* directories live.
#
# Local dev: this module sits in labs/live-quiz/, so the default (its parent) is
# `labs/` and everything just works from a checkout.
#
# In the container the app is at /app and there is no repo above it, so the
# default would resolve to `/` and every week would 404 — which is exactly what
# the first production deploy did. The image therefore bakes the content in at
# /content and sets CONTENT_ROOT to match. (The lab solutions this copies are
# already public in the repo; the real answer keys live in git-ignored
# instructor/ and are not in the build context at all.)
CONTENT_ROOT = os.environ.get(
    "CONTENT_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# A course's content directories. Anchored, no dots, so `..` and absolute paths
# never match — that property is load-bearing and survives every change below.
#
# The unit prefix is PER COURSE because the real courses disagree:
#   software-security       week01-threat-modeling … week19-…
#   security-cryptography   week01-intro … week14-…
#   cloud-infrastructure    lesson01-03-aws-…, lesson07b-cloudtrail-…, lesson13-…
# and cloud-infra's numbering is not even regular: a lesson can span two numbers
# (`01-03`) or carry a letter suffix (`07b`). So the number is captured as an
# opaque STRING for display and never parsed into an int — the previous
# `int(name[4:6])` was a positional slice that assumed "week" + exactly 2 digits
# and would raise on `lesson07b`.
#
# Ordering stays lexical on the directory name, which is correct precisely
# because the numbers are zero-padded: lesson04 < lesson07 < lesson07b < lesson10.
UNIT_RE_CACHE: dict[str, re.Pattern] = {}
UNIT_NAME_RE = re.compile(r"^[a-z]{2,16}$")


def unit_re(unit: str = "week") -> re.Pattern:
    if unit not in UNIT_RE_CACHE:
        if not UNIT_NAME_RE.match(unit):
            raise ValueError(f"bad unit name {unit!r}")
        UNIT_RE_CACHE[unit] = re.compile(
            rf"^{unit}(\d{{2}}[a-z]?(?:-\d{{2}})?)-([a-z0-9-]+)$")
    return UNIT_RE_CACHE[unit]


# Kept for the many callers and tests that predate multi-course: the default unit.
WEEK_RE = re.compile(r"^week\d{2}[a-z]?(?:-\d{2})?-[a-z0-9-]+$")

# ── Courses ────────────────────────────────────────────────────────────────
# The instructor teaches several courses (software-security,
# security-cryptography, cloud-infrastructure-security) rendered from one
# curriculum monorepo. This plane used to serve exactly one of them: CONTENT_ROOT
# pointed at a single repo's `labs/` and the index was titled in the template.
#
# A course is (slug, title, root). Nothing more — a course is an ordering over
# week directories, which is also all a manifest is in the monorepo.
#
# Course slugs must NOT look like a week directory. `/learn/<x>` is ambiguous
# between "course x" and the legacy "week x of the default course", and we
# disambiguate on WEEK_RE. _load_courses() rejects a slug that would collide, so
# the ambiguity can never arise from configuration.
COURSE_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")


def _load_courses() -> list[dict]:
    """Course registry, from $COURSES (JSON) or a single course from CONTENT_ROOT.

    The single-course default is what keeps this change invisible to the current
    deployment: with no $COURSES set the platform behaves exactly as before,
    serving CONTENT_ROOT under one course.

    $COURSES is a JSON list of {slug, title, root, arena_url?}. `root` is the
    directory holding the weekNN-* dirs (i.e. a course repo's `labs/`).
    """
    raw = os.environ.get("COURSES", "").strip()
    if not raw:
        return [{
            "slug": os.environ.get("COURSE_SLUG", "software-security"),
            "title": os.environ.get("COURSE_TITLE", "Software Security"),
            "root": CONTENT_ROOT,
            "arena_url": os.environ.get("ARENA_URL", "").strip() or None,
            "unit": "week",
            "unit_label": "Week",
        }]
    out, seen = [], set()
    for c in json.loads(raw):
        slug = str(c.get("slug", "")).strip()
        if not COURSE_SLUG_RE.match(slug):
            raise ValueError(f"COURSES: bad course slug {slug!r}")
        if WEEK_RE.match(slug):
            # Would make /learn/<slug> ambiguous with a legacy week URL.
            raise ValueError(f"COURSES: slug {slug!r} collides with a week directory name")
        if slug in seen:
            raise ValueError(f"COURSES: duplicate slug {slug!r}")
        seen.add(slug)
        root = os.path.realpath(str(c["root"]))
        if not os.path.isdir(root):
            raise ValueError(f"COURSES: {slug!r} root does not exist: {root}")
        unit = str(c.get("unit") or "week")
        if not UNIT_NAME_RE.match(unit):
            raise ValueError(f"COURSES: {slug!r} has bad unit {unit!r}")
        out.append({"slug": slug, "title": str(c.get("title") or slug),
                    "root": root, "arena_url": (c.get("arena_url") or None),
                    "unit": unit,
                    "unit_label": str(c.get("unit_label") or unit.capitalize())})
    if not out:
        raise ValueError("COURSES was set but produced no courses")
    return out


COURSES = _load_courses()


def list_courses() -> list[dict]:
    """Every configured course, with how many weeks each currently publishes."""
    return [{**c, "week_count": len(list_weeks(c["slug"]))} for c in COURSES]


def course(slug: str | None) -> dict | None:
    """Resolve a course slug. `None` means the default (first) course, which is
    what every pre-existing single-course caller and URL relies on."""
    if slug is None:
        return COURSES[0]
    return next((c for c in COURSES if c["slug"] == slug), None)


def _root_of(course_slug: str | None) -> str | None:
    c = course(course_slug)
    return c["root"] if c else None
# Every student-facing document a week can carry, keyed by the URL segment.
#
# Still an ALLOWLIST of exact filenames, not a pattern or a denylist: a lab
# directory also holds `solution_app.py`, `vulnerable_app.py` and compose files,
# and the answer keys live in the git-ignored instructor/ tree. Nothing here may
# ever be widened to "any .md" — the point is that adding a file to a lab does
# not silently publish it.
#
# The six non-lab weeks (review, written exam, practical CTF) carry no
# worksheet.md at all: their material IS mock-ctf.md / exam.md / ctf.md. Before
# these were listed, /learn showed those weeks as a README and nothing else —
# the main document for six of nineteen weeks was simply absent from the
# platform while appearing complete on disk.
PUBLIC_FILES = {
    "worksheet": "worksheet.md",
    "readme": "README.md",
    # non-lab weeks — this is their primary material
    "mock-ctf": "mock-ctf.md",          # W7, W17 review
    "exam": "exam.md",                  # W8, W18 written
    "ctf": "ctf.md",                    # W9, W19 practical
    "scrimmage": "scrimmage.md",        # W16 capstone
    # per-week supplements a worksheet references
    "attack": "attack.md",              # W6, W10, W14
    "harden": "harden.md",              # W13
    "dependency-confusion": "dependency-confusion.md",  # W12
    "template": "THREAT-MODEL-TEMPLATE.md",             # W1 — students fill this in
    "pipeline": "README-pipeline.md",   # W15
}

# Lecture decks live outside the week directory, at slides/weekNN.md. Served
# read-only like everything else here; the generated .pptx is NOT served (it is
# a binary the renderer can't make inert, and the markdown is the source anyway).
SLIDES_DIR = "slides"

# Interactive simulations a worksheet may embed, by slug. An ALLOWLIST, because
# this is the one construct in the whole renderer that produces an <iframe> —
# a slug that isn't here renders as an ordinary code block, so a typo or a
# hostile string degrades to visible text rather than to markup.
#
# A worksheet embeds one with a fenced block:
#
#     ```sim
#     trust-boundary
#     ```
#
# A fence is used rather than a link because it cannot occur by accident in
# prose, and because the body is matched whole against this dict.
SIMS = {
    "trust-boundary": "Trust boundaries & threat chaining (Week 1)",
    "sqli-parse": "How concatenation changes the SQL parse tree (Week 4)",
}


def list_weeks(course_slug: str | None = None) -> list[dict]:
    """Every week directory that has something public to show, in order.

    `course_slug=None` keeps the original single-course behaviour.
    """
    c = course(course_slug)
    if c is None:
        return []
    root = c["root"]
    pat = unit_re(c.get("unit", "week"))
    out = []
    for name in sorted(os.listdir(root)):
        m = pat.match(name)
        if not m:
            continue
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        available = [k for k, f in PUBLIC_FILES.items()
                     if os.path.isfile(os.path.join(d, f))]
        if _slides_path(m.group(1), course_slug):
            available.append("slides")
        if not available:
            continue
        # The title must be the one on the document the row OPENS, not the
        # README's. Verified 2026-07-30: week 7's README says "Reflection &
        # Review (pre-Midterm)" while the row links mock-ctf.md, titled "Mock CTF
        # (Midterm dry-run)". The list promised revision and delivered a timed
        # CTF. Same divergence on weeks 8, 9, 18, 19 — the exam blocks.
        primary = None
        for k in PRIMARY_ORDER:
            if k in available:
                primary = k
                break
        primary = primary or (available[0] if available else None)
        primary_file = (PUBLIC_FILES.get(primary) if primary != "slides"
                        else None)
        title = None
        if primary_file:
            title = _title_of(os.path.join(d, primary_file))
        title = title or _title_of(os.path.join(d, "worksheet.md")) \
            or _title_of(os.path.join(d, "README.md")) \
            or name[7:].replace("-", " ").title()
        num = m.group(1)
        out.append({
            "slug": name,
            # TWO fields, because one cannot be both sortable and truthful.
            # `number` is an int taken from the leading two digits, which the
            # pattern guarantees exist — so ordering stays numeric (an earlier
            # attempt made this a string and "10" sorted before "2"; the existing
            # tests caught it, correctly).
            # `number_label` is what a student reads, and it keeps the
            # irregularity the cloud course actually has: "7b", "1-3".
            "number": int(num[:2]),
            "number_label": _num_label(num),
            "unit_label": c.get("unit_label", "Week"),
            "badge": PRIMARY_BADGE.get(primary, ""),
            "graded": PRIMARY_BADGE.get(primary, "") in GRADED_BADGES,
            "title": title,
            "short_title": short_title(title),
            "primary": primary,
            "available": available,
        })
    return out


# Which document IS the week, when the URL doesn't say. Order matters and is not
# alphabetical: it is "the thing a student opens when they open the week".
#
# Six of the nineteen weeks have NO worksheet.md — the review weeks are a
# mock CTF, the exam weeks are the paper, the practical weeks are the CTF brief.
# `/learn/<course>/<week>` used to hardcode `kind="worksheet"` for all of them,
# so **week07, 08, 09, 17, 18 and 19 returned 404 on their main link** — both
# written exams, both midterm/final CTFs and both mock CTFs, i.e. the six
# highest-stakes documents in the course. Present since the content plane was
# first built; found 2026-07-30 by requesting every week's bare URL rather than
# by reading the route.
# Titles as a student should read them in a LIST, which is not how they read at
# the top of a document. The headings carry context the row already gives —
# "Worksheet 4 — ", "Week 8 — " — and an hours figure that is wrong twice over:
# worksheets 13-16 say "(4 hrs)", but a KOSEN class is 3 hours and an MFU session
# is a whole Saturday. Verified against all 19 real headings.
_TRIM_LEAD = re.compile(
    r"^(?:Worksheet|Week|Lab|Lesson)s?(?:\s+[\d\u2013-]+)?\s*[:—–-]\s*", re.I)
_TRIM_TAIL = re.compile(r"\s*\((?:\d+(?:\.\d+)?\s*(?:hrs?|hours?)|Week\s+\d+)\)\s*$", re.I)


def _num_label(num: str) -> str:
    """"07" -> "7" · "07b" -> "7b" · "01-03" -> "1-3" (a range of lessons)."""
    parts = num.split("-")
    out = []
    for part in parts:
        digits = part[:2].lstrip("0") or "0"
        out.append(digits + part[2:])
    return "\u2013".join(out) if len(out) > 1 else out[0]


def short_title(title: str) -> str:
    """A list-row title. Never returns empty — an unmatched heading renders raw,
    which is redundant rather than blank."""
    if not title:
        return title
    out = title.strip()
    # Repeat: the cloud course stacks two prefixes — "Worksheet — Lessons 1-3: ".
    # Bounded so a pathological title cannot spin.
    for _ in range(4):
        nxt = _TRIM_LEAD.sub("", out, count=1).strip()
        if nxt == out:
            break
        out = nxt
    out = _TRIM_TAIL.sub("", out).strip()
    return out or title.strip()


# What KIND of thing a unit is, from the document that IS it. A student scanning
# 19 rows needs to see at a glance which ones are assessments — the exam weeks and
# the midterm/final CTFs look exactly like an ordinary lab in a bare list, and
# that is how someone walks into a graded block expecting a worksheet.
PRIMARY_BADGE = {
    "worksheet": "LAB",
    "mock-ctf": "REVIEW",
    "exam": "EXAM",
    "ctf": "CTF",
    "scrimmage": "CAPSTONE",
    "readme": "GUIDE",
}
# The two that carry a mark. Rendered differently, and never by colour alone.
GRADED_BADGES = {"EXAM", "CTF"}

PRIMARY_ORDER = ("worksheet", "mock-ctf", "exam", "ctf", "scrimmage", "readme")


def primary_kind(slug: str, course_slug: str | None = None) -> str | None:
    """The document a bare week URL should open, or None if the week has none."""
    week = next((w for w in list_weeks(course_slug) if w["slug"] == slug), None)
    return week["primary"] if week else None


def _title_of(path: str) -> str | None:
    """First `# heading` — the document's own title, not one we invent."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"^#\s+(.+)", line.strip())
            if m:
                return m.group(1).strip()
    return None


def _slides_path(unit_token: str, course_slug: str | None = None) -> str | None:
    """slides/weekNN.md, if it exists. Outside the week directory, so it gets its
    own containment check rather than reusing the lab-dir one."""
    c = course(course_slug)
    if c is None:
        return None
    if not re.fullmatch(r"\d{2}[a-z]?(?:-\d{2})?", unit_token or ""):
        return None      # never let a caller-supplied string reach a path join
    root = os.path.realpath(c["root"])
    # CONTENT_ROOT is `labs/` (or /content in the image); slides/ is its sibling
    # in a checkout and a sibling under /content in the image.
    for base in (os.path.dirname(root), root):
        p = os.path.realpath(os.path.join(
            base, SLIDES_DIR, f"{c.get('unit', 'week')}{unit_token}.md"))
        if (p == base or p.startswith(base + os.sep)) and os.path.isfile(p):
            return p
    return None


def read(slug: str, kind: str, course_slug: str | None = None) -> str | None:
    """Raw markdown for one week's public document, or None.

    Resolves and then re-checks containment: even though WEEK_RE already makes
    traversal impossible, the check costs nothing and survives someone later
    relaxing the pattern. With several courses configured the containment check
    matters more, not less — it is now per-course, so a week slug can never
    reach out of its own course's root.
    """
    c = course(course_slug)
    if c is None:
        return None
    if not unit_re(c.get("unit", "week")).match(slug or ""):
        return None
    base_root = c["root"]
    if kind == "slides":
        m = unit_re(course(course_slug).get("unit", "week")).match(slug)
        p = _slides_path(m.group(1), course_slug) if m else None
        if p is None:
            return None
        with open(p, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    if kind not in PUBLIC_FILES:
        return None
    root = os.path.realpath(base_root)
    path = os.path.realpath(os.path.join(root, slug, PUBLIC_FILES[kind]))
    if not (path == root or path.startswith(root + os.sep)):
        return None
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


# --- rendering -------------------------------------------------------------

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_ULI = re.compile(r"^\s*[-*+]\s+(.*)$")
_OLI = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_RULE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
# Matches the ESCAPED form: by the time block constructs are scanned, `>` is
# already `&gt;`. Escape-then-parse is the security property, so every pattern
# that touches < > & must be written against the escaped text, not the source.
_QUOTE = re.compile(r"^&gt;\s?(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")

# Only these schemes become clickable. `javascript:` and `data:` are the two that
# turn a link into script execution; anything unrecognised renders as plain text.
_SAFE_LINK = re.compile(r"^(https?://|mailto:|/|\#|\./|\.\./)", re.I)


def _inline(escaped: str) -> str:
    """Inline constructs, applied to text that is ALREADY html-escaped.

    Order matters: code spans first, so a payload inside backticks (which is how
    the worksheets present them) is never scanned for emphasis or links.
    """
    parts, last = [], 0
    for m in _INLINE_CODE.finditer(escaped):
        parts.append((_fmt(escaped[last:m.start()]), None))
        parts.append((m.group(1), "code"))
        last = m.end()
    parts.append((_fmt(escaped[last:]), None))
    return "".join(f"<code>{t}</code>" if k else t for t, k in parts)


def _fmt(s: str) -> str:
    s = _BOLD.sub(r"<strong>\1</strong>", s)
    s = _ITALIC.sub(r"<em>\1</em>", s)

    def link(m):
        text, href = m.group(1), m.group(2)
        # href is already escaped; unescape only to test the scheme, never to emit.
        if not _SAFE_LINK.match(html.unescape(href)):
            return f"{text} ({href})"      # shown, not clickable
        # Quotes MUST be escaped here even though the document-wide escape used
        # quote=False. This is the one place content lands inside an attribute,
        # and `[x](https://a"onmouseover="alert(1))` contains no whitespace, so it
        # satisfies the href pattern and would otherwise close the attribute and
        # open a live event handler. Found by testing, not by reading.
        safe = href.replace('"', "&quot;").replace("'", "&#x27;")
        return f'<a href="{safe}" rel="noopener noreferrer">{text}</a>'
    return _LINK.sub(link, s)


def render(md: str) -> str:
    """Markdown → HTML, with every byte escaped before anything is recognised."""
    lines = html.escape(md, quote=False).replace("&#x27;", "'").splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    list_stack: list[str] = []

    def close_lists():
        while list_stack:
            out.append(f"</{list_stack.pop()}>")

    while i < n:
        line = lines[i]

        # fenced code — emitted verbatim (already escaped), never re-scanned
        fence = re.match(r"^\s*```+\s*([A-Za-z0-9_+-]*)\s*$", line)
        if fence:
            close_lists()
            lang = fence.group(1)
            body, i = [], i + 1
            while i < n and not re.match(r"^\s*```+\s*$", lines[i]):
                body.append(lines[i])
                i += 1
            i += 1

            # ```sim … ``` embeds an interactive simulation. The body must match
            # a slug in the SIMS allowlist EXACTLY; anything else falls through
            # to a normal code block, so an unknown or hostile slug becomes
            # visible text and never an iframe.
            #
            # The frame is sandboxed with `allow-scripts` and deliberately
            # WITHOUT `allow-same-origin`: granting both together is equivalent
            # to no sandbox at all, because the framed page could then reach
            # into this origin and remove its own sandbox attribute. A
            # simulation needs no access to the parent document.
            if lang == "sim":
                slug = "\n".join(body).strip()
                if slug in SIMS:
                    out.append(
                        f'<figure class="sim">'
                        f'<iframe src="/sim/{slug}" title="{html.escape(SIMS[slug])}"'
                        f' sandbox="allow-scripts" loading="lazy"'
                        f' referrerpolicy="no-referrer"></iframe>'
                        f'<figcaption>{html.escape(SIMS[slug])} — '
                        f'<a href="/sim/{slug}">open full size</a></figcaption>'
                        f"</figure>")
                    continue

            cls = f' class="lang-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>" + "\n".join(body) + "</code></pre>")
            continue

        if not line.strip():
            close_lists()
            i += 1
            continue

        if _RULE.match(line):
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        h = _HEADING.match(line)
        if h:
            close_lists()
            lvl = min(len(h.group(1)) + 1, 6)   # shift down: page owns <h1>
            out.append(f"<h{lvl}>{_inline(h.group(2).strip())}</h{lvl}>")
            i += 1
            continue

        q = _QUOTE.match(line)
        if q:
            close_lists()
            body = []
            while i < n and _QUOTE.match(lines[i]):
                body.append(_QUOTE.match(lines[i]).group(1))
                i += 1
            out.append(f"<blockquote><p>{_inline(' '.join(body))}</p></blockquote>")
            continue

        # table: a header row followed by a |---|---| separator
        if "|" in line and i + 1 < n and _TABLE_SEP.match(lines[i + 1]):
            close_lists()
            def cells(s):
                return [c.strip() for c in s.strip().strip("|").split("|")]
            head = cells(line)
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(cells(lines[i]))
                i += 1
            th = "".join(f"<th>{_inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
                         for r in rows)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>")
            continue

        m = _ULI.match(line) or _OLI.match(line)
        if m:
            want = "ul" if _ULI.match(line) else "ol"
            if not list_stack or list_stack[-1] != want:
                close_lists()
                list_stack.append(want)
                out.append(f"<{want}>")
            out.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue

        close_lists()
        para = []
        while i < n and lines[i].strip() and not (
                _HEADING.match(lines[i]) or _ULI.match(lines[i]) or
                _OLI.match(lines[i]) or _RULE.match(lines[i]) or
                _QUOTE.match(lines[i]) or lines[i].lstrip().startswith("```")):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(para))}</p>")

    close_lists()
    return "\n".join(out)


def render_document(slug: str, kind: str, course_slug: str | None = None) -> dict | None:
    md = read(slug, kind, course_slug)
    if md is None:
        return None
    c = course(course_slug)
    if kind == "slides":
        _m = unit_re(c.get("unit", "week")).match(slug)
        title = (_title_of(_slides_path(_m.group(1), course_slug)) if _m else None) \
            or f"Slides — {slug}"
    else:
        title = _title_of(os.path.join(c["root"], slug, PUBLIC_FILES[kind])) or slug
    return {"slug": slug, "kind": kind, "title": title, "html": render(md),
            "course": c["slug"], "course_title": c["title"]}
