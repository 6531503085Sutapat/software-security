"""tests/test_learn_routes.py — HTTP coverage for the /learn content plane.

WHY THIS FILE EXISTS. Before it, the suite had 244 tests and **not one of them
made a request to /learn**. Everything tested `content.py`'s functions directly,
so the route layer — URL shapes, 404s, redirects, and the CSP that keeps the
Week 5 XSS payload inert — was entirely unexercised. When /learn was reshaped for
multiple courses, all 244 still passed while every URL had changed underneath.

Two things are pinned here that would otherwise fail silently and in the wrong
direction:

  * **Legacy URLs keep working.** /learn/week04-injection is what existing
    worksheets, printed handouts and anything already given to a student use. It
    must redirect, not 404.
  * **Courses are isolated.** A week directory in course A must not be readable
    through course B's URL, even though both are just directories on disk.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import content as C  # noqa: E402
from app import app as flask_app  # noqa: E402


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def _a_week():
    weeks = C.list_weeks()
    assert weeks, "no weeks published — fixture assumption broken"
    return weeks[0]


def _default_course():
    return C.COURSES[0]["slug"]


# ── the single-course reality that ships on 15 Aug ─────────────────────────

def test_learn_index_serves_weeks_when_one_course(client):
    """With one course configured the front door shows weeks directly — no
    pointless "pick your course" click for a cohort that has exactly one."""
    r = client.get("/learn")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert _a_week()["slug"] in body


def test_course_scoped_index(client):
    r = client.get(f"/learn/{_default_course()}/")
    assert r.status_code == 200
    assert _a_week()["slug"] in r.get_data(as_text=True)


def test_course_scoped_document(client):
    w = _a_week()
    r = client.get(f"/learn/{_default_course()}/{w['slug']}")
    assert r.status_code == 200


def test_course_scoped_document_kind(client):
    w = _a_week()
    kind = w["available"][0]
    r = client.get(f"/learn/{_default_course()}/{w['slug']}/{kind}")
    assert r.status_code == 200


# ── the promise that nothing already handed to a student breaks ────────────

def test_legacy_week_url_redirects_not_404(client):
    """/learn/<week> is what every existing link uses. It must survive."""
    w = _a_week()
    r = client.get(f"/learn/{w['slug']}")
    assert r.status_code == 301, "legacy week URL must redirect, never 404"
    assert r.headers["Location"].endswith(f"/learn/{_default_course()}/{w['slug']}")


def test_legacy_week_kind_url_redirects(client):
    w = _a_week()
    kind = w["available"][0]
    r = client.get(f"/learn/{w['slug']}/{kind}")
    assert r.status_code == 301
    assert r.headers["Location"].endswith(
        f"/learn/{_default_course()}/{w['slug']}/{kind}")


def test_legacy_redirect_actually_lands_on_content(client):
    """Following the redirect must reach a real page — a redirect to a 404 is
    not a working link."""
    w = _a_week()
    r = client.get(f"/learn/{w['slug']}", follow_redirects=True)
    assert r.status_code == 200


# ── refusals ───────────────────────────────────────────────────────────────

def test_unknown_course_404(client):
    assert client.get("/learn/no-such-course/").status_code == 404


def test_unknown_week_under_valid_course_404(client):
    assert client.get(f"/learn/{_default_course()}/week99-nope").status_code == 404


def test_non_public_file_is_not_served(client):
    """solution_app.py and friends sit in the same directory as the worksheet.
    The allowlist is the only thing keeping them unreachable."""
    w = _a_week()
    for kind in ("solution_app.py", "solution", "vulnerable_app.py", "../README.md"):
        r = client.get(f"/learn/{_default_course()}/{w['slug']}/{kind}")
        assert r.status_code == 404, f"{kind} must not be served"


def test_traversal_in_course_segment_404(client):
    for bad in ("..", "../..", "%2e%2e"):
        assert client.get(f"/learn/{bad}/").status_code in (301, 308, 404)


# ── the header that keeps the Week 5 payload inert ─────────────────────────

def test_document_response_forbids_script(client):
    w = _a_week()
    r = client.get(f"/learn/{_default_course()}/{w['slug']}")
    csp = r.headers.get("Content-Security-Policy", "")
    assert csp, "content pages must carry a CSP"
    assert "script-src" not in csp, (
        "the content plane must have NO script-src at all — worksheets ship live "
        "XSS payloads and share an origin with the teacher's grading session")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"


def test_index_forbids_script(client):
    r = client.get("/learn")
    assert "script-src" not in r.headers.get("Content-Security-Policy", "")


# ── multi-course, which is the point of the change ─────────────────────────

@pytest.fixture
def two_courses(tmp_path, monkeypatch):
    """Two real course roots on disk, each with its own week directory."""
    a = tmp_path / "alpha"
    b = tmp_path / "beta"
    (a / "week01-alpha-topic").mkdir(parents=True)
    (b / "week01-beta-topic").mkdir(parents=True)
    (a / "week01-alpha-topic" / "worksheet.md").write_text("# Alpha week one\n")
    (b / "week01-beta-topic" / "worksheet.md").write_text("# Beta week one\n")
    monkeypatch.setenv("COURSES", json.dumps([
        {"slug": "alpha", "title": "Alpha Course", "root": str(a)},
        {"slug": "beta", "title": "Beta Course", "root": str(b),
         "arena_url": "https://ctf.example"},
    ]))
    importlib.reload(C)
    import routes_content
    importlib.reload(routes_content)
    yield
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C)
    importlib.reload(routes_content)


def test_two_courses_are_listed(two_courses):
    courses = C.list_courses()
    assert [c["slug"] for c in courses] == ["alpha", "beta"]
    assert courses[0]["week_count"] == 1


def test_each_course_sees_only_its_own_weeks(two_courses):
    assert [w["slug"] for w in C.list_weeks("alpha")] == ["week01-alpha-topic"]
    assert [w["slug"] for w in C.list_weeks("beta")] == ["week01-beta-topic"]


def test_a_week_is_not_readable_through_another_course(two_courses):
    """The containment check is per-course. Beta's week must be invisible under
    alpha even though both are just directories on the same filesystem."""
    assert C.read("week01-beta-topic", "worksheet", "alpha") is None
    assert C.read("week01-alpha-topic", "worksheet", "beta") is None
    assert C.read("week01-alpha-topic", "worksheet", "alpha") is not None


def test_course_slug_may_not_look_like_a_week(monkeypatch, tmp_path):
    """A course slug matching WEEK_RE would make /learn/<x> ambiguous between a
    course and a legacy week URL. Rejected at load rather than resolved by luck."""
    monkeypatch.setenv("COURSES", json.dumps(
        [{"slug": "week01-collide", "title": "X", "root": str(tmp_path)}]))
    with pytest.raises(ValueError, match="collides"):
        importlib.reload(C)
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C)


def test_duplicate_course_slug_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("COURSES", json.dumps([
        {"slug": "dup", "title": "A", "root": str(tmp_path)},
        {"slug": "dup", "title": "B", "root": str(tmp_path)},
    ]))
    with pytest.raises(ValueError, match="duplicate"):
        importlib.reload(C)
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C)


def test_missing_root_rejected_loudly(monkeypatch):
    """A typo'd path must fail at startup, not serve an empty course all term."""
    monkeypatch.setenv("COURSES", json.dumps(
        [{"slug": "ghost", "title": "Ghost", "root": "/nonexistent/path/xyz"}]))
    with pytest.raises(ValueError, match="does not exist"):
        importlib.reload(C)
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C)


# ── every week's MAIN link must open something ─────────────────────────────

def test_every_week_bare_url_opens_its_primary_document():
    """The bare week URL is the main link on the index; it must never 404.

    It used to hardcode `kind="worksheet"`, and six of nineteen weeks have no
    worksheet at all — both written exams, both midterm/final CTFs and both mock
    CTFs 404'd on their own link. Pinning EVERY week, not a sample, because the
    six that broke were exactly the ones a spot check of week 1 would miss.
    """
    from app import app as fa
    fa.config["TESTING"] = True
    client = fa.test_client()
    course = _default_course()
    broken = []
    for w in C.list_weeks():
        r = client.get(f"/learn/{course}/{w['slug']}")
        if r.status_code != 200:
            broken.append((w["slug"], r.status_code, w["available"]))
    assert not broken, f"weeks whose main link does not open: {broken}"


def test_primary_kind_prefers_the_real_document_over_the_readme():
    """A README exists for every week, so falling back to it would hide the
    breakage rather than fix it — the exam weeks must open the exam."""
    for slug, expected in (("week08-midterm-written", "exam"),
                           ("week07-review-midterm-prep", "mock-ctf"),
                           ("week19-final-ctf-capstone", "ctf"),
                           ("week01-threat-modeling", "worksheet")):
        if any(w["slug"] == slug for w in C.list_weeks()):
            assert C.primary_kind(slug) == expected, slug


def test_home_uses_each_course_own_unit_word(monkeypatch, tmp_path):
    """A course organised in LESSONS must not be described in weeks.

    The cloud course numbers its material Lesson 1-3, Lesson 7b — telling that
    student "10 weeks" makes them doubt they are in the right place.
    """
    wk = tmp_path / "wk"; ls = tmp_path / "ls"
    (wk / "week01-alpha").mkdir(parents=True)
    (ls / "lesson04-beta").mkdir(parents=True)
    (wk / "week01-alpha" / "worksheet.md").write_text("# Alpha\n")
    (ls / "lesson04-beta" / "worksheet.md").write_text("# Beta\n")
    monkeypatch.setenv("COURSES", json.dumps([
        {"slug": "wk", "title": "Weeky", "root": str(wk)},
        {"slug": "ls", "title": "Lessony", "root": str(ls),
         "unit": "lesson", "unit_label": "Lesson"},
    ]))
    importlib.reload(C)
    import app as appmod
    importlib.reload(appmod)
    body = appmod.app.test_client().get("/").get_data(as_text=True)
    assert "1 week" in body and "1 lesson" in body, body[:400]
    # and the lesson course's own unit token survives, irregularities included
    assert C.list_weeks("ls")[0]["number_label"] == "4"
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C); importlib.reload(appmod)


def test_irregular_lesson_numbers_do_not_crash_and_read_correctly(monkeypatch, tmp_path):
    """`lesson01-03-` spans two numbers and `lesson07b-` carries a letter. The
    old code did `int(name[4:6])` — a positional slice that assumed "week" plus
    exactly two digits, and raised on both."""
    r = tmp_path / "c"
    for d in ("lesson01-03-fundamentals", "lesson07b-monitoring", "lesson10-vpc"):
        (r / d).mkdir(parents=True)
        (r / d / "worksheet.md").write_text(f"# {d}\n")
    monkeypatch.setenv("COURSES", json.dumps(
        [{"slug": "cloud", "title": "Cloud", "root": str(r), "unit": "lesson"}]))
    importlib.reload(C)
    got = [(w["number"], w["number_label"]) for w in C.list_weeks("cloud")]
    assert got == [(1, "1–3"), (7, "7b"), (10, "10")], got
    monkeypatch.delenv("COURSES", raising=False)
    importlib.reload(C)


def test_legacy_url_does_not_redirect_for_a_non_public_kind(client):
    """The legacy handler must refuse the same things the canonical one refuses.

    It used to 301 any second segment, so /learn/week04-injection/solution
    answered with a redirect rather than a 404 — no content leaked, but it
    confirms the path shape to anyone probing for answer keys, and it made the
    two routes disagree about what exists.
    """
    w = _a_week()
    for kind in ("solution", "answers", "pptx", "solution_app.py"):
        r = client.get(f"/learn/{w['slug']}/{kind}")
        assert r.status_code == 404, (
            f"legacy /learn/<week>/{kind} returned {r.status_code}, must be 404")


def test_legacy_url_still_redirects_for_a_real_kind(client):
    """...without breaking the redirect that keeps printed links alive."""
    w = _a_week()
    kind = w["available"][0]
    assert client.get(f"/learn/{w['slug']}/{kind}").status_code == 301
