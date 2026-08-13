---
marp: true
theme: default
paginate: true
header: "Software Security · Week 17 · Review"
---

# Week 17
## Reflection & Review
Pre-Final · Weeks 10–16 (+ callbacks)

<!-- Same energy as W7 — game, not lecture. Frame: consolidate the modern stack + a few first-half callbacks; zero surprises for the final. ~2 min. -->

---

## Goal today

- Consolidate Weeks 10–16
- 🎯 **Security Jeopardy: Champions Edition**
- 🧪 Mock final CTF (same team mechanic as Week 19 — not the same coverage, see below)

<!-- Roadmap. Open with the cumulative review quiz (quiz2.md, 25 pts) per AGENDA, then the games. -->

---

## Map of the modern stack

| Wk | Topic | One-line |
|---|---|---|
| 10 | API security | check ownership; bind intended fields |
| 11 | Memory safety | fuzz, exploit, go memory-safe |
| 12 | Supply chain | SBOM, SLSA, sign & verify |
| 13 | Cloud/container | least privilege, no misconfig |
| 14 | AI/LLM | prompt injection; least-privilege tools |
| 15 | DevSecOps | automated gates; fail closed |
| 16 | Capstone | graded via the Wk 19 project demo, not a quiz question |

<!-- Cold-call one student per row for the one-liner (retrieval). Week 16 gets its own row (this slide's own subtitle says "Weeks 10-16") but flag it as differently-assessed — quiz2.md doesn't examine it, the W19 demo does. Add 2–3 first-half callbacks (injection, auth) since the final is cumulative. ~10 min. -->

---

## 🎯 Jeopardy: Champions Edition

Whole-course categories — modern stack + first-half callbacks:

| API | Memory | Supply Chain | Cloud | AI/LLM | DevSecOps |
|---|---|---|---|---|---|

<!-- Same run as W7 but whole-course. Seed questions from exams/item-bank.md (final pool). Weight the board toward DevSecOps and first-half callbacks, not more API questions — the mock CTF right after this covers API well; it has ZERO DevSecOps or Capstone coverage, and DevSecOps alone is 15 of the Wk18 written exam's 100 marks. Say this gap out loud to the room. Teams = Houses; Final-Jeopardy wager; points to the CTFd board. ~75 min. -->

---

## 🧪 Mock final CTF

**Not the same format as Week 19** — say so explicitly:

- 8 challenges here vs. **12** in W19; Web is 1 optional callback here vs. **5 separate W19 challenges (60/150 pts)**
- No DevSecOps or Capstone challenge in either the mock **or** the W19 CTF (both stop at Week 14) — that content is examined on the Week 18 written paper instead (15/100 pts)
- Mock has hints, ungraded; W19 has none, and is graded as half of the "Final" bucket — **W18 written + W19 CTF together are 25% of the course grade**, not W19 alone
- Team-based, leaderboard — the team mechanic and general flow ARE the same, just not the coverage

<!-- Correct the "same format" framing head-on — this course's own lesson-plan notes exist specifically because instructors kept saying "same as the final" and it isn't. Also correct a second, easy-to-repeat mistake: don't say "W19 is 25% of the final grade" — the 25% is the combined W18+W19 average; W19 alone is roughly half that. And don't imply DevSecOps/Capstone show up in W19 either — neither ctf.md nor the mock ever tests them, they're W18-written-only. Run mock-ctf.md / CTF pool, incl. a binary (toolbox container) + LLM challenge. Budget: 150 min per AGENDA (quiz 30 + Jeopardy 75 + break 15 + mock 150 + debrief 30 = 300 total) — not 90, that's a 60-min undercount that will visibly break the room's pacing. ~150 min. -->

---

## Exam scope reminder

- **Wk 18 written:** cumulative, emphasis on Weeks 10–15 (Week 16 capstone isn't separately examined)
- **Wk 19:** capstone CTF tournament + final project demos (**video walkthrough submitted before the session** + a short live Q&A — not a live demo slot)

<!-- State scope + logistics clearly — 10-15, not 10-16 (this was deliberately corrected in exam.md, don't reintroduce the old range here). W19's demo format changed too: pre-recorded + async grading, because the old live-demo format can't fit N≈80-120 students into a 90-min block. Remind teams the W19 demo is graded — bring a runnable project + the video. ~3 min. -->

---

# Final next week
Bring your project: threat model, SBOM, signed artifact, CI pipeline

<!-- Close: checklist of what to bring to W19; confirm project repos run. -->
