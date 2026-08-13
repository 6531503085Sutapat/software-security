---
marp: true
theme: default
paginate: true
header: "Software Security · Week 8 · Midterm"
---

# Week 8
## Midterm — Written Exam
Covers Weeks 1–6

<!-- Proctor deck. Before starting: confirm exam version (rotate from exams/item-bank.md each cohort), state time, closed/open-note rule, and integrity policy. Keep talking minimal once the clock starts. -->

---

## Format

- Duration: **120 minutes**
- **Closed book unless stated otherwise**
- 100 pts, 4 sections: A Concepts (30) · B Spot the Vuln (20) · **C Applied SQL Injection (30)** · D Design (20)

<!-- State it aloud exactly as printed on the paper — don't paraphrase the section split. Section C is not a "spot the vuln" bonus, it's a full quarter of the exam: students write real payloads and the reasoning behind each one, across auth-bypass, cross-DB fingerprinting, and a schema dump — per the answer key, C is graded on payload+reasoning only, zero fix credit (the fix skill is Section D's job, 10 of its 20 pts). Don't tell them to write a fix for C, it wastes their exam time. No phones/AI. -->

---

## What's assessed

- **A — Concepts (30):** CIA triad, STRIDE modeling, SAST/DAST/SCA/fuzzing, hashing vs. encryption vs. encoding, trust boundaries, least privilege / fail closed
- **B — Spot the Vuln (20):** find & name the flaw + CWE in a code snippet
- **C — Applied SQL Injection (30):** given a vulnerable endpoint, **write the payload and the reasoning** — auth bypass, cross-DB fingerprinting, schema/table dump. **No fix credit here** — that's Section D's job
- **D — Design (20):** SQLi defenses (incl. the fix Section C doesn't grade); design a secure password-reset flow

<!-- Section C is the one people revise least and lose the most on — it's not covered by a generic "spot the vuln" bullet, it's 30 of 100 points of writing real payloads. Show this breakdown, then move on — exam day, not teaching. -->

---

## Tips

- Read the code carefully before answering "spot the vuln"
- For Section C: **write the actual payload**, not a description of one — plus the one-line reasoning. No fix credit in C; don't spend exam time writing one there
- Name the **fix**, not just the bug, for B and D
- Map every finding to a CWE / OWASP category

<!-- The single biggest score-saver: for Section C specifically, a described payload ("I would inject a UNION") earns far less than the literal string. Say it once, then start the clock. -->

---

# Good luck
Week 9: hands-on CTF practical

<!-- Close: remind W9 is the hands-on CTF — VM/tools must be ready. Collect papers; grade with exams/week08-…-answers.md. -->
