# Lesson Plan — Week 2: Secure SDLC, Tooling & Fuzzing

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 2 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week02-sdlc-tooling` |
| **Slides** | `slides/week02.md` |
| **Standards** | OWASP 2025 **A05 Injection** [CWE-89, CWE-78] · **A04 Cryptographic Failures** [CWE-327] · **A02 Security Misconfiguration** [CWE-798, CWE-489] |
| **CLOs addressed** | **CLO4** operate security tooling across the SDLC · **CLO5** evaluate & communicate · **CLO6** evidence & ethics |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — Place security activities across the SDLC and say what "shift-left / DevSecOps" means in practice for a CI pipeline.
- K2 — Distinguish SAST, DAST, SCA and secret scanning by what each *sees* and when in the SDLC each runs, and explain why hardcoded secrets keep ending up in repositories.
- K3 — Explain why coverage-guided fuzzing is considered the dominant modern bug-finding technique, and what pairing it with a sanitiser adds.
- K4 — Define true positive vs. false positive in scanner triage, and why misclassifying in either direction is costly.

**Skills (P)**
- P1 — Stand the tooling up: run `bash scan.sh` and confirm both the Semgrep and the Gitleaks section produce output.
- P2 — Read Semgrep output and locate the SQL injection in `/user` (CWE-89, string-formatted query), the OS command injection in `/ping` (CWE-78, `shell=True`), the weak `md5` password hash (CWE-327) and `debug=True` (CWE-489), each with its `file:line`.
- P3 — Read Gitleaks output and identify `AWS_SECRET_ACCESS_KEY` and `DB_PASSWORD` (CWE-798), naming the rule that fired for each.
- P4 — Triage findings into a table — *Tool | File:Line | CWE | Severity | TP/FP | Fix idea* — with at least 3 true positives and 1 likely false positive, each justified.
- P5 — Build and run a libFuzzer harness under AddressSanitizer and capture the resulting crash.
- P6 — Apply the same three tools (Semgrep, Gitleaks, Trivy) to the team's own project target and produce a findings list.
- P7 — Turn a manual scan into an automated CI gate that fails on HIGH/CRITICAL.
- P8 — Remediate the planted flaws and present a before/after diff for each, mapped to its CWE.

**Attitude (A)**
- A1 — Run the scanners only against the provided `vulnerable-repo/` on their own machine; do not point SAST/secret scanners at third-party repos or production systems without authorisation, and treat any secret found here as fake lab data ([ETHICS.md](../../ETHICS.md)).
- A2 — Submit evidence that is identifiably their own work — `whoami` / login email / student ID and a timestamp on every screenshot — and be able to reproduce it live on request.
- A3 — Treat AI-generated security code and advice as something to critique and verify, not to trust.

## 2. Key ideas (the through-line)

No single tool sees the whole program. SAST reads the source and can spot a pattern the code will never
have to execute; a secret scanner reads bytes the source-analyser has no rule for; SCA reads the
dependency list rather than the code at all; a fuzzer learns nothing from reading and everything from
*running*. This week's lab is deliberately arranged so each tool finds something the others cannot —
Semgrep finds the string-built query, Gitleaks finds the credentials sitting three lines above it, and
libFuzzer finds a missing bound check that no pattern rule was ever going to match. The second half of
the idea is that a finding is not a bug: it becomes one only when a human assigns it a CWE, a severity
and a true-positive/false-positive call they can defend. A scanner that cries wolf gets switched off,
which is why triage — not scanning — is the graded skill this week.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
- **Instructor, before class:** pre-pull the three scanner images and build the toolbox —
  `semgrep/semgrep`, `zricethezav/gitleaks:latest`, `aquasec/trivy`, and
  `docker build -t softsec-toolbox labs/toolbox`. Trivy additionally downloads its vulnerability
  database on first run, so run it once on the room's network before the session. Have the offline
  fallback ready (see §8).
- **Prerequisite concept:** what a CWE identifier is (Week 1), and how to read a `file:line` reference.

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | ~10-min retrieval quiz on Week 1 (security mindset, trust boundaries, STRIDE); bridge — Week 1 found *design* flaws before code, this week finds *implementation* flaws automatically and at scale; today's agenda | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concepts | Security across the SDLC (Requirements → Design → Code → Build → Test → Deploy → Operate) and what "shift left" buys; the tooling families table — SAST / DAST / SCA / secret scanning / fuzzing, each by *what it sees* and *when*; SAST vs. DAST in one line; the worked example on the `/user` endpoint and the hardcoded key, pointing at the exact line each tool fires on | Lecture + live scanner run on the projector (the hook: run a scanner on a flawed repo and let a finding pop up in seconds) |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | Fuzzing: random/mutated inputs, coverage-guided exploration (libFuzzer/AFL++), pairing with ASan to pinpoint the bug, and `clang -g -fsanitize=address,fuzzer harness.c -o fuzz` run against a seeded corpus (measured on this repo: unseeded runs found the bug in only 1 of 6 attempts within 45 s, a seeded `printf 'FUZ' > corpus/seed` crashed on all 3 — worth saying out loud, since "the fuzzer found nothing" is the most common lab outcome); then triage — TP vs. FP, CWE + severity, prioritising by exploitability × impact. Real cases: ⬚ *(the repo names no breach for this week — pick two, or collect them from the class; Part 4 Q2 asks each student to name one)* | Lecture + short discussion: "what control would have caught this before release?" |
| 1:35–1:55 | Defences | The five remediations students will apply in the lab — parameterised query with a `?` placeholder; an argument list instead of `shell=True`; secrets moved to environment variables; bcrypt/argon2 instead of `md5`; `debug=False`. Then the tools they will meet outside the course: SonarQube (quality gate over the "7 axes"), GitHub Advanced Security (CodeQL + secret scanning + Dependabot), and technical debt as a cost-curve argument | Lecture with before/after code comparisons |
| 1:55–2:00 | Brief the games | **"Bug Triage Race"** — Semgrep + Gitleaks on the flawed repo, score = true positives − misclassified, live scoreboard — plus the **"Fuzzing Race"** mini-game: first team to make `harness.c` crash wins | Instruction |

**Checks for understanding during lecture**
- After the tooling-families table: cold-call *"which tool finds the secret? which finds the SQL injection? could one tool find both?"*
- Before the break: one-minute paper — *"name a bug SAST would miss but DAST would catch."*

## 5. Laboratory — 180 min

Target: `cd labs/week02-sdlc-tooling` → `cat scan.sh` → `bash scan.sh`, which runs Semgrep
(`--config p/default --config p/owasp-top-ten`) then Gitleaks against `./vulnerable-repo`. The scanned
target is `vulnerable-repo/app.py` plus `requirements.txt`; it contains five planted flaws. There is no
`docker compose` target this week — the "app" is a repository, not a running service.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:05 | **Task 0 — Onboarding (5 min)** | Run `bash scan.sh`; confirm both the Semgrep and the Gitleaks section produce output | Screenshot showing both tools ran |
| 0:05–0:30 | **Task 1 — SAST sweep with Semgrep (25 min)** | Read the Semgrep output; locate the SQL injection in `/user` (CWE-89), the OS command injection in `/ping` (CWE-78, `shell=True`), the weak `md5` password hash (CWE-327) and `debug=True` (CWE-489) | One screenshot per finding with the `file:line` |
| 0:30–0:45 | **Task 2 — Secret scan with Gitleaks (15 min)** | Read the Gitleaks output; identify `AWS_SECRET_ACCESS_KEY` and `DB_PASSWORD` (CWE-798) | Screenshot + the rule that fired for each |
| 0:45–1:15 | **Task 3 — Bug Triage Race (30 min)** | Build the table *Tool \| File:Line \| CWE \| Severity \| TP/FP \| Fix idea*; mark at least 3 true positives and 1 likely false positive and justify each (score = TP − misclassified) | The completed triage table |
| 1:15–1:25 | **Task 4 — Fuzzing intro (10 min)** | In the `labs/toolbox` container (Apple clang has no libFuzzer runtime), build `clang -g -fsanitize=address,fuzzer harness.c -o fuzz`, then **seed the corpus** and run: `mkdir -p corpus && printf 'FUZ' > corpus/seed && ./fuzz corpus` | The ASan crash output (or a screenshot) + a 2-sentence note on why fuzzing finds this bug when a linter/SAST pass over the same 4-line check would not |
| 1:25–2:05 | **Task 6 — Scan the project target (40 min)** | Run Semgrep + Gitleaks against **NoteVault** (`../../project/starter-app`); also run `docker run --rm -v "$PWD/../../project/starter-app:/src" aquasec/trivy fs /src` | A findings list (tool, `file:line`/CVE, CWE) — reused later in the project vuln report |
| 2:05–2:30 | **Task 7 — Build a security CI gate (25 min)** | Adapt `../week15-devsecops-pipeline/security-ci.yml` into a workflow that runs Semgrep + Trivy + Gitleaks and **fails on HIGH/CRITICAL**; run it locally (`act`) or commit to a fork and read the Actions log | The workflow file + a screenshot of a failing run |
| 2:30–2:40 | **Task 5 — Defend / fix it (10 min)** | Remediate the planted flaws in `vulnerable-repo/app.py`: parameterised query (`?` placeholder) in `/user`; drop `shell=True` and pass an argument list in `/ping`; both secrets to environment variables; bcrypt/argon2 instead of `md5`; `debug=False` | A before/after diff for each fix mapped to its CWE |
| — homework | **Task 8 — SAST blind spots (20 min)** | Find one real bug in `vulnerable-repo/app.py` (or NoteVault) that Semgrep did **not** flag, and explain why a pattern-based tool missed it | The bug + a 2-sentence explanation |
| 2:40–2:55 | **AI-resilient tasks** | *Audit the AI* (critique an AI-written exploit or fix), *Explain-in-Plain-English*, *Prompt Problem* | Written answers (start in class, finish as homework) |
| 2:55–3:00 | **Micro-demo + submit** | 2–3 rotating students give a 2–3 min "show your finding/fix"; everyone submits | Worksheet PDF → Classroom; fixed code → GitHub |

> **Scheduling note — this week is over-subscribed.** Worksheet 2's own task budgets
> (5 + 25 + 15 + 30 + 10 + 40 + 25 + 20 + 10) already total 180 min, leaving no room for
> [AGENDA.md](../../AGENDA.md)'s standard-template blocks — *AI-resilient tasks* (20 min) +
> *rotating micro-demo* (10 min) + *submit* (5 min), **35 min combined, not 20**. AGENDA.md flags a
> related drift itself ("Current `worksheet.md` Part-3 durations vary (145–205 min)"). The resolution
> above takes **Task 8 off the clock** and sets it as homework, which frees only 20 of the 35 min
> needed — so the schedule above does not restore AGENDA's blocks at their standard length, it
> further compresses them: *AI-resilient tasks* to **15 min** (2:40–2:55) and *micro-demo + submit*
> combined to **5 min** (2:55–3:00), instead of the standard 20 + 10 + 5. Task 8 is the only
> 20-minute task whose removal does not break the break-then-defend sequence, and it feeds Part 4
> Reflection Q3 naturally. Tell the class about this compressed slot at 0:00 so nobody expects the
> full micro-demo window.

**Formative checkpoints.**
- Verified on the current files (2026-07-26): `scan.sh` reports **10 Semgrep findings** ("Ran 322 rules
  on 3 files") against only **four planted code flaws** — several rules fire on the same line. Say so
  before Task 3 starts, or half the room will count duplicate rule hits as separate true positives and
  lose points to "misclassified". Deduplicating overlapping hits is precisely the judgement the score
  (TP − misclassified) is meant to reward.
- Students expect a secret scanner to name an AWS-specific rule for `AWS_SECRET_ACCESS_KEY`. It does
  not — the rule keys on entropy and shape, not on the variable name. Keep your own copy of the
  expected Gitleaks output to hand; students who guess the rule name from the variable will record
  Task 2's "rule that fired" wrongly. This is a good 30-second discussion of what a secret scanner
  actually looks at.
- A student still without Gitleaks output at 0:45 is almost always running it from the wrong place —
  see the first two rows of §8.
- Tasks 0–3 must be done by 1:15 for the fuzzing race and the project scan to fit. A team still stuck
  on triage at that point should freeze its table at three justified rows and move on.

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 2, Part 2 (lecture questions) | Written answers | K1–K4 | 20 of the worksheet's 100, within the 30% worksheet component |
| Worksheet 2, Part 3 (scan output + triage table + screenshots) | Commands run, screenshots, triage table, ASan crash | P1–P7, A1 | 40 of 100 |
| Worksheet 2 — remediated `app.py` with before/after diffs | Diffs mapped to CWE | P8 | 25 of 100 |
| Worksheet 2, Part 4 (reflection) | CWE/OWASP mapping, a real breach, tool-value judgement | K2, K4 | 15 of 100 |
| Weekly quiz (start of lecture) | Quiz score | K1–K4 | Part of the 10% quiz/participation component |
| Bug Triage Race score (TP − misclassified) | Live scoreboard | P4 | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation | P1–P8, A2 | Pass/flag for follow-up |
| Per-student flag | ⬚ — the worksheet issues one only conditionally ("if this lab issues one"); the repo does not record a Week 2 flag | A2 | Integrity control, not a mark |

*Audit the AI* and the *EiPE / Prompt Problem* count toward the worksheet's "Defense + Reflection"
score, in the rubric's own wording. Partial credit is available where a student explains a mechanism correctly but could not
land the tool run.

## 7. Materials

- Lab: `labs/week02-sdlc-tooling/` — `README.md`, `worksheet.md`, `scan.sh`, `harness.c`,
  `vulnerable-repo/app.py`, `vulnerable-repo/requirements.txt`
- Slides: `slides/week02.md`
- Toolbox (needed for Task 4): `labs/toolbox/` — clang 19 with libFuzzer/ASan, gdb, nmap, sqlmap,
  python3, git, curl, vim
- Project target for Task 6: `project/starter-app` (NoteVault)
- CI template for Task 7: `labs/week15-devsecops-pipeline/security-ci.yml`
- References (from the lab README): OWASP Secure Product Design Cheat Sheet · https://semgrep.dev/ ·
  https://github.com/gitleaks/gitleaks · https://llvm.org/docs/LibFuzzer.html ·
  https://github.com/AFLplusplus/AFLplusplus
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Gitleaks reports "no leaks found" from the repository root.** `.gitleaks.toml` allowlists `labs/week02-sdlc-tooling/vulnerable-repo/.*` so this repo's own CI is not failed by its planted teaching secrets — a student who scans from the root concludes the tool is broken | Insist on `cd labs/week02-sdlc-tooling` and `bash scan.sh`, which mounts `vulnerable-repo` directly and never sees the repo config. Worth 60 seconds in the brief: the allowlist is itself a teachable artefact |
| **The README's Gitleaks command and `scan.sh`'s differ, and only one works.** `scan.sh` runs `detect --no-git -s /repo -v`; the README §game block shows `detect -s /repo -v`. `vulnerable-repo/` is not a git repository, so the README form fails with `fatal: not a git repository` and prints "no leaks found" — verified 2026-07-26. `scan.sh`'s form prints `leaks found: 2` | Have students run `scan.sh` (the worksheet's own instruction), and use the discrepancy as the day's first triage lesson: a tool that exits quietly having scanned nothing is worse than one that errors |
| `scan.sh` run from the wrong directory | It mounts `"$PWD/$TARGET"`, so it only works from inside `labs/week02-sdlc-tooling`. The `cat scan.sh` step in the worksheet exists precisely so students read the mount before running it |
| **Three image pulls plus a database download in one room.** `semgrep/semgrep`, `zricethezav/gitleaks:latest`, `aquasec/trivy` (Task 6), and `silkeh/clang:19` under the toolbox build; Trivy then fetches its vulnerability DB on first run | Pre-pull and pre-build before the session; keep a USB copy (`docker save` / `docker load`). If the network dies mid-session, Tasks 0–5 still run from cached images; Task 6's Trivy step is the one that hard-fails without it |
| **Task 4 will not build on the host.** Apple clang ships no libFuzzer runtime, and the toolbox needs its capability flags | Run inside `labs/toolbox`: `docker run -it --rm --cap-add=SYS_PTRACE --security-opt seccomp=unconfined -v "$PWD":/work -w /work softsec-toolbox`. Omitting `--cap-add=SYS_PTRACE --security-opt seccomp=unconfined` is the classic ASan/gdb failure. Build the image before class, not during it |
| **Task 7 needs `act` or a GitHub fork with Actions enabled** — `act` is *not* in the toolbox image, and a fork run needs an account and network | Decide before class which route the room takes. If neither is available, accept the workflow file plus a written account of which job fails and on which severity threshold, and defer the failing-run screenshot to homework |
| **Students over-count Semgrep findings.** Ten findings over four planted code flaws — several rules fire on the same line | Warn at the start of Task 3 that duplicate rule hits on the same line are one finding. This is exactly the judgement the score (TP − misclassified) is meant to reward |
| **Leftover fuzzing artefacts in the lab folder.** Running the harness writes `fuzz` and a `crash-<sha1>` reproducer into whatever directory is mounted | Both patterns are git-ignored (`fuzz`, `crash-*`), but delete them at the end of the session — the curriculum monorepo's parity gate compares every file in the lab directory |
| A team finishes Tasks 0–3 by 0:45 | Extension: bring Task 8 back on the clock, or have them write the Semgrep rule that *would* have caught their Task 8 bug |
| Copy-paste of another team's triage table | Identity-stamped screenshots (`whoami` / student ID + timestamp) plus the viva spot-check; triage justifications are the part that cannot be copied without being explainable |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚
