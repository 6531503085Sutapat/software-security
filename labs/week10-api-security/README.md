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
Take over accounts/vehicles in the crAPI target; each flag = points on the leaderboard.
```bash
git clone https://github.com/OWASP/crAPI.git
cd crAPI/deploy/docker && docker compose -f docker-compose.yml up -d
```
1. **BOLA:** access another user's vehicle/order by id.
2. **Mass assignment:** set a field you shouldn't (e.g. role/credit) via JSON body.
3. **Resource consumption:** trigger an unthrottled endpoint.
4. **Fix (round 2):** object-level auth checks, explicit allow-listed request schemas, and rate limiting.

## Run the local target
```bash
docker compose up        # vulnerable_api.py on http://localhost:8080 ; solution_api.py on :8081
```
The secure API is `solution_api.py` (on :8081).

## Deliverable
Findings report (API Top 10 mapping) + fixes.

## References
- https://owasp.org/API-Security/  ·  https://github.com/OWASP/crAPI
