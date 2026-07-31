# Week 4 — Injection & Input Handling

**OWASP 2025:** A05 Injection · **CWE:** CWE-89 (SQLi), CWE-78 (command injection)

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (see Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week04.md`.
3. **Lab (180 min)** — play the game below, then complete **Worksheet 4** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `docker compose up` → http://localhost:8080.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · fixed code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How/where: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — add this week's finding + fix to your NoteVault report.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Exploit SQL and command injection.
- Explain why parameterized queries defeat injection.
- Apply input validation and output handling correctly.

## ⚔️ Signature game — "SQLi Boss Fight" (DVWA / Juice Shop)
```bash
# DVWA
docker run --rm -it -p 80:80 vulnerables/web-dvwa
# OR Juice Shop
docker run --rm -p 3000:3000 bkimminich/juice-shop
```
1. Extract data via SQLi (e.g. `' OR 1=1 -- `, UNION-based).
2. Achieve command injection on a vulnerable endpoint.
3. **Fix:** rewrite the endpoints with prepared statements / parameterized APIs and allow-list validation; re-test to confirm the payloads now fail.

## Run the local target
```bash
docker compose up        # vulnerable_app.py on http://localhost:8080  (the / page lists endpoints)
```
The fixed version is `solution_app.py`.

## Deliverable
PoC payloads + the patched code + proof the fix blocks them.

## References
- https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
