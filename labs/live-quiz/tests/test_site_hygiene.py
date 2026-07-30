"""Regression tests for the site-wide defects a full audit of the live site found.

Every test here corresponds to something that was ACTUALLY BROKEN in production,
not to a hypothetical. They are grouped by the failure they prevent, because the
value of each one is "this specific thing came back".

The expensive lesson behind the first group: an unreadable file (mode 0600 after
an rsync) 500'd a linked page for weeks. Git tracks only the exec bit, so no
diff, review or CI job could have shown it — only a request could.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import content as C          # noqa: E402
from app import app as flask_app   # noqa: E402


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def _course():
    return C.COURSES[0]["slug"]


# ── an unreadable file must 404, never 500 ─────────────────────────────────

def test_unreadable_document_is_treated_as_missing(tmp_path, monkeypatch):
    """A file mode a deploy got wrong must not hand a student a stack trace."""
    p = tmp_path / "locked.md"
    p.write_text("# Secret\n")
    p.chmod(0o000)
    try:
        assert C._slurp(str(p)) is None
        assert C._title_of(str(p)) is None
    finally:
        p.chmod(0o644)          # so pytest's tmp cleanup can remove it


def test_every_linked_document_kind_actually_renders():
    """The week14 README 500'd in production while every sibling served fine.

    Walks what the course index ADVERTISES and renders each one, so a document
    the site links but cannot produce fails here instead of in class.
    """
    broken = []
    for c in C.COURSES:
        for w in C.list_weeks(c["slug"]):
            for kind in w["available"]:
                if C.render_document(w["slug"], kind, c["slug"]) is None:
                    broken.append(f"{c['slug']}/{w['slug']}/{kind}")
    assert not broken, f"linked but unrenderable: {broken}"


# ── repo-relative markdown links ───────────────────────────────────────────

def test_no_rendered_document_emits_a_repo_relative_md_link():
    """`[x](../../SUBMISSION.md)` rendered verbatim resolves against /learn/...
    and 404s. It did, on 47 of 124 document pages."""
    offenders = []
    for c in C.COURSES:
        for w in C.list_weeks(c["slug"]):
            for kind in w["available"]:
                doc = C.render_document(w["slug"], kind, c["slug"])
                if doc and re.search(r'href="\.\.?/[^"]*\.md"', doc["html"]):
                    offenders.append(f"{c['slug']}/{w['slug']}/{kind}")
    assert not offenders, f"repo-relative .md links still linked: {offenders}"


def test_course_root_docs_resolve_and_serve(client):
    """SUBMISSION.md is linked from thirteen worksheets; it must be a real page."""
    slug = _course()
    names = [d["name"] for d in C.list_course_docs(slug)]
    assert "submission" in names
    r = client.get(f"/learn/{slug}/doc/submission")
    assert r.status_code == 200


def test_repo_relative_links_are_rewritten_not_merely_dropped():
    """The no-broken-links test above is satisfied by degrading a link to plain
    text, so on its own it would still pass if resolution stopped working. This
    asserts the useful half: the link a student needs is a LINK, and it goes
    somewhere that answers 200.
    """
    slug = _course()
    linked = set()
    for w in C.list_weeks(slug):
        doc = C.render_document(w["slug"], w["primary"], slug)
        linked.update(re.findall(r'href="(/learn/[^"]*/doc/[^"]*)"', doc["html"]))
    assert f"/learn/{slug}/doc/submission" in linked, (
        "no worksheet linked SUBMISSION.md as a resolved URL — either the "
        "fixture changed or link resolution regressed")
    # and every URL it produced is one this app will actually serve
    valid = {f"/learn/{slug}/doc/{d['name']}" for d in C.list_course_docs(slug)}
    assert linked <= valid, f"resolved to URLs that do not exist: {linked - valid}"


def test_week_to_week_relative_link_resolves_to_the_on_site_url():
    """`../week16-capstone/worksheet.md` must become /learn/<c>/week16-.../worksheet."""
    slug = _course()
    md = "[the capstone](../week16-capstone/worksheet.md)"
    root = os.path.realpath(C.course(slug)["root"])
    if not os.path.isdir(os.path.join(root, "week16-capstone")):
        pytest.skip("fixture course has no week16-capstone")
    out = C.render(md, ctx={"course": slug,
                            "dir": os.path.join(root, "week19-final-ctf-capstone")})
    assert f'href="/learn/{slug}/week16-capstone/worksheet"' in out


@pytest.mark.parametrize("name", ["../../../etc/passwd", "..", "", "nope",
                                  "instructor", "SUBMISSION.md"])
def test_course_doc_names_outside_the_allowlist_are_refused(client, name):
    assert C.render_course_doc(name, _course()) is None
    assert client.get(f"/learn/{_course()}/doc/{name}").status_code in (404, 308)


# ── legacy redirects must find the OWNING course ───────────────────────────

def test_legacy_week_url_redirects_into_the_course_that_owns_it(client):
    """Hardcoding COURSES[0] sent every cryptography legacy URL into
    software-security, where it 404'd — and a live crypto page emits six."""
    for c in C.COURSES:
        weeks = C.list_weeks(c["slug"])
        if not weeks:
            continue
        r = client.get(f"/learn/{weeks[0]['slug']}")
        assert r.status_code == 301
        assert f"/learn/{c['slug']}/" in r.headers["Location"], (
            f"{weeks[0]['slug']} belongs to {c['slug']} but went to "
            f"{r.headers['Location']}")
        assert client.get(r.headers["Location"]).status_code == 200


# ── headers every response needs ───────────────────────────────────────────

@pytest.mark.parametrize("path", ["/", "/login", "/register", "/quiz",
                                  "/submit", "/play", "/learn", "/sim"])
def test_every_public_page_carries_a_csp(client, path):
    """/ and /login — the page with the password form — had no CSP at all."""
    csp = client.get(path).headers.get("Content-Security-Policy", "")
    assert "default-src 'none'" in csp
    assert "unsafe-inline" not in csp


def test_learn_plane_keeps_its_stricter_script_free_policy(client):
    """The app-wide default must never widen the content plane, which renders
    worksheets containing live XSS payloads."""
    csp = client.get(f"/learn/{_course()}/").headers["Content-Security-Policy"]
    assert "script-src" not in csp
    assert "form-action 'none'" in csp


@pytest.mark.parametrize("path", ["/", "/login", "/learn"])
def test_head_mirrors_get(client, path):
    """HEAD /login answered 400: Flask dispatches HEAD to the GET view, and the
    `== "GET"` test dropped it into the POST branch's CSRF check."""
    assert client.head(path).status_code == client.get(path).status_code


def test_security_headers_are_not_duplicated(client):
    r = client.get("/learn")
    assert len(r.headers.get_all("X-Content-Type-Options")) == 1
    assert len(r.headers.get_all("Content-Security-Policy")) == 1


# ── discoverability ────────────────────────────────────────────────────────

def test_robots_and_sitemap_are_served(client):
    rb = client.get("/robots.txt")
    assert rb.status_code == 200 and "text/plain" in rb.headers["Content-Type"]
    assert b"Disallow: /login" in rb.data and b"Allow: /learn" in rb.data

    sm = client.get("/sitemap.xml")
    assert sm.status_code == 200 and "xml" in sm.headers["Content-Type"]
    body = sm.data.decode()
    assert f"/learn/{_course()}/" in body
    for w in C.list_weeks(_course()):
        assert f"/learn/{_course()}/{w['slug']}" in body


def test_pages_carry_description_and_card_metadata(client):
    """Lecturers share these URLs in LINE and Teams; they unfurled as bare
    links, and nothing gave a search engine a snippet to use."""
    html = client.get(f"/learn/{_course()}/").data.decode()
    for needle in ('name="description"', 'property="og:title"',
                   'property="og:image"', 'rel="canonical"', 'rel="icon"'):
        assert needle in html, f"missing {needle}"


def test_favicon_and_card_assets_exist(client):
    for path in ("/static/favicon.svg", "/static/favicon.png",
                 "/static/apple-touch-icon.png", "/static/og-card.png"):
        assert client.get(path).status_code == 200, path


def test_woff2_is_served_as_a_font(client):
    r = client.get("/static/fonts/InterVariable.woff2")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "font/woff2"
    assert "max-age" in r.headers.get("Cache-Control", "")


# ── the shell must not change shape between pages ──────────────────────────

@pytest.mark.parametrize("path", ["/", "/learn", "/quiz", "/submit",
                                  "/login", "/register"])
def test_every_shell_page_gets_the_course_switcher(client, path):
    """Four routes forgot to pass nav_courses, so the header grew and shrank as
    a student navigated. It comes from a context processor now."""
    html = client.get(path).data.decode()
    assert "lx-tier2" in html, f"{path} is not on the shared shell"
    if len(C.COURSES) > 1:
        assert "lx-tier1" in html, f"{path} lost the course switcher"


def test_reading_page_offers_a_way_onward(client):
    """A 6000px worksheet ended in the footer with no link to the next unit."""
    weeks = C.list_weeks(_course())
    if len(weeks) < 2:
        pytest.skip("needs at least two units")
    html = client.get(f"/learn/{_course()}/{weeks[0]['slug']}").data.decode()
    assert "lx-docnav" in html
    assert weeks[1]["slug"] in html


def test_slides_do_not_leak_frontmatter_or_speaker_notes():
    """Decks are Marp sources. The YAML block and the lecturer's own
    `<!-- Cold-call: ... -->` cues were rendering as student-visible text."""
    checked = 0
    for c in C.COURSES:
        for w in C.list_weeks(c["slug"]):
            if "slides" not in w["available"]:
                continue
            html = C.render_document(w["slug"], "slides", c["slug"])["html"]
            assert "marp: true" not in html, f"{w['slug']} leaks frontmatter"
            assert "&lt;!--" not in html and "<!--" not in html, \
                f"{w['slug']} leaks a speaker note"
            checked += 1
    assert checked, "no decks found — this test would pass vacuously"


# ── the site must not publish URLs a client can choose ─────────────────────

def test_self_referential_urls_ignore_a_forged_host_header(monkeypatch):
    """The sitemap's <loc>, the canonical link and og:url are absolute URLs the
    site publishes ABOUT ITSELF. Derived from request.url_root they come from
    the Host header, so a forged one makes this app hand a crawler, a
    link-preview fetcher or a shared cache URLs on someone else's domain.
    """
    import app as appmod
    monkeypatch.setattr(appmod, "SITE_ORIGIN", "https://learn.example")
    flask_app.config["TESTING"] = True
    c = flask_app.test_client()

    sm = c.get("/sitemap.xml", headers={"Host": "evil.example"}).data.decode()
    assert "evil.example" not in sm
    assert "<loc>https://learn.example/" in sm

    page = c.get("/learn", headers={"Host": "evil.example"}).data.decode()
    assert "evil.example" not in page
    assert 'rel="canonical" href="https://learn.example/learn"' in page

    rb = c.get("/robots.txt", headers={"Host": "evil.example"}).data.decode()
    assert "evil.example" not in rb
