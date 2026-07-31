"""Every page must be able to RUN under the CSP it is served with.

The defect that made this file necessary: the app-plane CSP (`script-src 'self'`
with no `'unsafe-inline'`) shipped while host.html still started the projector
screen from an inline `<script>initHost(…)</script>`. The browser dropped that
script. Nothing threw, nothing logged, no response changed — the projector simply
never joined its socket room, so the lobby stayed at 0 players and Start game
never enabled. It reached production and 353 tests stayed green, because every
one of them asserts on the RESPONSE and a blocked inline script is a policy
decision, not an error.

Same policy, same silence, four more casualties found alongside it:
  * set_form.html's parse preview (inline <script>)
  * console.html's delete confirmation (inline onsubmit=)
  * the answer colours on /host and /play (style="--o:var(--a-red)" from JS)
  * the response-distribution bar widths (style="--w:NN%")

So these tests do not check behaviour; they check that the MARKUP is compatible
with the POLICY. The two live in different files and nothing else connects them.

`'unsafe-inline'` would make all of this pass and is exactly the wrong fix: these
pages carry a password form and a teacher's authenticated session, on the same
origin as a content plane that renders course markdown containing real XSS
payloads. The markup comes to the policy, never the other way round.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import _APP_CSP, app as flask_app          # noqa: E402
from routes_content import CSP as LEARN_CSP, SIM_CSP  # noqa: E402

TEMPLATES = os.path.join(os.path.dirname(__file__), "..", "templates")
STATIC = os.path.join(os.path.dirname(__file__), "..", "static")

# Every policy this app serves. If one of them ever gains 'unsafe-inline' the
# corresponding assertions below stop applying — which is why the guard tests at
# the bottom pin the policies themselves.
POLICIES = {"app": _APP_CSP, "learn": LEARN_CSP, "sim": SIM_CSP}

_INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)
_STYLE_ATTR = re.compile(r"\sstyle\s*=\s*\"")
# Any `on*=` attribute, not a list of the ones we happened to think of. An
# enumerated list is a denylist, and this test exists to catch the CLASS: the
# first version named nine handlers and would have waved through ontoggle,
# onpaste, oncontextmenu, onpointerdown and every future one. HTML has no
# non-event attribute starting with "on", so the pattern needs no exceptions.
_EVENT_ATTR = re.compile(r"\son[a-z]+\s*=", re.I)


_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
_JS_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_JS_LINE_COMMENT = re.compile(r"^\s*//.*$", re.M)


def _templates():
    return sorted(f for f in os.listdir(TEMPLATES) if f.endswith(".html"))


def _read(name):
    """Template source with comments removed.

    Comments have to go before any of this is scanned: the notes explaining why
    a given inline construct was removed necessarily QUOTE that construct, so a
    naive scan flags the very documentation of the fix. Stripping them also
    makes the tests honest — a commented-out onsubmit= is not a violation.
    """
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
        src = fh.read()
    return _JINJA_COMMENT.sub("", _HTML_COMMENT.sub("", src))


def _read_script(name):
    """Ditto for our JavaScript."""
    with open(os.path.join(STATIC, name), encoding="utf-8") as fh:
        src = fh.read()
    return _JS_LINE_COMMENT.sub("", _JS_BLOCK_COMMENT.sub("", src))


# ── the policies themselves ────────────────────────────────────────────────

@pytest.mark.parametrize("name,policy", sorted(POLICIES.items()))
def test_no_policy_allows_inline(name, policy):
    """The assertions below are only meaningful while this holds."""
    assert "'unsafe-inline'" not in policy, name
    assert "'unsafe-hashes'" not in policy, name


# ── markup that the policy would silently drop ──────────────────────────────

@pytest.mark.parametrize("name", _templates())
def test_template_has_no_inline_script(name):
    bodies = [m.group(1).strip() for m in _INLINE_SCRIPT.finditer(_read(name))]
    assert not [b for b in bodies if b], (
        f"{name} has an inline <script> body. Under script-src 'self' the "
        f"browser drops it and the page silently loses that behaviour — move it "
        f"to static/ and pass any data in via a data- attribute.")


@pytest.mark.parametrize("name", _templates())
def test_template_has_no_inline_event_handler(name):
    found = [m.group(0).strip() for m in _EVENT_ATTR.finditer(_read(name))]
    assert not found, (
        f"{name} has inline event handlers {found}. They are inline script and "
        f"are dropped by script-src 'self' — attach the listener from static/.")


@pytest.mark.parametrize("name", _templates())
def test_template_has_no_inline_style_attribute(name):
    assert not _STYLE_ATTR.search(_read(name)), (
        f"{name} has a style=\"…\" attribute. style-src 'self' without "
        f"'unsafe-inline' makes it inert — measured, not assumed: an element "
        f"carrying style=\"position:absolute\" computed to `static`. Use a class.")


@pytest.mark.parametrize("name", ["host.js", "player.js", "set_form.js", "confirm.js"])
def test_script_emits_no_inline_style_attribute(name):
    """The subtler half: markup our own JS writes into innerHTML is still markup,
    and a style="" attribute in it is dropped exactly the same way. This is how
    the answer colours and the results bars died."""
    src = _read_script(name)
    assert 'style="' not in src, (
        f"{name} writes a style=\"…\" attribute into markup. Put the value on a "
        f"class, or set it through element.style, which style-src does not cover.")


# ── and the one that actually died ─────────────────────────────────────────

def test_host_screen_self_starts_without_inline_script():
    """host.html must hand the PIN to host.js through the DOM, and host.js must
    pick it up on its own. Both halves, because either alone is a dead screen."""
    html = _read("host.html")
    assert "data-pin=" in html
    assert re.search(r'<script src="/static/host\.js', html)
    with open(os.path.join(STATIC, "host.js"), encoding="utf-8") as fh:
        js = fh.read()
    assert "dataset.pin" in js
    assert "initHost(" in js.split("function initHost")[-1]


def test_rendered_host_page_carries_the_pin_and_no_inline_script():
    """End to end through the real template, since the two files above could
    each be right and still not agree on the attribute name."""
    flask_app.config["TESTING"] = True
    with flask_app.test_request_context("/host/create"):
        from flask import render_template
        html = render_template("host.html", created_pin="123456")
    assert 'data-pin="123456"' in html
    assert not [m.group(1).strip() for m in _INLINE_SCRIPT.finditer(html)
                if m.group(1).strip()]


def test_static_scripts_are_cache_busted():
    """A stale host.js is the same dead projector as a blocked one, and just as
    quiet. Every one of our scripts must carry the deploy's asset version."""
    for name in ("host.html", "player.html", "console.html", "set_form.html"):
        html = _read(name)
        for src in re.findall(r'<script src="(/static/[^"]+)"', html):
            assert "?v=" in src, f"{name} loads {src} with no cache-busting token"
