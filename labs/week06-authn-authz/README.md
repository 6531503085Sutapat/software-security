# Week 6 — Authentication, Sessions & Access Control

**OWASP 2025:** A01 Broken Access Control, A07 Authentication Failures · **CWE:** CWE-639 (IDOR), CWE-347 (improper signature verification), CWE-321 (weak hardcoded key)

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week06.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 6** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `docker compose up → http://localhost:8080`.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Distinguish authentication vs authorization.
- Exploit IDOR and broken access control.
- Identify JWT pitfalls (alg=none, weak secret) and fix token handling.

## 🗺️ Signature game — "IDOR Treasure Hunt + JWT Forgery"
Target: provided app with user objects and JWT auth (or Juice Shop).
1. **IDOR:** change an object/user id in a request to read another user's data.
2. **Privilege escalation:** use a forged token to become another regular user (e.g. impersonate "bob") — horizontal, not an admin-only function.
3. **JWT:** forge a token (none-alg or brute weak HMAC secret).
4. **Fix:** enforce a server-side ownership check on every object access (`order["owner"] != user`, not RBAC/ABAC), validate JWT alg + signature with a strong secret/key, and add deny-by-default checks.

## Run the local target
```bash
docker compose up        # vulnerable_app.py on http://localhost:8080  (the / page lists endpoints)
```
The fixed version is `solution_app.py`.

## Deliverable
Exploits + citation of the fix lines in `solution_app.py` (not student-authored fix code) + re-test results.

## References
- https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
