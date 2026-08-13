---
marp: true
theme: default
paginate: true
header: "Software Security · Week 16"
---

# Week 16
## Capstone Studio & CTF Warm-up
Software Security · Nutthakorn Chalaemwongwan

<!-- Studio day, not a lecture. Frame: this is the dress rehearsal for the graded Week 19. Goal = every team leaves knowing exactly what to fix. ~2 min. -->

---

## Today

- Work-in-progress capstone demos
- Cross-team peer review
- 🏆 Practice CTF tournament (previews Week 19)

<!-- Roadmap. Time-box: WIP demos + peer review first half, practice CTF second half (300-min block). Keep demos strictly timed so everyone presents. -->

---

## Capstone — what good looks like

- Clear threat model → real vulnerabilities → working fixes
- SBOM + signed artifact
- Security CI pipeline that gates the build
- Story: attack → root cause → fix

<!-- Show the bar before demos so teams self-assess. This = the Week 19 graded rubric (project/README.md). Emphasize the narrative: attack → root cause → fix is what scores. ~4 min. -->

---

## The whole term, one lookup table

![The OWASP Top 10 (2025), each row paired with the week that taught it, the lab file that demonstrated it, and a representative CWE — A01 Broken Access Control (weeks 6, 10, deep coverage), A02 Security Misconfiguration (weeks 13, 2), A03 Software Supply Chain Failures (weeks 12, 15, deep coverage), A04 Cryptographic Failures (week 3), A05 Injection (weeks 4, 5, 2, deep coverage), A06 Insecure Design (week 1), A07 Authentication Failures (week 6), A08 Integrity Failures (week 12), A09 Logging Failures (week 15), A10 Mishandling Exceptional Conditions (week 15) — plus three categories beyond the web Top 10 still graded in the capstone CTF: API1 BOLA (week 10), memory-safety exploitation (week 11), and prompt injection (week 14).](img/owasp-map.svg)

<!-- The self-assessment tool for this session: which categories does YOUR capstone actually demonstrate, and which week's lab is the closest precedent to borrow from? The three "deep coverage" rows (A01/A03/A05) had the most lab hours — that's where a team's evidence will be strongest, and a useful nudge for teams still choosing what to build around. ~4 min. -->

---

## Demo format (today, ungraded)

- 10-min demo + 5-min Q&A
- Show one full attack→fix walkthrough — **live** unless your environment breaks, then a recorded fallback is fine (this is a rehearsal, not the Week 19 format)
- Get peer feedback before the graded Week 19

<!-- Run on a timer (15 min/team). "Ungraded" lowers stakes so they expose weak spots now. Prefer live — it's the better rehearsal — but don't hard-block a team whose sandbox breaks; the worksheet itself allows a recorded fallback for the attack segment, so don't contradict it on stage. -->

---

## Peer review rubric

- Is the threat model complete?
- Are findings CWE/OWASP-mapped & reproduced?
- Do the fixes actually close the bug?
- Is the pipeline real (fails on findings)?

<!-- Hand each team this as a checklist to score the team presenting (use scrimmage.md). Peer feedback in writing → the presenting team gets a punch-list. This is the main value of the session. -->

---

## 🏆 Practice CTF

- Mixed web / API / binary / supply-chain / cloud / LLM — 9 challenges, 6 categories
- **Boss challenge:** chains two bugs on **NoteVault** itself — your term project's own starter app
- Cross-team scrimmage, dry run for the Week 19 tournament

<!-- Run the scrimmage (scrimmage.md / item-bank CTF pool) in the exact W19 team format so the final has no surprises — don't drop "cloud" from the category list, it's a real category on the board (misconfig hunt, wk13). The Boss challenge is the one place this CTF ties back to the capstone theme — call it out, it's easy to miss. Leaderboard on CTFd. ~2.5 h. -->

---

## Before Week 19

- Fix gaps peers flagged
- Finalize SBOM + signing + pipeline
- Rehearse the demo

<!-- Send them off with a concrete punch-list (the peer feedback). Remind: W19 demo is graded + the final CTF tournament. -->

---

# Next: pre-final review (Week 17)
Then the final — Wk 18 written · Wk 19 capstone CTF

<!-- Bridge to W17 review. Confirm project repos are runnable before the final. -->
