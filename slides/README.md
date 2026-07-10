# Slides

Lecture slides live here, one Marp deck per week (`week01.md` … `week19.md`).

## Per-week standard

- **Teaching weeks** (1–6, 10–15): ~**14–18 slides** each, fixed skeleton —
  Title → Agenda → Recap → Motivation/definitions → core content (what/how/example/impact) → OWASP/CWE map → Defenses → **signature game** + lab steps → Deliverable → Key takeaways → Questions.
- **Capstone week** (16): ~7–8 slides — studio day, not a lecture: WIP demos + peer review + practice CTF tournament.
- **Review weeks** (7, 17): ~7–8 slides — topic map + Jeopardy + mock CTF.
- **Exam weeks** (8, 9, 18, 19): ~5–6 slides — format, scope, rules/tips.
- Each teaching week also ships **1 lab** (the matching `labs/weekNN…/README.md`); Week 16's lab is the capstone/scrimmage materials.

> Status: skeletons exist for **all 19 weeks** and follow the standard. Weeks 1–3 have been expanded and synced with their updated labs (Elevation of Privilege + Secure by Design in Wk1; fuzzing + Bug/Fuzzing Race in Wk2; Capture the Hash in Wk3).

## Rendered decks (PowerPoint)

Presentable, **KOSEN-KMITL-branded** `.pptx` for all 19 weeks live in **[`pptx/`](pptx/)**
(generated from these `.md` files). See [pptx/README.md](pptx/README.md) to regenerate.

## Workflows — two options (pick one or mix)

## Option A — Markdown slides with Marp (version-controlled, recommended)

Write each lecture as a Markdown file and render to HTML/PDF/PPTX with [Marp](https://marp.app/).

```bash
# install once
npm i -g @marp-team/marp-cli

# render a deck
marp slides/week01.md -o slides/out/week01.html   # HTML
marp slides/week01.md --pdf                         # PDF
marp slides/week01.md --pptx                        # PowerPoint
```

A deck file starts with front-matter:

```markdown
---
marp: true
theme: default
paginate: true
---

# Week 1 — Security Mindset & Threat Modeling
Software Security · <Your Name>

---

## What does "secure" mean?
- CIA triad
- Trust boundaries
- Attack surface
```

Decks can be published automatically to **GitHub Pages** so students view them in the browser (no download). See `.github/workflows/` to add a Pages build step when ready.

## Option B — Google Slides (link out)

Author in Google Slides and link the deck per week below. Good for image-heavy decks and quick edits; not version-controlled.

| Week | Deck link |
|------|-----------|
| 1 | _add link_ |
| 2 | _add link_ |
| … | … |

> Decision pending — keep both rows until you choose. For a security course where OWASP content changes yearly, Marp keeps slides in sync with the labs.
