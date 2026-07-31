# Quizzes

Two layers, both under the *Participation / quizzes* slice (10%):

## 1. Weekly quizzes (graded, low-stakes) — `weekly/`
A short **~10-min quiz every teaching week** (start of class) for retrieval practice.
- **6 questions** (5 MCQ auto-graded + 1 short answer).
- **Drop the lowest 1–2** scores across the term (reduces anxiety; rewards consistency).
- Files: `weekly/week01.md … weekly/week15.md` (teaching weeks 1–6, 10–15).

| Quiz | Covers |
|------|--------|
| `weekly/weekNN.md` | that week's lecture material |

**Integrity:** weekly quizzes are taken **in class, timed (~10 min), devices away / locked
browser** — that is the main anti-cheat. The Form shuffles questions/options and allows one
response per school account. **Question 6 (🔒) asks about your own lab work** (the payload you
used, the bug you found) — it is graded against your CTFd capture, so AI/copied answers that
don't match your own work score zero.

## 2. Cumulative review quizzes (pre-exam) — `quiz1.md`, `quiz2.md`
Bigger 25-pt review quizzes used **in the review weeks** to prep for the exams.
| Quiz | Covers | When |
|------|--------|------|
| [quiz1.md](quiz1.md) | Weeks 1–6 | Week 7 review (pre-midterm) |
| [quiz2.md](quiz2.md) | Weeks 10–15 | Week 17 review (pre-final) |

---

Answer keys are kept **out of the public repo** in the git-ignored `instructor/` directory
(`instructor/quizzes/` and `instructor/quizzes/weekly/`) — never distribute to students.
Exam keys live in `instructor/exams/`.

Students sit these on the platform: **`learn.zcr.ai/quiz`**, using the one-time code handed out in class.

> Worksheets (the longer, graded hands-on lab sheets) live with each lab in
> `labs/weekNN…/worksheet.md`. Template: [worksheets/TEMPLATE.md](../worksheets/TEMPLATE.md).
