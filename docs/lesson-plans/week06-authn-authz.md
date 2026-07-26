# Lesson Plan — Week 6: Authentication, Sessions & Access Control

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 6 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week06-authn-authz` |
| **Slides** | `slides/week06.md` |
| **Standards** | OWASP 2025 **A01 Broken Access Control** · **A07 Authentication Failures** · CWE-639 (IDOR), CWE-347 (improper signature verification), CWE-321 (weak hardcoded key) |
| **CLOs addressed** | **CLO2** exploit · **CLO3** remediate · **CLO5** evaluate & communicate · **CLO6** evidence & ethics |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — Distinguish *authentication* (who you are) from *authorisation* (what you may access), and identify which of the two is missing when an authenticated endpoint performs no ownership check.
- K2 — Explain IDOR (CWE-639): why exposing a direct object reference (`/api/orders/<oid>`) without a server-side ownership check lets any logged-in user read another user's object.
- K3 — Explain the two JWT forgery mechanisms — accepting `alg:none` (CWE-347, an *unsigned* token) and signing with a guessable secret (CWE-321) — and why pinning the algorithm, using a strong random secret and requiring `exp`/`aud` claims defeats both.

**Skills (P)**
- P1 — Log in as `alice` and use her token to read `bob`'s order via `/api/orders/2`, and explain why the missing ownership check is the root cause.
- P2 — Forge an unsigned `alg:none` token claiming `sub: bob` and have the vulnerable app accept it, with no secret needed.
- P3 — Forge a validly-signed HS256 token using the guessable secret `secret`.
- P4 — Document the full attack chain (forge a token → access any `oid`) that combines the flaws.
- P5 — Run `solution_app.py` and demonstrate that the IDOR now returns **403** and both forged tokens return **401**, naming the fix line for each.

**Attitude (A)**
- A1 — Forge tokens and access other users' objects only inside the sandbox (`http://localhost:8080`) or their own Juice Shop, under [ETHICS.md](../../ETHICS.md).
- A2 — Submit identity-stamped evidence (`whoami` / login email / student ID + timestamp) that is identifiably their own work, and be able to reproduce it live on request.
- A3 — Treat AI-generated authentication and access-control code as something to be verified, not trusted.

## 2. Key ideas (the through-line)

Authentication answers *"who are you?"*; authorisation answers *"what are you allowed to do with this
particular object?"*. Broken access control tops the OWASP list because these two are constantly
confused: an endpoint checks that a caller is logged in and then serves whatever object id they ask
for. A token proves identity — it says nothing about ownership, so authorisation must be re-checked
**server-side, deny-by-default, on every object access**. And the identity claim is only as
trustworthy as the verification behind it: if the verifier accepts `alg:none`, or signs with a
secret an attacker can guess, the "who you are" claim is itself forgeable. The fix is structural on
both fronts — an ownership check the client cannot skip, and signature verification with a pinned
algorithm, a strong secret and required claims — never a longer list of ids to trust.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop running (Week 1 Lab 0); skim the Week 5 recap. Have
  `curl` and `python3` with `pyjwt` available (or work entirely inside the lab container).
- **Instructor, before class:** pull `python:3.12-slim` ahead of the session so the room is not
  competing for it at once. Note that this lab does **not** ship a pre-built image — the compose
  file runs `pip install --no-cache-dir flask pyjwt` at container start, so the first
  `docker compose up` needs PyPI access; pre-warm that (see §8). If flags are being graded, seed the
  per-student `.env` first (`python3 ../../instructor/seed_flags.py env <STUDENT_ID> > .env`).
- **Prerequisite concept:** basic HTTP request/response and the `Authorization: Bearer` header; the
  three-part structure of a JWT (`header.payload.signature`).

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | ~10-min retrieval quiz on Week 5 (XSS & client-side risks); today's agenda | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concept | Authentication vs. authorisation; sessions and JWT structure (`header.payload.signature`); why authorisation must be re-checked server-side on every object access; walk `/api/orders/<oid>` in `vulnerable_app.py` and show `current_user()` being called but its result ignored (identity proven, ownership never decided) | Lecture + live coding on the projector |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | IDOR / broken access control (CWE-639); JWT forgery two ways — `alg:none` (CWE-347) and a weak/guessable secret (CWE-321); privilege escalation to `admin` via a forged `sub`; two brief real cases: the 2022 Optus breach (enumerable identifiers on a poorly-authorised API) and the Peloton API IDOR disclosure | Lecture + short discussion: "what single check would have stopped this?" |
| 1:35–1:55 | Defences | Deny-by-default ownership checks on every access (RBAC/ABAC); pin the JWT algorithm (no `none`) and verify the signature; strong random secret + key management; require `exp` and `aud` claims; where a framework helps and where it does not | Lecture with code-diff (`vulnerable_app.py` → `solution_app.py`) |
| 1:55–2:00 | Brief the game | "IDOR Treasure Hunt + JWT Forgery" — loot orders that aren't yours, mint a token you were never given, then defend the app so both fail | Instruction |

**Checks for understanding during lecture**
- After the core concept: cold-call *"in `/api/orders/<oid>`, which line proves the caller is authenticated, and which line is missing that would prove they are authorised?"*
- Before the break: one-minute paper — *"why does a valid signature not tell you whether this user owns this order?"*

## 5. Laboratory — 180 min

Target: `docker compose up` in `labs/week06-authn-authz` → `http://localhost:8080`
(vulnerable app; `solution_app.py` is the correct version). Service name `authz-lab`; the compose
file publishes host **8080 → container 5000**. Steps mirror `attack.md`.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:05 | **Task 0 — Onboarding (5 min)** | Stand the app up (`docker compose up`); log in as `alice` and capture her JWT into `$TOKEN`; confirm `/api/orders/1` returns her Laptop order | Screenshot of the token + order 1 |
| 0:05–0:35 | **Task 1 — IDOR Treasure Hunt (30 min) 🗺️** | Read bob's order with alice's token: `curl -s http://localhost:8080/api/orders/2 -H "Authorization: Bearer $TOKEN"` (vs. `/api/orders/1`, which is hers) | Both responses + screenshot of bob's `Phone` order + why the missing ownership check (CWE-639) is the root cause |
| 0:35–1:05 | **Task 2 — JWT Forgery via alg:none (30 min) 🔏** | Mint an unsigned token — `jwt.encode({"sub": "bob"}, key="", algorithm="none")` — and call `/api/orders/2` with it | Forged token + screenshot of the accepted response + explanation of the `none` flaw (CWE-347) |
| 1:05–1:35 | **Task 3 — JWT Forgery via weak secret (30 min) 🔏** | Sign a valid HS256 token with the guessable secret — `jwt.encode({"sub": "bob"}, "secret", algorithm="HS256")` — and replay it | Token + screenshot + 2–3 sentences on why secret strength + key management matter |
| 1:35–2:00 | **Task 4 — Privilege/identity escalation reasoning (25 min)** | Document the full attack chain (forge token → access any `oid`); optionally replay the requests through Burp Suite Repeater | Short chain diagram/paragraph + Burp (or `curl`) evidence |
| 2:00–2:30 | **Task 5 — Defend / fix it (30 min) 🛡️** | Stop the vulnerable container (`Ctrl-C`), run the fixed app — `docker compose run --rm --service-ports authz-lab bash -c "pip install --no-cache-dir flask pyjwt && python solution_app.py"` — get a fresh alice token, then re-fire Tasks 1–3 | Screenshots of the **403** and both **401**s + the fix line for each: ownership check (L64), algorithm pinned to HS256 (L50), strong random secret + required `aud`/`exp` (L10/40) |
| 2:30–2:50 | **AI-resilient tasks** | *Audit the AI* (critique an AI-written exploit or fix), *Explain-in-Plain-English*, *Prompt Problem* | Written answers (start in class, finish as homework) |
| 2:50–3:00 | **Micro-demo + submit** | 2–3 rotating students give a 2–3 min "show your exploit/fix"; everyone submits | Worksheet PDF → Classroom; fixed code → GitHub |

**Formative checkpoints.** Task 1 is the fastest "aha" and needs only `curl` plus the header — a
student who cannot make `/api/orders/2` leak has almost always mistyped the `Authorization: Bearer`
header or lost the `$TOKEN` variable; have them re-run Task 0. A student stuck on Task 2 for more
than ~10 minutes is usually hitting a PyJWT version that handles `alg:none` differently — check that
encoding uses `key=""` and that the app decodes with `options={"verify_signature": False},
algorithms=["none"]`. Tasks 1–3 must be landed by 2:00 for the defend task to fit; a student still
stuck there should switch to Task 5 and return afterwards.

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 6, Parts 1–4 | Tokens/payloads, screenshots, fix lines, written answers | K1–K3, P1–P5, A2 | Part of the 30% worksheet component |
| Weekly quiz (start of lecture) | Quiz score | K1–K3 | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation | P1–P5, A2 | Pass/flag for follow-up |
| Per-student flag | Flag value tied to the individual student | A2 | Integrity control, not a mark |

The worksheet's own rubric (100 pts) splits as: Part 2 lecture questions (20), Part 3 exploitation +
evidence for Tasks 1–4 (40), Part 3 defence for Task 5 with fixes proven and lines cited (25), Part
4 reflection (15). Partial credit is available where a student explains the mechanism correctly but
could not land the exploit.

## 7. Materials

- Lab: `labs/week06-authn-authz/` — `vulnerable_app.py`, `solution_app.py`, `docker-compose.yml`, `worksheet.md`, `attack.md`, `README.md`
  (**Instructor note:** `README.md` line 3 currently tags this lab `CWE-639 (IDOR), CWE-287`,
  which is stale — `worksheet.md`'s header and the `CWE` comments in `vulnerable_app.py`/
  `solution_app.py` all agree on CWE-639, CWE-347, CWE-321, which is what this plan's Standards
  row above uses. Trust the worksheet/code, not the README, until the README is corrected.)
- Slides: `slides/week06.md`
- Optional secondary target / proxy: OWASP Juice Shop (`bkimminich/juice-shop`, `-p 3000:3000`); Burp Suite (browser proxy to `127.0.0.1:8080` to intercept/replay)
- Reference: OWASP Authorization Cheat Sheet; OWASP JSON Web Token Cheat Sheet (linked in the lab `README.md`)
- Real cases for the deep-dive: 2022 Optus breach; Peloton API IDOR disclosure (from Worksheet 6, Part 4)
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| `pip install` at container start fails or is slow | `docker compose up` runs `pip install --no-cache-dir flask pyjwt` on start, so a room with no/slow internet cannot build the app; pre-pull `python:3.12-slim` and pre-warm a pip cache (or bake a local image) before class |
| Port 8080 already in use on a student's machine | The compose file publishes host `8080 → container 5000`; override the **left** side of the `ports` mapping in `docker-compose.yml`. The app listens on 5000 *inside* the container, so do not republish 5000 (macOS AirPlay squats on 5000, not 8080) |
| Task 5 "fix looks broken" | The `docker compose run …` command must install **both** `flask pyjwt`; dropping `pyjwt` makes `solution_app.py` crash on `import jwt` and reads as a broken fix |
| Unpinned `pyjwt` behaves differently | `flask` and `pyjwt` are installed unpinned at container start, so behaviour tracks whatever PyPI serves that day; a PyJWT major-version change can alter how `alg:none` encodes/decodes. If Task 2 misbehaves, check `pip show pyjwt` and pin the version for the class |
| Stale `$TOKEN` after switching to the fixed app | The fixed app's tokens carry `exp`/`aud`; an old vulnerable-app token replayed against `solution_app.py` yields 401 and can look like the exploit "still works" — have students re-run Task 0 to mint a fresh token after every restart |
| Juice Shop optional target won't start | `bkimminich/juice-shop` is a large image needing port 3000 free; pull it before class only if students will actually use it |
| Per-student flags not seeded | Flags come from `instructor/seed_flags.py` into `.env` (`FLAG_IDOR`, `FLAG_JWT`); without seeding the app falls back to placeholder flags that are not attributable — seed before class if flags are graded |
| A student finishes Tasks 1–3 early | Extension: forge a `sub: admin` token (via `alg:none` or the weak secret) to reach `/api/admin` and read `FLAG_JWT`; or write the regression test that proves the ownership check and algorithm pin stay fixed |
| A student cannot land any exploit | Pair them for Task 1 (IDOR, `curl`-only), then require they land Task 2 or 3 alone; mark the mechanism explanation, not the keystrokes |
| Copy-paste of a classmate's token/payload | Per-student flags make submitted evidence attributable; viva spot-check the pair |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚
