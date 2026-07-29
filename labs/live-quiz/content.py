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

# weekNN-slug only. Anchored, no dots, so `..` and absolute paths never match.
WEEK_RE = re.compile(r"^week\d{2}-[a-z0-9-]+$")
# The files a week may expose. An allowlist, not a pattern — a lab directory also
# holds vulnerable_app.py, solution_app.py and docker-compose.yml, and the
# solution is emphatically not student-facing.
PUBLIC_FILES = {"worksheet": "worksheet.md", "readme": "README.md"}


def list_weeks() -> list[dict]:
    """Every week directory that has something public to show, in order."""
    out = []
    for name in sorted(os.listdir(CONTENT_ROOT)):
        if not WEEK_RE.match(name):
            continue
        d = os.path.join(CONTENT_ROOT, name)
        if not os.path.isdir(d):
            continue
        available = [k for k, f in PUBLIC_FILES.items()
                     if os.path.isfile(os.path.join(d, f))]
        if not available:
            continue
        out.append({
            "slug": name,
            "number": int(name[4:6]),
            "title": _title_of(os.path.join(d, "worksheet.md")) or
                     _title_of(os.path.join(d, "README.md")) or
                     name[7:].replace("-", " ").title(),
            "available": available,
        })
    return out


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


def read(slug: str, kind: str) -> str | None:
    """Raw markdown for one week's public document, or None.

    Resolves and then re-checks containment: even though WEEK_RE already makes
    traversal impossible, the check costs nothing and survives someone later
    relaxing the pattern.
    """
    if not WEEK_RE.match(slug or "") or kind not in PUBLIC_FILES:
        return None
    root = os.path.realpath(CONTENT_ROOT)
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


def render_document(slug: str, kind: str) -> dict | None:
    md = read(slug, kind)
    if md is None:
        return None
    return {"slug": slug, "kind": kind,
            "title": _title_of(os.path.join(CONTENT_ROOT, slug, PUBLIC_FILES[kind]))
                     or slug,
            "html": render(md)}
