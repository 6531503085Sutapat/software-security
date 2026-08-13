# Week 10 — API Security

**OWASP API Security Top 10:** API1 BOLA · API3 broken object property level auth (mass assignment) · API4 unrestricted resource consumption

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week10.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 10** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `docker compose up → :8080 (insecure) / :8081 (secure)`.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Map the REST/GraphQL attack surface.
- Exploit BOLA and mass assignment.
- Add authorization, schema validation, and rate limiting.

## 🥷 Signature game — "crAPI Raid"
Target: **the local API below** — that's the graded lab (see rubric), not crAPI.
1. **BOLA:** read another user's orders by id with zero ownership check (`/api/users/<id>/orders`).
2. **Mass assignment:** smuggle `is_admin`/`balance` into `POST /api/users`.
3. **Resource consumption:** hammer `/api/login` — no rate limit (`401×5 → 429×2`).
4. **Fix:** read `solution_api.py` and cite the exact line that blocks each exploit (the object-level ownership check, the `ALLOWED_CREATE_FIELDS` allow-list, and the rate limiter).

> **Bonus (optional, ~20 min, ungraded): crAPI** — OWASP's own intentionally-vulnerable API, real GUID-based BOLA. Capture-only — **no fix step**.
```bash
git clone https://github.com/OWASP/crAPI.git
cd crAPI/deploy/docker && docker compose -f docker-compose.yml up -d
```

## Run the local target
```bash
docker compose up        # vulnerable_api.py on http://localhost:8080 ; solution_api.py on :8081
```
The secure API is `solution_api.py` (on :8081).

## Deliverable
Findings report (API Top 10 mapping) + fixes.

## References
- https://owasp.org/API-Security/  ·  https://github.com/OWASP/crAPI
