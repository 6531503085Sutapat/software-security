---
marp: true
theme: default
paginate: true
header: "Software Security · Week 7 · Review"
---

# Week 7
## Reflection & Review
Pre-Midterm · Weeks 1–6

<!-- Energy up — review week is a GAME, not a lecture. Set the frame: today's job is "zero surprises on exam day." ~5h block = cumulative quiz + Jeopardy + mock CTF + cheat sheet. ~2 min. -->

---

## Goal today

- Consolidate Weeks 1–6
- 🎯 **Security Jeopardy** team quiz-show
- 🧪 **Mock CTF** in the midterm format
- Build your one-page cheat sheet

<!-- Roadmap, 1 min. Start the session with the cumulative review quiz (quiz1.md, 25 pts, 30 min) per the AGENDA, THEN the games. Tell them everything today mirrors the real exam. -->

---

## Map of the half

![A revision map of weeks 1 to 6: untrusted input crosses a trust boundary toward a sink, and every week places its control exactly at that crossing. Week 1 threat modeling: draw the DFD, run STRIDE at each crossing. Week 2 SDLC/tooling: Semgrep, Gitleaks, DAST and fuzzing catch what rides through commit/build/run unseen. Week 3 crypto: argon2id + AES-GCM with the key from the environment, not MD5/ECB with a fixed key. Week 4 injection: a parameterized query, no shell, an allow-list on the host. Week 5 XSS/CSRF: contextual encoding, a strict CSP, SameSite plus a real CSRF token. Week 6 auth: deny by default, a server-side owner check, and verifying the JWT's algorithm and signature.](img/revision-map.svg)

<!-- Fast recap — cold-call one student per row to give the one-liner from memory. Don't lecture; it's retrieval practice. Same unifying shape as Week 1's own trust-boundary concept: input crosses, a control sits at the crossing — the map makes that pattern visible across all 6 weeks at once, not just stated per week. ~10 min. -->

---

## 🎯 Security Jeopardy

Categories × point values:

| Threat Modeling | Tooling | Crypto | Injection | XSS | Auth |
|---|---|---|---|---|---|

<!-- Run by Houses/teams. Prep the board beforehand (6 categories × 5 values, questions seeded from the exam item bank). Rules: team picks, answers; wrong answer loses the points; end with a Final-Jeopardy wager. Keep it fast and loud. Award points into the CTFd/Houses board. ~60–75 min. -->

---

## 🧪 Mock CTF

Same format as Week 9, **6 challenges**, ~150 min:

- Injection (SQLi / command)
- XSS (**stored** only — reflected/DOM aren't in this mock)
- Auth / IDOR / JWT
- Crypto (crack a hash — the ECB oracle is a Week 3 *lab* task, not part of this mock)

> No surprises on exam day.

<!-- Run the EXACT Week 9 format (see mock-ctf.md) so the real CTF feels familiar — but the TIMING is 150 min per AGENDA.md and mock-ctf.md itself, not 90; get this wrong on stage and the room's schedule breaks by an hour. Circulate; offer hints that cost points. The point is calibration: they should leave knowing what they can/can't do. ~150 min. -->

---

## Common mistakes to avoid

- Confusing encoding vs encryption vs hashing
- "Validated input" ≠ safe → still parameterize
- Authentication without authorization
- Trusting client-side checks

<!-- Spend real time here — these are the top exam point-losers every cohort. Ask the room which they're shaky on and drill those. ~8 min. -->

---

## Deliverable

A **one-page cheat sheet** (your own) — may be allowed in the exam at instructor's discretion.

<!-- Making the cheat sheet IS the studying (generative learning). Decide + announce now whether it's allowed in the written exam. -->

---

# Midterm next week
Wk 8 = written · Wk 9 = hands-on CTF · covers Weeks 1–6

<!-- Logistics: state exam dates, what to bring, room/VM readiness for W9. Reassure: today's mock = the real thing. -->
