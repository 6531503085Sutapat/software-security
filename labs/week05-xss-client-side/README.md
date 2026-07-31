# Week 5 — Cross-Site Scripting (XSS) & Client-Side Risks

**OWASP 2025:** A05 Injection · **CWE:** CWE-79 (XSS), CWE-352 (CSRF)

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week05.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 5** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `docker compose up → http://localhost:8080`.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Distinguish reflected, stored, and DOM-based XSS.
- Understand the same-origin policy, cookies (SameSite), and CSP.
- Build a CSRF PoC and defend against it.

## ⛳ Signature game — "XSS Golf" (Juice Shop)
1. Land a **stored** XSS and a **DOM** XSS payload.
2. Steal/abuse a session via the XSS (sandbox only).
3. Build a CSRF page that performs a state-changing request.
4. **Fix:** add contextual output encoding, a strict Content-Security-Policy, `SameSite=Lax/Strict` cookies, and CSRF tokens; verify the attacks fail.

## Run the local target
```bash
docker compose up        # vulnerable_app.py on http://localhost:8080  (try /hello?name=, /comments)
```
The fixed version is `fixed_app.py`.

## Deliverable
Working payloads + CSP/encoding/CSRF fixes + screenshots of blocked attacks.

## References
- https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
