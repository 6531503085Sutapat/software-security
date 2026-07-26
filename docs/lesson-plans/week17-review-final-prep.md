# Lesson Plan — Week 17: Reflection & Review (pre-Final)

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 17 · ⬚ |
| **Contact time** | 300 min (course specification §6 records 2 lecture + 3 laboratory hours; AGENDA.md runs the review weeks as one continuous block) |
| **Lab folder** | `labs/week17-review-final-prep` |
| **Slides** | `slides/week17.md` |
| **Type** | Review — **no new content**. Consolidates Weeks 10–16 (+ first-half callbacks) |
| **Standards consolidated** | OWASP **API Security Top 10:2023** — API1 BOLA · API3 BOPLA (mass assignment) · API4 Unrestricted Resource Consumption · OWASP **2025** — A02 Security Misconfiguration · A03 Software Supply Chain Failures · A08 Software or Data Integrity Failures · A09 Security Logging & Alerting Failures · A10 Mishandling of Exceptional Conditions · OWASP **Top 10 for LLM Applications (2025)** — LLM01, LLM02, LLM05, LLM06, LLM08, LLM10 · CWE-121, 787, 134, 242, 416, 193, 1104, 829, 1357, 1395, 321, 732, 16, 798, 250, 538, 269, 200 |
| **CLOs addressed** | **CLO1–CLO5** (course specification §6, week 17 row) |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — Recall, without notes, the one-line core of each of Weeks 10–16 and name the OWASP 2025 / API 2023 / LLM 2025 category and the CWE that goes with it.
- K2 — State which of the modern-stack topics is exercised by each mock-CTF challenge, and which two (DevSecOps and the capstone) the mock does *not* reach — they are carried by the Jeopardy board, Quiz 2 and the Week 18 written paper.
- K3 — Describe the shape of both final papers — what the Week 18 written exam asks for and what the Week 19 capstone CTF + project demo asks for — well enough to plan revision time and team roles against it.

**Skills (P)**
- P1 — Re-land each of the mock-CTF challenges under the Week 19 team format, with the hints used *after* an attempt rather than instead of one.
- P2 — For each challenge solved, give the one-line fix and name the OWASP/CWE id — the two things the Week 19 submission table also requires.
- P3 — Bring a runnable term project (threat model, SBOM, signed artifact, CI pipeline) to demo, and confirm every mock-CTF target comes up on the machine they will sit Week 19 on.
- P4 — Identify, honestly, which topics the team cannot yet do unaided, and say so in the debrief.

**Attitude (A)**
- A1 — Test only the sandbox targets supplied by the course, under [ETHICS.md](../../ETHICS.md) — this holds in a practice CTF exactly as it does in a graded one.
- A2 — Treat the mock as calibration rather than performance: an unsolved challenge found today is worth more than a solved one copied from a neighbour.
- A3 — Use the hints in `mock-ctf.md` after trying, not instead of trying — Week 19 offers none.

## 2. Key ideas (the through-line)

Weeks 10–16 look like six separate modern-stack topics and are really the same question the first half asked, now moved to where software actually ships: *where does untrusted data cross a boundary, and what does it get to control on the other side?* In Week 10 the boundary is an API object reference; in Week 11 it is the saved return address on a C stack; in Week 12 it is the name a package resolver shops for across two indexes; in Week 13 it is an IAM grant and a baked-in secret; in Week 14 it is the instruction/data line inside a prompt; in Week 15 the pipeline is asked to *find the crossing on the developer's behalf and fail closed when it does*. The review week's job is to make that single question retrievable under time pressure, because the final will present it in an unfamiliar wrapper and, unlike the midterm, it is cumulative. The second job is calibration: teams consistently over-rate what they can reproduce without the worksheet open, and the mock CTF is the cheapest place to discover that before it is worth 25% of the mark.

## 3. Prior knowledge and preparation

- **Students, before class:** review Weeks 10–16 — slides, their own submitted worksheets, and the OWASP/CWE lists (`labs/week17-review-final-prep/README.md`, step 1). Bring the machine they will sit Week 19 on, and a term project that runs.
- **Instructor, before class — the five mock-CTF targets:** the mock draws from `labs/week10-api-security`, `labs/week11-memory-safety-exploitation`, `labs/week12-supply-chain`, `labs/week13-cloud-container` and `labs/week14-ai-llm-security` (+ a web-half callback). These do **not** all start the same way — see §5.3. In particular, **build the toolbox image once the day before** (`docker build -t softsec-toolbox labs/toolbox`, `FROM silkeh/clang:19`) and pull `python:3.12-slim` and `aquasec/trivy:latest` on the room network, because the toolbox build is the long pole of the whole session (§10).
- **Instructor, before class — the Jeopardy board:** no board file ships in the repo. The `slides/week17.md` presenter note says to seed it from the final item bank (`instructor/exams/item-bank.md`) and prepare it beforehand — plus a Final-Jeopardy wager. The board itself is 6 categories (named on the slide's table header) × 5 point values, the same structure documented in `slides/week07.md`'s presenter note for the equivalent Week 7 Jeopardy round; week17.md's own note does not state the "× 5" figure.
- **Instructor, before class — the quiz:** Quiz 2 (`quizzes/quiz2.md`) runs closed book unless the instructor states otherwise — `quiz2.md` itself carries no book-condition text; that convention is stated only in `quiz1.md` (the Week 7 quiz, line 6: "Closed book unless your instructor says otherwise"). Decide and announce it today.
- **Instructor, before class — the exam-scope decision:** `labs/week18-final-written/README.md` records a live choice — *"cumulative-with-second-half-emphasis. Switch to second-half-only if preferred."* Students need to hear which one applies today; it is an instructor decision (⬚).
- **Prerequisite state:** the Weeks 10–14 labs have been completed and submitted, and the toolbox container has been built at least once. A team that never stood up the binary target or the Trivy scanners will lose the mock-CTF block to environment setup.

## 4. Consolidation plan — the seven weeks under review

| Wk | Topic | Signature exercise | Must be retrievable cold | Re-tested today by |
|---:|---|---|---|---|
| 10 | API security | "crAPI Raid" (BOLA + mass assignment) | BOLA = IDOR at API scale; a client-supplied `X-User-Id` header is not authentication; allow-list bindable fields; object-level authz is per-request, per-object | Mock-CTF **#1, #2**; Jeopardy (*API*); Quiz 2 Part A/B |
| 11 | Memory safety & exploitation | "Fuzzing Race → Pwn the Binary" | data vs code on the stack; ret2win via a saved-RA overwrite; the offset must be *derived*, not assumed; `printf(user)` vs `printf("%s", user)`; memory-safe languages are the durable fix | Mock-CTF **#3, #4**; Jeopardy (*Memory*); Quiz 2 Part A |
| 12 | Software supply-chain security | "Dependency Confusion Heist" | why a higher-versioned public look-alike wins; SBOM/SLSA/signing; an *unsigned* image must fail `cosign verify` | Mock-CTF **#5**; Jeopardy (*Supply Chain*); Quiz 2 Part A/C |
| 13 | Cloud & container security | "Misconfig Hunt" (CloudGoat-style) | `*:*` IAM violates least privilege; a secret in `ENV` is recoverable from a shipped image; unpinned `:latest`; distroless + non-root shrinks attack surface | Mock-CTF **#6**; Jeopardy (*Cloud*); Quiz 2 Part A/C |
| 14 | AI / LLM application security | "Gandalf Challenge" + tool poisoning | direct vs indirect prompt injection; a secret in the system prompt is the LLM02 anti-pattern; LLM output is untrusted → output-handling/XSS; least-privilege tools limit agency | Mock-CTF **#7**; Jeopardy (*AI/LLM*); Quiz 2 Part A/B |
| 15 | DevSecOps: putting it together | "Break the Build" (Red vs Blue) | fail **closed**, not open; a CI gate fails the build on HIGH/CRITICAL; SAST/SCA/secret-scanning — what each catches; SARIF to the Security tab | Jeopardy (*DevSecOps*); Quiz 2 Part A/C; **Week 18 written** |
| 16 | Capstone studio & CTF warm-up | Project WIP review + `scrimmage.md` | attack → root cause → fix, demoed live; threat model → SBOM → signed artifact → CI pipeline as one story | Project readiness check today; graded in **Week 19** |

**Coverage gap to name out loud.** The mock CTF's challenges are drawn from Weeks 10–14 (plus one web-half callback) only. **Weeks 15 (DevSecOps) and 16 (capstone) have no mock-CTF challenge.** DevSecOps is carried today by the Jeopardy *DevSecOps* category and Quiz 2, and it is examined in the **Week 18 written paper** — where the CI-gate question (A6, 5 pts) and the GitHub-Actions-pipeline design (D1, 10 pts) put **15 of the paper's 100 marks** on a week the mock never touches. A team that revises only from the mock CTF will walk into Week 18 having skipped it. The capstone is not a CTF topic at all — it is the graded project demo, due Week 19.

## 5. Session run-sheet — 300 min

Timings are AGENDA.md's review-week agenda (Weeks 7 & 17).

| Time | Block | What happens |
|---|---|---|
| 0:00–0:30 | **Cumulative review quiz** | Quiz 2 (`quizzes/quiz2.md`) — 25 pts, 30 min |
| 0:30–1:45 | **Security Jeopardy: Champions** | Team quiz-show across the modern stack + first-half callbacks |
| 1:45–2:00 | **Break** | Teams start their mock-CTF targets during the break — **including the toolbox build** |
| 2:00–4:30 | **Mock final CTF** | `labs/week17-review-final-prep/mock-ctf.md`, in the Week 19 team format |
| 4:30–5:00 | **Debrief** | Common mistakes (§6) + final logistics (§7) |

*(The presenter notes in `slides/week17.md` sketch a shorter shape — roughly 60–75 min of Jeopardy and ~90 min of mock CTF. AGENDA.md gives 75 min of Jeopardy and 150 min of mock CTF; `mock-ctf.md` itself says ~165 min. Follow AGENDA's 150-min block; if the mock overruns, the natural lever to drop is challenge 8, the optional web callback. This is documentation drift, in the same family as AGENDA.md's own "drift to resolve" note.)*

### 5.1 Cumulative review quiz — 0:00–0:30

| Field | Value |
|---|---|
| Instrument | `quizzes/quiz2.md` — "Quiz 2 — Modern Stack (Weeks 10–15)" |
| Weight | 25 pts, 30 min |
| Blueprint | Part A multiple choice 10 × 1 pt · Part B short answer 3 × 3 pts · Part C applied 2 × 3 pts |
| Covers | API security · Memory safety & exploitation · Supply chain · Cloud/container · AI/LLM · DevSecOps |
| Conditions | Closed book unless the instructor states otherwise — `quiz2.md` itself carries no book-condition text; the convention comes from `quiz1.md` (Week 7 quiz, line 6), so this is the instructor's call to make and announce today |
| Delivery | Google Form (SUBMISSION.md; Forms are built with `instructor/make_quiz_forms.gs`), individual, one attempt, shuffled, locked to the school account. `quiz2.md` prints as the paper fallback |
| Where it counts | The 10% weekly-quizzes / participation component |

Weeks 7 and 17 deliberately have **no** `quizzes/weekly/weekNN.md` 6-question quiz — the cumulative quiz *is* this week's retrieval practice (`quizzes/README.md`). Note that Quiz 2 covers Weeks 10–**15**; the Week 16 capstone carries no quiz content.

**Cohort rotation.** `quiz2.md` is a static file reused every cohort, which is a leak risk. Swap two or three Part A MCQs and/or the Part B/C alternates from the review-quiz item bank into a cohort copy, keeping the total at 25 pts (10 × 1 + 3 × 3 + 2 × 3).

### 5.2 Security Jeopardy: Champions — 0:30–1:45

- **Categories** — the six named in the lab README and `slides/week17.md`, one per modern-stack week under review:
  *API · Memory · Supply Chain · Cloud · AI/LLM · DevSecOps*, with first-half callbacks (injection, auth) folded into the squares since the final is cumulative.
- **Board** — 6 categories (named on the slide) × 5 point values, following the same structure documented in `slides/week07.md`'s presenter note for the equivalent Week 7 round, plus a **Final Jeopardy wager** at the end (`slides/week17.md` presenter note: seed from the item bank, prepare beforehand). Prepare it before the session; nothing ships in the repo.
- **Seed** — draw the questions from the final item bank (`instructor/exams/item-bank.md`), per the `slides/week17.md` note.
- **Teams** — run by Houses (non-graded engagement layer, per course specification §7).
- **Rules** — the team picks a square and answers; keep it fast.
- **Points** — award them into the CTFd / Houses board if the scoreboard is running; the Awards mechanism for non-flag games is documented in `instructor/CTFd-SETUP.md` §6.
- **Purpose** — this is the retrieval-practice slot for **DevSecOps (Week 15)**, which the mock CTF does not reach, and for the first-half callbacks. Weight the board towards those rather than filling it with API questions the mock already drills.

### 5.3 Mock final CTF — 2:00–4:30

**How it is run.** `labs/week17-review-final-prep/mock-ctf.md`: ~165 min (the file's figure; the AGENDA block is 150 min — see §5's drift note), **teams**, sandbox targets only, **hints included**, **ungraded (participation)**, no real exam flags. Same format as the Week 19 final CTF. For each challenge the team records their payload/command plus a one-line fix, then self-checks against the linked solution file. Warm-up (concepts): for any two challenges give the OWASP 2025 / API / LLM id + CWE, and one sentence on which control would have prevented it in CI.

| # | Challenge | Topic | Hint given in the file | Self-check against |
|---|---|---|---|---|
| 1 | Read another user's orders via the API | BOLA (W10) | id in the URL, no authz | `solution_api.py` |
| 2 | Create a user you shouldn't be able to | mass assignment (W10) | smuggle `is_admin` in the body | `solution_api.py` |
| 3 | Reach `win()` in the binary | stack overflow (W11) | offset 72 → overwrite RA; `objdump` for `&win` | `exploit_skeleton.py` |
| 4 | Make the binary crash with a fuzzer | fuzzing (W11) | `clang -fsanitize=address,fuzzer fuzz_harness.c` | `safe.rs` (the fix) |
| 5 | Find the vulnerable dependency / unsigned image | supply chain (W12) | `trivy fs` / `cosign verify` | `sign.sh`, `sca_scan.sh` |
| 6 | Spot the IAM/secret/root misconfig | cloud (W13) | `trivy config`; read `Dockerfile.insecure` | `harden.md` |
| 7 | Make the chatbot leak its secret | prompt injection (W14) | override the system instruction | `guarded_chatbot.py` |
| 8 | Callback: any one web bug from W4–6 | web | reuse a midterm technique | week04–06 solutions |

**Infrastructure needed.** Unlike Week 7's four `docker compose up` targets, these five start five different ways — get this right or the block is lost to setup.

| Target | Start | Published host port | Installed / built at start | Also needed |
|---|---|---|---|---|
| `labs/week10-api-security` | `docker compose up` | **`8080:5000`** insecure, `8081:5001` secure | `flask` (pip at container start) | a browser or `curl`; seeded users alice(1) bob(2) carol(3, admin) |
| `labs/week11-memory-safety-exploitation` | `docker build -t softsec-toolbox labs/toolbox`, then `docker run -it --rm --cap-add=SYS_PTRACE --security-opt seccomp=unconfined -v "$PWD/labs/week11-memory-safety-exploitation":/work -w /work softsec-toolbox`; inside: `make vuln`, `clang -g -fsanitize=address,fuzzer fuzz_harness.c -o fuzz` | none (runs in the toolbox) | the `softsec-toolbox` image (`FROM silkeh/clang:19`) | `objdump`/`gdb` (in the image); `setarch` to disable ASLR; **verify the offset — do not trust 72 blindly** |
| `labs/week12-supply-chain` | `bash sca_scan.sh` (trivy fs + pip-audit), then `docker build -t week12-supplychain:lab .` and `bash sign.sh week12-supplychain:lab` | none | pulls `aquasec/trivy` / cosign in the scripts | network for `cosign verify`; signing itself needs an OIDC browser flow + registry push (not needed for the mock's verify/scan) |
| `labs/week13-cloud-container` | `bash scan.sh` (`trivy config` over the Dockerfiles) | none | pulls `aquasec/trivy:latest` | network to pull Trivy; `Dockerfile.insecure`, `harden.md`, IAM JSON reviewed manually |
| `labs/week14-ai-llm-security` | `docker compose up` | `6000:6000` insecure, `6001:6001` guarded | `flask` (pip at container start) | a browser or `curl`; **fully offline** — a local rule-based mock, no API key, no real model |
| callback `labs/week04-06…` | `docker compose up` in the chosen week | `8080:5000` each | `flask` (W4/5), `flask`+`pyjwt` (W6) | a browser or `curl` |

No per-student flag seeding is required for the mock: the Week 10 and Week 14 targets fall back to public placeholder flag values when the `FLAG_*` environment variables are unset (`labs/week10-api-security/vulnerable_api.py` L15–16, `labs/week14-ai-llm-security/vulnerable_chatbot.py` L20). Flag seeding (`instructor/seed_flags.py env <STUDENT_ID> > .env`) is not part of today.

**How scoring works.** The mock CTF is **ungraded** — `mock-ctf.md` marks it participation, with no flags and no point values, and the team's feedback loop is the self-check column above. The repo defines no scoring scheme for it: any points beyond participation are ⬚ (instructor's choice). If the CTFd scoreboard is running, the documented way to put the session on the same leaderboard as the weekly games is CTFd **Awards** (`instructor/CTFd-SETUP.md` §6: 1st/2nd/3rd = 300/200/100, first-blood +100, most creative +50). Do not describe CTFd's dynamic scoring or point-costing hints as the mock's scoring model — those apply to the flag-bearing challenge set, not to this session.

**Formative checkpoints.** Challenges 1 and 2 are pure `curl` against the Week 10 API and are the two shortest paths — every team should have landed both by 3:00; a team still stuck is usually re-typing the request rather than reading the ownership check missing in `vulnerable_api.py`. The binary work (challenges 3 and 4) is the long pole: it needs the toolbox image built and the offset *derived* (not the hint's 72 assumed) — start it first, not last. A team that has solved everything early should attempt the **indirect-injection / output-XSS** work (Week 14 worksheet Tasks 2–3), because Week 19 has such a challenge and the mock does not (§7.3).

### 5.4 Debrief — 4:30–5:00

Run §6's misconception list against the room ("hands up who is shaky on this one") and drill the two or three that draw the most hands, then give the Week 18/19 logistics from §7. Close by confirming every team has a term project that runs and every mock-CTF target came up on their own machine.

## 6. Common misconceptions to re-test

Every entry below is drawn from a specific correction carried in the Weeks 10–15 worksheets or code — each exists because the naive version is wrong under reproduction.

| # | Misconception | Where it comes from | How to re-test it today |
|---|---|---|---|
| 1 | A client-supplied `X-User-Id` header is authentication | Week 10 worksheet Q4 — `current_user()` trusts the header; a caller sets it to anything | Mock-CTF #1, then "which line makes this not authentication, and what replaces it?" |
| 2 | BOLA and mass assignment are the same bug | Week 10 lecture Q1/Q2 — one is object-level *read* authz (API1), the other is binding fields the client shouldn't set (API3) | Jeopardy *API*: give both a one-line fix (ownership check vs allow-list) |
| 3 | "A WAF will stop BOLA" | Week 10 worksheet Q1 — the request is well-formed; only per-object authz catches it | Ask why the `:8081` ownership check succeeds where a filter cannot |
| 4 | The ret2win offset is always 72 | Week 11 worksheet Task 2 step 2 and `exploit_skeleton.py` L39/L52 — "do **not** trust 72 blindly"; derive it with a cyclic pattern | Make them show the `cyclic_find`/RIP evidence, not just type 72 |
| 5 | On the hardened build it is the stack canary that fires | Week 11 worksheet Task 3 and `Makefile` L54 — on this build FORTIFY_SOURCE's `__strcpy_chk` catches the overflow **before** the canary's epilogue check runs (`*** buffer overflow detected ***: terminated`) | "Which mitigation actually fired, and why not the canary?" |
| 6 | `printf(user_input)` is fine | Week 11 lecture Q3 — CWE-134; `%n` can write memory, `printf("%s", user_input)` is the fix | Jeopardy *Memory*: "what does `%n` buy the attacker?" |
| 7 | An SBOM + signature would have caught the XZ backdoor | Week 12 worksheet Part 4 Q2 — signing proves provenance/integrity, but a *signed, malicious* upstream still verifies; the honest answer names what signing does and does not cover | Ask what signing proves and what it cannot, using the XZ case |
| 8 | An unsigned image "passes if nothing complains" | Week 12 worksheet Task 3 — the negative test `cosign verify python:3.9-slim` **must** fail with "no matching signatures" | Have them run the negative test and read the failure as the pass condition |
| 9 | Trivy will flag the over-permissive IAM policy | Week 13 worksheet Task 2 and `scan.sh` L18–21 — `trivy config` does **not** parse standalone IAM JSON; only 3 of 6 `Dockerfile.insecure` defects map to Trivy rules (`DS-0001/0002/0031`), the rest are manual review | Mock-CTF #6: "the scanner is clean on the IAM file — is the policy safe?" |
| 10 | "Tell the model never to reveal the secret" is a control | Week 14 worksheet Q2 — a secret in `SYSTEM_PROMPT` is the LLM02 anti-pattern; the real fix is keeping it out of the prompt, not instructing the model | Mock-CTF #7, then argue keep-it-out vs filter (defence in depth) |
| 11 | LLM output is safe to render | Week 14 worksheet Q3/Task 2 — LLM05; `mock_llm()` output flows unescaped into `PAGE.format(reply=reply)` → reflected XSS | Show `<script>alert(1)</script>` firing, then the `escape()` guard |
| 12 | Failing "safe" means logging the error and continuing | Week 15 — the insecure service on `:8090` `/admin` fails **open**; the secure service on `:8091` fails **closed** + logs; a CI gate must *fail the build* on HIGH/CRITICAL, not log-and-continue | Jeopardy *DevSecOps*: "fail open vs fail closed — which line is the difference?" |

Two operational stumbles worth pre-empting in the same breath, because they cost minutes rather than marks: the binary target must be built and run **inside the toolbox container** with `--cap-add=SYS_PTRACE --security-opt seccomp=unconfined` (Week 11 setup) — `make vuln` on a macOS host may fail at the link step (`Makefile` L14–16) — and `cosign verify` in challenge 5 needs the network to reach the registry and transparency log.

## 7. Exam preparation

### 7.1 Week 18 — written, 150 min, 100 pts

Cumulative, emphasis on Weeks 10–16. Closed book unless stated otherwise. Blueprint, from `labs/week18-final-written/exam.md`:

| Section | Focus | Marks |
|---|---|---|
| A | Modern-stack concepts | 30 (6 × 5) |
| B | Spot the Vulnerability — name it (+ OWASP/CWE) and give the fix | 20 (4 × 5) |
| C | Applied — BOLA fix, image scan/SBOM/sign/verify, RAG+tool risks | 30 (3 × 10) |
| D | Design & DevSecOps — GitHub Actions pipeline; a supply-chain incident | 20 (2 × 10) |

**It will ask** for the six modern-stack concept areas in Section A (BOLA vs mass assignment; memory-safety mitigations; SBOM/SLSA/signing; security misconfiguration; direct vs indirect prompt injection; the CI security gate), four "spot the vuln" snippets in Section B (BOLA endpoint, insecure Dockerfile, unescaped LLM output, unchecked `strcpy`), three applied designs in Section C, and two design/DevSecOps essays in Section D (a GitHub Actions security pipeline; a notable supply-chain incident such as XZ Utils, SolarWinds or Log4Shell). For code answers it wants the **exact** payload or fix written out.

**It will not ask** for anything outside those four sections. It is cumulative with second-half emphasis — but confirm the scope decision today: `labs/week18-final-written/README.md` records the choice as *cumulative-with-second-half-emphasis, or second-half-only if preferred* (⬚, instructor's call). Two parallel forms exist (A/B) for make-up sittings (course specification §9).

**DevSecOps is the block the mock does not touch.** Section A6 (5 pts) and D1 (10 pts) both sit on Week 15, which has no mock-CTF challenge — that is up to **15 of the paper's 100 marks** on material a team drilling only from the mock never met. Cover it in the Jeopardy *DevSecOps* category and Quiz 2 Part C (Q15, "Break the Build"), and say plainly in the debrief that pipeline gate design and fail-closed logging are examinable.

### 7.2 Week 19 — capstone CTF + project demos, 240 min

Team-based. From `labs/week19-final-ctf-capstone/ctf.md` and README, and AGENDA.md:

- **Capstone CTF tournament** (0:00–2:30, 150 min): **150 pts across 12 challenges**, team-based, leaderboard, sandbox targets only, targets started by the instructor. For each challenge the submission table wants three things — the **flag** (or noted proof), the **payload or command**, and a **one-line mitigation**. Difficulty rises with points; first-blood bonus is at the instructor's discretion.
- **Graded final project demos** (2:30–4:00, 90 min): each team presents its secured build end-to-end — threat model → vulnerabilities → remediation → SBOM + signed artifact → CI pipeline — as a 10-minute demo + 5-minute Q&A, scored by rubric (`project/README.md`, `project/REPORT-TEMPLATE.md`).

Flags in Week 19 are submitted via the CTF Form / Classroom (SUBMISSION.md). The final (W18 written + W19 CTF) is worth **25%** of the course mark (course specification §4); the term project is a separate 15%, with each member's mark scaled by peer contribution.

### 7.3 What today's mock does *not* cover — say this explicitly

`mock-ctf.md` promises the "exact format of Week 19", and the mock's challenges do map onto the Week 19 set. Real differences remain, and teams should hear all of them today:

| | Mock CTF (today) | Week 19 |
|---|---|---|
| Challenges | 8 | **12** |
| First-half web | one optional callback (challenge 8) | **five separate challenges** — Boolean Bypass 10 · Shell Out 15 · Persistent Pop 10 · Not Your Object 10 · Token Smith 15 = **60 of 150 pts** |
| API | split into two (#1 BOLA, #2 mass assignment) | **combined** into one — #6 "Raid the API" (15 pts) |
| Indirect injection / output XSS | **no counterpart** (mock #7 is *direct* injection only) | #12 "Indirect Hit" (10 pts), drawn from Week 14 worksheet Tasks 2–3 |
| Hints | included in the file | none |
| Stakes | ungraded, participation | team-scored, part of the 25% final |

The two Week 19 challenges with **no mock counterpart** — the 60-point block of first-half web and the indirect-injection challenge — are exactly where a team that revised only from the mock is exposed. Anyone who reaches the end of the mock early should spend the remaining time re-landing a web-half exploit end-to-end and doing the Week 14 indirect-injection thought-experiment rather than polishing a solved challenge.

### 7.4 Logistics to read out in the debrief

`slides/week17.md`'s closing note asks for the final logistics to be stated in this session, and none of them are recorded in the repository:

- Week 18 (written) — date / time / room: ⬚
- Week 19 (CTF + demos) — date / time / room: ⬚
- Exam-scope decision (cumulative vs second-half-only) and whether Quiz 2 was closed book: ⬚ (announce today)
- Week 19 machine readiness — teams run the CTF and demo on the machine they used today; any target (especially the toolbox binary) that did not come up in the mock must be fixed before Week 19, not on the day.

### 7.5 Deliverable — a runnable term project (not a cheat sheet)

Unlike the pre-midterm review, Week 17's stated prep deliverable is not a cheat sheet — `slides/week17.md` closes on *"Bring your project: threat model, SBOM, signed artifact, CI pipeline"*, and `labs/week16-capstone` / `project/README.md` define the artefacts. The Week 17 job is to leave the room with a project that **runs** and a team that knows its Week 19 roles. Confirm, per team: the project demos end-to-end, the SBOM and signed artifact exist, the CI pipeline is green, and each member can name one challenge class they own. Any grading of the demo itself is in Week 19 (⬚ here — the repo states the deliverable, not a Week 17 mark for it).

## 8. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Cumulative review quiz — Quiz 2 (25 pts) | Quiz score | K1, K2 | Part of the 10% quizzes / participation component |
| Mock CTF | Payload + one-line fix recorded per challenge | P1, P2, A1 | **Ungraded** — participation |
| Security Jeopardy: Champions | Team points | K1 | Non-graded engagement (Houses); CTFd Awards if the scoreboard is running |
| Project readiness check | Runnable project + named Week 19 roles | P3, P4 | ⬚ (graded in Week 19, not today) |
| Debrief self-assessment | Named weak areas | P4, A2 | Formative — feeds the instructor's Week 18/19 support list |

There is **no worksheet** for Week 17: the lab folder holds `README.md` and `mock-ctf.md` only, and the week carries none of the 13 graded worksheets. The graded final follows in Weeks 18–19 (25% of the course mark, course specification §4).

## 9. Materials

- Lab: `labs/week17-review-final-prep/` — `README.md`, `mock-ctf.md`
- Quiz: `quizzes/quiz2.md` (25 pts, 30 min) · quiz mechanics: `quizzes/README.md`
- Slides: `slides/week17.md`
- Mock-CTF targets: `labs/week10-api-security` (`docker compose up`), `labs/week11-memory-safety-exploitation` (toolbox container — `labs/toolbox`), `labs/week12-supply-chain` (`bash sca_scan.sh` / `bash sign.sh`), `labs/week13-cloud-container` (`bash scan.sh`), `labs/week14-ai-llm-security` (`docker compose up`), plus a web-half callback (`labs/week04-injection` / `labs/week05-xss-client-side` / `labs/week06-authn-authz`)
- Solution files the mock self-checks against: `solution_api.py` (W10), `exploit_skeleton.py` and `safe.rs` (W11), `sign.sh` and `sca_scan.sh` (W12), `harden.md` (W13), `guarded_chatbot.py` (W14), and the week04–06 solutions
- Toolbox image (Week 11 binary): `labs/toolbox` (`docker build -t softsec-toolbox labs/toolbox`, `FROM silkeh/clang:19`)
- What comes next: `labs/week18-final-written/` · `labs/week19-final-ctf-capstone/` · term project `project/README.md`
- Instructor-only (git-ignored): `instructor/CTFd-SETUP.md` (scoreboard, Houses, Awards), `instructor/make_quiz_forms.gs` (build the quiz Form), `instructor/exams/item-bank.md` (Jeopardy seed / final pool), `instructor/seed_flags.py` (per-student flags — for Week 19, not today)
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 10. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **The toolbox build is the long pole.** The Week 11 binary target needs the `softsec-toolbox` image (`FROM silkeh/clang:19` + apt install of gdb/nmap/sqlmap). Built cold in class on a weak network, it can swallow the first 20 minutes of the mock and blocks challenges 3 **and** 4 | Build it the day before (`docker build -t softsec-toolbox labs/toolbox`); have teams start the build during the 1:45–2:00 break, not at 2:00; keep an offline copy (`docker save`/`docker load`). Teams who did Week 11 on the same machine already have the image |
| **Apple-Silicon platform mismatch on the binary challenge.** The toolbox is **not** platform-pinned, so on an M-series Mac `docker build` produces an **arm64** image. The mock hint "offset 72 → overwrite RA" and `exploit_skeleton.py`'s arithmetic (`buf[64] + saved RBP = 72`, then the saved RIP is overwritten with `WIN_ADDR`, `0x401176`-style) are **x86-64**; on arm64 the offset and `objdump` addresses differ | The worksheet already forbids trusting 72 — have students **derive the offset** with the cyclic pattern and read `&win` from `objdump` on *their* build (Week 11 Task 2). If x86-64 parity with the hint is wanted, build/run the toolbox as `linux/amd64` under emulation (slower). Either way, the flag/`[+] win() reached` line is the proof, not the number 72 |
| **`make vuln` fails on a macOS host.** `-z execstack`/`-no-pie` are GNU-ld/Linux flags; the link step fails outside the container (`Makefile` L14–16) | Build and run the binary **only inside the toolbox** with `--cap-add=SYS_PTRACE --security-opt seccomp=unconfined`; `make syntax` is the host-side parse check, not a build |
| **Two Trivy pulls + a Cosign network call.** Challenge 5 (`sca_scan.sh`/`cosign verify`) and challenge 6 (`bash scan.sh` → `aquasec/trivy:latest`) both hit the network; `cosign verify` reaches the registry and Rekor | Pre-pull `aquasec/trivy:latest` the day before; run the scans during the break. A team offline can still do challenge 6 by code review of `Dockerfile.insecure` against `harden.md` and describe the mitigation — which is what the Week 18 partial-credit answer rewards |
| **Trivy won't flag the IAM policy — students think it's clean.** `trivy config` does not parse standalone IAM JSON, and only 3 of the 6 `Dockerfile.insecure` defects map to Trivy rules (`scan.sh` L18–21) | Brief this before the block: the IAM `*:*` and the manual-review defects (`COPY . .`, `chmod -R 777`, unpinned `pip install`) are found by **reading** the file against `harden.md`, not by the scanner. Frames misconception #9 |
| **Host-port 8080 clash between W10 and the web callback.** `labs/week10-api-security` publishes `8080:5000`, and challenge 8's callback targets (`week04`/`05`/`06`) each also publish `8080:5000`. A team that leaves the API up and then `docker compose up`s a web-half target gets a bind failure | Run one 8080 target at a time (the API and the callback are independent challenges), or override the published port in the second compose file. `:8081` (secure API) and `:6000/:6001` (Week 14) do not clash |
| **The Jeopardy board does not exist until someone makes it.** Nothing ships in the repo; without it the 75-minute middle block has no content | Build the 6 × 5 board plus the Final-Jeopardy wager beforehand from `instructor/exams/item-bank.md`. Fallback: run the "Map of the modern stack" cold-call recap from `slides/week17.md` and extend the mock-CTF block |
| **The CTFd scoreboard may not be up.** AGENDA.md hedges it as "if running", so points from Jeopardy and the mock may have nowhere to land | Tally on the whiteboard and enter CTFd Awards afterwards (`instructor/CTFd-SETUP.md` §6: 300/200/100, first-blood +100, most creative +50). Nothing today is graded on those points |
| **A team cannot sit the Form quiz** — Quiz 2 runs as a Google Form locked to the school account (SUBMISSION.md) | Print `quizzes/quiz2.md`; it carries name/ID/date fields and marks up to the same 25 |
| **Quiz-item leakage between cohorts.** `quiz2.md` is a static file reused each term | Swap two or three Part A MCQs and/or the Part B/C alternates from the review-quiz item bank into a cohort copy, holding the total at 10 × 1 + 3 × 3 + 2 × 3 = 25 |

## 11. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per block (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Mock-CTF challenges left unsolved by more than a third of the teams: ⬚
- Misconceptions from §6 that actually surfaced in the debrief (and any new ones): ⬚
- Anything to change before this week runs again: ⬚
