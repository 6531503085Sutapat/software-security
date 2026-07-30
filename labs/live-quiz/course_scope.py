"""course_scope.py — validate the course a graded artifact belongs to.

Courses live in the content registry ($COURSES / the curriculum monorepo), not in
this database, so there is no foreign key to lean on. This is the boundary check
that replaces one: a slug that is not a configured course never reaches storage.

Rejecting rather than defaulting is deliberate. Silently filing a quiz under the
first course would put it in front of the wrong cohort, and the teacher would see
it listed exactly where they expected — the failure would be invisible until a
student in the wrong class sat it.
"""
from __future__ import annotations


def valid_slugs() -> set[str]:
    import content as C
    return {c["slug"] for c in C.COURSES}


def check(course_slug: str | None) -> str:
    """Return the slug, or raise ValueError. `None` means the default course —
    the single-course case, and every caller that predates courses."""
    import content as C
    if course_slug is None:
        return C.COURSES[0]["slug"]
    if course_slug not in valid_slugs():
        raise ValueError(
            f"unknown course {course_slug!r} — configured: {sorted(valid_slugs())}")
    return course_slug
