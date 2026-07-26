# Lesson Plan — Week 10: API Security

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 10 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week10-api-security` |
| **Slides** | `slides/week10.md` |
| **Standards** | OWASP API Security Top 10:2023 — **API1 BOLA** · **API3 Broken Object Property Level Authorization** (mass assignment) · **API4 Unrestricted Resource Consumption** |
| **CLOs addressed** | **CLO2** exploit · **CLO3** remediate · **CLO5** evaluate & communicate · **CLO6** evidence & ethics |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — Define **BOLA (API1:2023)**, state why it is the #1 API risk, and explain why a WAF cannot reliably stop it.
- K2 — Explain **mass assignment / broken object property level authorization (API3:2023)**, and contrast a blocklist against an allow-list of bindable fields.
- K3 — Explain why object-level authorization must be checked **per request, per object** (not once at login), and why a client-supplied header such as `X-User-Id` is not authentication.

**Skills (P)**
- P1 — Read another user's orders on `:8080` by changing the id in the URL, and explain from the response why no ownership check ran (API1).
- P2 — Smuggle `is_admin` and `balance` into user creation on `:8080` and confirm the response echoes the privileged fields (API3).
- P3 — Show that `/api/login` on `:8080` has no throttle by running the brute-force loop, and name the two impacts of an unthrottled endpoint (API4).
- P4 — Apply the correct fix to each of the three flaws using `solution_api.py`, and demonstrate the new behaviour on `:8081` (the 401→403→200 ladder, the forced `is_admin:false, balance:0`, and the `429`).

**Attitude (A)**
- A1 — Run exploits only against the lab targets supplied here (`vulnerable_api.py` on `:8080`) or a student's own OWASP crAPI instance, under [ETHICS.md](../../ETHICS.md).
- A2 — Submit identity-stamped evidence (`whoami` / login email / student ID + timestamp) that is their own work and can be reproduced live on request.
- A3 — Treat an AI-generated exploit or fix as something to be verified, not trusted.

## 2. Key ideas (the through-line)

APIs concentrate the web vulnerabilities from the first half of the course — IDOR, injection, broken
authentication — but strip away the browser that used to sit in front of them. There is no SameSite
cookie or CSP to lean on; the JSON endpoint *is* the raw attack surface, and every client is fully
attacker-controlled. **BOLA is IDOR at API scale:** the server authenticates *who* is calling but
never checks that the *object* being requested belongs to them, so incrementing an id in the URL
reads a stranger's data. **Mass assignment** is the same trust failure on the way in: the client
sends a field the UI never exposes (`is_admin`, `balance`) and the server binds it blindly. The
fixes are structural, not filters — an ownership check on *every* object access, an allow-list of
bindable fields with the server owning all sensitive ones, and a rate limit so an endpoint cannot be
hammered for free.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop running (Week 1 Lab 0); `curl` available on the command
  line; skim the recap — the slides bridge BOLA straight back to Week 6's IDOR / access-control
  material. This is the first teaching week after the midterm (W8 written, W9 CTF).
- **Instructor, before class:** pull the lab image ahead of the session (`docker compose pull` in the
  lab folder) — both services run `pip install --no-cache-dir flask` on first boot, so the container
  is not answering until the Flask "Running on …" line appears; give it ~30–60 s before curling. If
  you intend to demo the optional crAPI bonus, clone and pull it well ahead: the slides warn "crAPI is
  heavier (compose stack) — start the pull early".
- **Prerequisite concept:** what an object id / IDOR is (Week 6), and basic HTTP verbs with `curl`
  (`-X POST`, `-H`, `-d`).

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | ~10-min retrieval quiz; recap the web half (injection, XSS, auth/IDOR) and bridge IDOR → BOLA; today's agenda | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concepts | Why APIs are different: machine-to-machine, no browser safety net (no SameSite/CSP); object ids everywhere → IDOR/BOLA; clients can send any field → mass assignment; the OWASP API Security Top 10. Worked example: `GET /api/vehicle/1001/location` (yours) vs `1002` (someone else's) — BOLA (API1) | Lecture + live `curl` on the projector |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | Mass assignment (API3) — client sets `role`/`credit` the server blindly binds; API2 broken authentication, API4 unrestricted resource consumption (no rate limit), excessive data exposure. Real cases: a named API authorization breach (worksheet Part 4 asks students to research the Optus / T-Mobile BOLA/IDOR incidents), then the deck's "legitimate feature + missing authz → RCE" example (WordPress 404-template editor); short discussion "what would have stopped this?" | Lecture + short discussion |
| 1:35–1:55 | Defences | Object-level authorization on every request (ownership check); allow-list request schemas / bind only intended fields, return DTOs; rate limiting and quotas; schema validation (OpenAPI / GraphQL types) | Lecture with before/after code |
| 1:55–2:00 | Brief the game | **"crAPI Raid"** — exploit BOLA + mass assignment in the crAPI target, then Round 2 = add authorization checks, schema validation and rate limiting | Instruction |

**Checks for understanding during lecture**
- After the core concept: cold-call *"the server knows who I am — why does it still leak user 1002's data?"* (it never checks the object belongs to the caller).
- On the recap: cold-call *"what was IDOR?"* — then name BOLA as the same bug at API scale.
- At the end: *"what one check stops BOLA?"* (per-object ownership authorization on every request).

## 5. Laboratory — 180 min

Target: `docker compose up` in `labs/week10-api-security` → `http://localhost:8080` (INSECURE,
`vulnerable_api.py`) and `http://localhost:8081` (SECURE, `solution_api.py`). Seeded users:
`alice` (id 1), `bob` (id 2), `carol` (id 3, admin, balance 9999).

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:15 | **Task 0 — Onboarding** (15 min) | `curl http://localhost:8080/` and `curl http://localhost:8081/`; note which port is insecure; record the three seeded users | Both root responses + the user table |
| 0:15–0:50 | **Task 1 — BOLA: read another user's orders** (35 min) | `curl http://localhost:8080/api/users/3/orders` — receive carol's "Server rack" order with no auth; iterate the id (`/api/users/2/orders`); on `:8081` observe the ladder — `401` (no identity), `403` (`X-User-Id: 1` reading id 3), `200` (`X-User-Id: 1` reading id 1) | Leaked order JSON + the 401/403/200 transcript + mitigation note (API1) |
| 0:50–1:20 | **Task 2 — Mass assignment: self-promote to admin** (30 min) | `curl -X POST http://localhost:8080/api/users -H "Content-Type: application/json" -d '{"username":"mallory","password":"x","is_admin":true,"balance":1000000}'`; confirm the response echoes `"is_admin": true, "balance": 1000000`; repeat against `:8081` → forced to `is_admin:false, balance:0` | Both responses side by side + mitigation note (API3) |
| 1:20–1:45 | **Task 3 — Unrestricted resource consumption: brute-force login** (25 min) | Run the brute-force loop from `attack.md` against `:8080` (guesses incl. `alice123`) — all attempts processed; on `:8081` loop 7 times and confirm the 6th/7th return `429` | The `401 401 401 401 401 429 429` sequence + mitigation note (API4) |
| 1:45–2:05 | **Task 4 — Bonus: crAPI Raid** (optional, 20 min) | Against the student's own OWASP crAPI instance (`git clone https://github.com/OWASP/crAPI.git`), capture one BOLA or mass-assignment flag | Flag + endpoint + which API Top 10 id it maps to |
| 2:05–2:25 | **Task 5 — Defend / fix it** (20 min) | Read the three `# --- FIX …` blocks in `solution_api.py`; for each finding quote the line that defeats it — the per-object ownership check `caller["id"] != uid and not caller["is_admin"]`, the `ALLOWED_CREATE_FIELDS` binding, and the `RATE_LIMIT=5 / RATE_WINDOW=60` limiter — and give the new `:8081` status | Per API1/API3/API4: the exploit, the `solution_api.py` line that blocks it, the new HTTP status |
| 2:25–2:45 | **AI-resilient tasks** (20 min) | *Audit the AI* (critique an AI-written exploit/fix), *Explain-in-Plain-English*, *Prompt Problem* | Written answers (start in class, finish as homework) |
| 2:45–3:00 | **Micro-demo + submit** (15 min) | 2–3 rotating students give a 2–3 min "show your exploit/fix"; everyone submits | Worksheet PDF → Classroom; fixed code → GitHub |

**Formative checkpoints.** Tasks 1–3 (the three graded exploits) must be finished before the defend
task — a student still on Task 1 at 1:20 should carry Task 5 forward and return to the rest. If a
Task 1 request against `:8080` comes back `401` or `403`, the student is curling `:8081` (the secure
API) by mistake — check the port before debugging anything else. Task 4 is optional: if the room is
behind, skip it and treat the local `:8080` / `:8081` pair as the graded target; if a student breezes
through, the crAPI raid is their extension.

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 10, Parts 2–4 | Payloads, raw responses / HTTP status, screenshots, fix lines, written answers | K1–K3, P1–P4, A2 | Part of the 30% worksheet component |
| Weekly quiz (start of lecture) | Quiz score | K1–K2 | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation | P1–P4, A2 | Pass/flag for follow-up |
| Per-student flag | Flag value tied to the individual student | A2 | Integrity control, not a mark |

The worksheet's own rubric (100 pts) weights it as: Lecture questions (Part 2) 20 · Exploitation +
evidence (Tasks 1–4) 40 · Defense (Task 5, fixes mapped to `solution_api.py`) 25 · Reflection
(Part 4) 15. Per-student flags for this lab are seeded through the `FLAG_BOLA` / `FLAG_MASSASSIGN`
environment variables (see the instructor note in `docker-compose.yml`); flag values are never
printed here. Partial credit is available where a student explains the mechanism correctly but could
not land the exploit.

## 7. Materials

- Lab: `labs/week10-api-security/` — `vulnerable_api.py`, `solution_api.py`, `docker-compose.yml`, `attack.md`, `worksheet.md`, `README.md`
- Slides: `slides/week10.md`
- Optional signature-game target: OWASP crAPI — `git clone https://github.com/OWASP/crAPI.git`, then `cd crAPI/deploy/docker && docker compose -f docker-compose.yml up -d` (a heavier multi-container stack)
- Reference: OWASP API Security — https://owasp.org/API-Security/ · OWASP crAPI — https://github.com/OWASP/crAPI
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| Slow/failed pull of `python:3.12-slim` in class | Pre-pull before the session (`docker compose pull` in the lab folder); keep a USB copy (`docker save`/`docker load`). Both services `pip install flask` on first boot — wait for the Flask "Running on …" line (~30–60 s) before curling, or an early `curl` looks like a dead app |
| Port 8080 or 8081 already in use | Something else may already hold the published host port — during preparation for this plan, Docker itself was already publishing `8080` and `docker compose up` failed with `Bind for 0.0.0.0:8080 failed: port is already allocated`. Free the process or remap the published port in `docker-compose.yml` (e.g. `"8082:5000"`); the containers' internal ports stay `5000`/`5001` |
| Apple-Silicon platform mismatch | `python:3.12-slim` is multi-arch and pulls/runs natively on arm64 (verified for this plan) — no `--platform` flag needed for the local lab |
| Re-running the Task 3 `:8081` loop looks "broken" | The limiter is `RATE_LIMIT=5 / RATE_WINDOW=60`: a second run of the loop *inside the same 60-second window* returns `429` from the first attempt, not `401`×5 then `429`. Wait out the 60 s, or restart the `solution-api` container, before demonstrating the clean `401 401 401 401 401 429 429` sequence |
| Need to reset seeded state between attempts | `USERS`, `ORDERS` and the rate-limiter counters are all in-memory — `docker compose restart` (or `down`/`up`) clears the mallory account from Task 2 and the login attempts from Task 3 back to the seeded three users |
| Optional crAPI bonus needs network + a large pull | Task 4 clones and pulls a multi-container stack from the internet; if the room network is slow, skip it (it is optional) and grade against the local `:8080` / `:8081` pair. Pull crAPI ahead of class if you plan to demo it |
| Copy-paste of a classmate's evidence | Per-student flags (`FLAG_BOLA` / `FLAG_MASSASSIGN`, seeded via the instructor script referenced in `docker-compose.yml`) make submitted evidence attributable; viva spot-check the pair |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚
