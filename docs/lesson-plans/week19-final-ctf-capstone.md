# Lesson Plan — Week 19: Final — Capstone CTF Tournament + Project Demos

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 19 · ⬚ |
| **Contact time** | 240 min — a single final block: **150 min capstone CTF + 90 min graded project demos**. No lecture, no lab (`AGENDA.md`, *Week 19 — Final CTF + project demos (240 min)*) |
| **Lab folder** | `labs/week19-final-ctf-capstone` — holds `README.md` and `ctf.md` (the student paper); it ships no target of its own |
| **Slides** | `slides/week19.md` — proctor/compère deck, not a teaching deck |
| **Covers** | The whole term (`ctf.md`, *Covers*): web, API, supply chain, cloud, memory safety and LLM/agentic challenges (`labs/week19-final-ctf-capstone/README.md`) |
| **Targets** | `labs/week04-injection` · `labs/week05-xss-client-side` · `labs/week06-authn-authz` · `labs/week10-api-security` · `labs/week11-memory-safety-exploitation` · `labs/week12-supply-chain` · `labs/week13-cloud-container` · `labs/week14-ai-llm-security` (the week named against each challenge in `ctf.md`) · `project/starter-app` for the demos |
| **Standards** | The ids the source weeks' READMEs attach: **A05** Injection · CWE-89, CWE-78 (W4) · **A05** Injection · CWE-79, CWE-352 (W5) · **A01** Broken Access Control, **A07** Authentication Failures · CWE-639, CWE-287 (W6) · **API1** BOLA, **API3** broken object property level auth (mass assignment), **API4** unrestricted resource consumption (W10) · CWE-787, CWE-121, CWE-416, CWE-134, CWE-193 (W11) · **A03** Software Supply Chain Failures, **A08** Software or Data Integrity Failures · CWE-1104, CWE-829 (W12) · **A02** Security Misconfiguration · CWE-732, CWE-16 (W13) · **LLM01** Prompt Injection, **LLM02** Sensitive Info Disclosure, **LLM05** Improper Output Handling, **LLM06** Excessive Agency, **LLM08** Vector/Embedding Weaknesses, **LLM10** Unbounded Consumption (W14) |
| **CLOs addressed** | **CLO2** exploit · **CLO3** remediate · **CLO5** evaluate & communicate · **CLO6** evidence & ethics (course specification §6, row 19) |

---

## 1. Session objectives

This is an assessment, not a teaching session. It carries **two separate instruments in one room** —
a team CTF and a graded team demo — and they feed two different gradebook columns (§5). What the
sitting is designed to evidence:

**Knowledge (K)**
- K1 — For each challenge solved, state in one line the control that would have prevented it
  (`ctf.md` requires a **mitigation** column per challenge).
- K2 — Recognise which vulnerability class a target's behaviour belongs to across the *whole* term,
  without task scaffolding: `ctf.md` states only a title, a topic and the source week.
- K3 — For the demo: name each finding's **CWE** and **OWASP Top 10:2025** (or API / LLM Top 10)
  category and its root cause (`project/README.md`, deliverable 2; `labs/week16-capstone/worksheet.md` Part 3 B).

**Skills (P)**
- P1 — Web half: SQLi login, command injection, stored XSS (challenges 1–3, targets W4/W5).
- P2 — Identity and access: IDOR, forging a JWT to admin, BOLA + mass assignment (challenges 4–6,
  targets W6/W10).
- P3 — Binary half: stack overflow → `win()` ret2win, and crashing the binary with a fuzzer
  (challenges 7–8, target W11).
- P4 — Build and platform: find the vulnerable dep / unsigned image; exposed secret / `*:*` IAM /
  root Dockerfile (challenges 9–10, targets W12/W13).
- P5 — LLM: prompt injection → leak the secret; indirect injection / output XSS (challenges 11–12,
  target W14).
- P6 — Record, per challenge, the **flag (or noted proof)**, the **payload/command** and a
  **one-line mitigation** — the three columns of `ctf.md`'s submission table.
- P7 — Present a secured build end to end: threat model → vulnerabilities found → remediation;
  SBOM + signed artifact; security CI/CD pipeline; **a pre-recorded video walkthrough submitted
  before the session, plus a 3-minute live Q&A** (`labs/week19-final-ctf-capstone/README.md`).

**Attitude (A)**
- A1 — Attack only the provided targets, under [ETHICS.md](../../ETHICS.md) (`ctf.md`, *Rules*).
- A2 — One submission per team per challenge; document the method (`ctf.md`, *Rules*).
- A3 — Answer unscripted follow-up questions on the team's own work at the demo — a live viva check
  (`project/README.md`, deliverable 6).

## 2. What is assessed

### 2.1 The tournament — 12 challenges, 150 points, 150 minutes, team-based

Titles, topics and points exactly as printed in `ctf.md`. Each challenge is independent — a target
that will not start costs the team that challenge, not the paper.

| # | Title | Topic / target | Pts |
|---|---|---|---:|
| 1 | **Boolean Bypass** | SQLi login (week04) | 10 |
| 2 | **Shell Out** | command injection (week04) | 15 |
| 3 | **Persistent Pop** | stored XSS (week05) | 10 |
| 4 | **Not Your Object** | IDOR (week06) | 10 |
| 5 | **Token Smith** | forge JWT to admin (week06) | 15 |
| 6 | **Raid the API** | BOLA + mass assignment (week10) | 15 |
| 7 | **Smash** | stack overflow → `win()` ret2win (week11) | 20 |
| 8 | **Fuzz First** | crash the binary with a fuzzer (week11) | 10 |
| 9 | **Bad Dependency** | find the vulnerable dep / unsigned image (week12) | 10 |
| 10 | **Misconfig Hunt** | exposed secret / `*:*` IAM / root Dockerfile (week13) | 15 |
| 11 | **Jailbreak the Bot** | prompt injection → leak the secret (week14) | 10 |
| 12 | **Indirect Hit** | indirect injection / output XSS (week14) | 10 |

`ctf.md` adds: *"Difficulty rises with points"*, and *"First-blood bonus at instructor's discretion."*

### 2.2 The demo — graded separately

Each team presents its secured build: threat model → vulnerabilities found → remediation; SBOM +
signed artifact; security CI/CD pipeline. **Format (graded):** each team submits a pre-recorded
video walkthrough **before the session** (graded asynchronously against the project rubric), and
the in-class slot is a **3-minute live Q&A** — a viva check, not a re-demo
(`labs/week19-final-ctf-capstone/README.md`; `AGENDA.md` §*Week 19*). `ctf.md` line 6 says the demo
*"is scored separately"* and links the rubric — see the cross-reference defect noted in §5.

**CLO coverage.** Challenges 1–12 evidence **CLO2**; the per-challenge mitigation line is the
**CLO3** evidence available inside a 150-minute tournament (there is no defend-and-re-test task, as
there is in a teaching week). The demo carries **CLO3** (remediation shown and re-tested) and
**CLO5** (communicating a finding, its impact and its fix, plus the Q&A). Per-student flags,
identity-stamped evidence and the live viva carry **CLO6**.

## 3. Preparation and infrastructure readiness

### 3.1 What this sitting actually runs on

- **Student machines, local Docker.** "All lab targets run locally in Docker" on the student's own
  machine; no cloud account for the core labs (course specification §1, §10). Solving does not
  depend on the campus network — but *starting* the targets does (§3.4, §9).
- **No new target ships this week.** `labs/week19-final-ctf-capstone/` contains only `README.md`
  and `ctf.md`; every challenge points at an existing lab folder, and the demos run each team's own
  project repository plus `project/starter-app` (NoteVault).
- **CTFd is the scoreboard, not the grade.** `instructor/CTFd-SETUP.md` is explicit: the flags in
  `instructor/ctfd/challenges.yml` are shared/static placeholders (a `_XXXX` suffix to rotate per
  cohort), and CTFd is the engagement arena; graded integrity uses the per-student flags from
  `seed_flags.py`. CTFd runs on `http://localhost:8000` (`CTFd-SETUP.md` §1).
- **The two point systems are not the same board.** The paper (`ctf.md`) is 12 challenges / 150 pts
  with fixed values. `challenges.yml` is dynamic (`initial: 500`, `minimum: 100`, `decay: 15`),
  values 200–500, splits "Raid the API" into *"crAPI Raid: BOLA"* and *"crAPI Raid: Mass
  Assignment"*, adds *"Capture the Hash"*, and carries a 15th challenge — *"Boss: Breach NoteVault"*
  — that **is not on the student paper**. (12 paper topics − 1 merged "Raid the API" + 2 split
  BOLA/Mass Assignment + 1 "Capture the Hash" + 1 "Boss" = 15 total `challenges.yml` entries.)
  `slides/week19.md`'s speaker note says to run the tournament "from `ctf.md` + `exams/item-bank.md`
  (CTF pool, incl. the boss chain)". Decide before the day which board students are told is
  authoritative; the graded instrument is the paper.
- **The spawnable platform is not in play.** `instructor/PLATFORM-ROADMAP.md` is a decision record
  whose answer is "yes — but *not now*"; the prototype was built and torn down the same session, and
  go-live is scoped to Apr 2027. Do not plan this sitting around it.
- **Submission of record.** "W19 Final CTF + demo — flags via Form; live project demo (graded by
  rubric)" ([SUBMISSION.md](../../SUBMISSION.md), *Exams*). `ctf.md`'s own submission table is the
  paper form of the same three columns.

### 3.2 Per-student flag seeding — and where it does not reach

```bash
export FLAG_SALT='<this cohort's salt — never published>'   # instructor/anti-cheating.md §A
python3 instructor/seed_flags.py gen students.txt -o flags.csv     # authoritative table
python3 instructor/seed_flags.py env <STUDENT_ID> > .env           # in the lab folder that uses it
python3 instructor/seed_flags.py verify 'FLAG{...}' students.txt   # who was this issued to?
```

`instructor/seed_flags.py` is a shim: it forwards `FLAG_SALT` to `SWSEC_FLAG_SALT` and requires the
sibling `KOSEN69 - curriculum` monorepo — without it, it exits with
`ERROR: curriculum monorepo not found at …` and generates nothing. The challenge-key vocabulary now
comes from that monorepo's `courses/software-security.yml`.

**Which of the twelve are actually attributable** (verified against the compose files, the app
source and the course manifest — not assumed):

| # | Challenge | Flag key | Seeded how | Attributable per student? |
|---|---|---|---|---|
| 1 | Boolean Bypass | `sqli` | `labs/week04-injection` compose passes `FLAG_SQLI` | **Yes** |
| 2 | Shell Out | `cmdi` | same compose passes `FLAG_CMDI` | **Yes** |
| 3 | Persistent Pop | `xss` | `labs/week05-xss-client-side` compose has *no* `environment:` block | **No** |
| 4 | Not Your Object | `idor` | `labs/week06-authn-authz` compose passes `FLAG_IDOR` | **Yes** |
| 5 | Token Smith | `jwt` | same compose passes `FLAG_JWT` | **Yes** |
| 6 | Raid the API | `bola`, `massassign` | `labs/week10-api-security` compose passes both; read at `vulnerable_api.py:15–16` | **Yes** |
| 7 | Smash | `pwn` | `vuln.c:47` reads `getenv("FLAG_PWN")` — but W11 ships **no compose**; students `make` natively | **Only if `FLAG_PWN` is exported in the shell** |
| 8 | Fuzz First | `fuzz` | no target env at all | **No** |
| 9 | Bad Dependency | `supplychain` | W12 is scripts + Dockerfile, no compose, no env | **No** |
| 10 | Misconfig Hunt | `misconfig` | W13 is Dockerfiles + IAM JSON, no compose, no env | **No** |
| 11 | Jailbreak the Bot | `promptinj` | `labs/week14-ai-llm-security` compose passes `FLAG_PROMPTINJ` to both services | **Yes** |
| 12 | Indirect Hit | `indirect` | no target env | **No** |

The course manifest says this in as many words: `xss`, `crack`, `ecb`, `fuzz`, `supplychain`,
`misconfig`, `indirect` and `boss` are listed under `extra_challenge_keys` and described there as
*"Static/manually-graded CTFd-only challenges with no attributable per-lesson lab"*. So **five of
twelve challenges (3, 8, 9, 10, 12) are not per-student by construction, and a sixth (7) only
becomes so if the student exports the variable by hand.** Plan their attribution around
identity-stamped evidence, the method note and the viva (§6) — not around the flag.

**Pre-flight, in each of the four seeded folders.** `docker compose config` must show a *value* for
each `FLAG_*`. Checked with no `.env` present, all four render `null`:

```
labs/week04-injection        FLAG_CMDI: null        FLAG_SQLI: null
labs/week06-authn-authz      FLAG_IDOR: null        FLAG_JWT: null
labs/week10-api-security     FLAG_BOLA: null        FLAG_MASSASSIGN: null
labs/week14-ai-llm-security  FLAG_PROMPTINJ: null   (both services)
```

When that happens the variable never reaches the container and the app serves the placeholder
committed in its source. W4/W6/W10 fall back to a `_demo`-suffixed `FLAG{...}` value; W14 instead
falls back to the fixed placeholder `FLAG{pr0mpt_1nj3ction_l34ks_s3cr3ts}` (`vulnerable_chatbot.py`,
`guarded_chatbot.py`) — check `docker compose config` for `FLAG_PROMPTINJ: null` rather than relying
on the string shape for that one. **A placeholder flag arriving on a submission
sheet means seeding failed, not that the team cheated.**

### 3.3 Teams, room, network, machines

- **Which team unit competes is not recorded.** `ctf.md` says only "Team-based". The Week 16
  scrimmage that previews it says "Teams of 2–4" (`labs/week16-capstone/scrimmage.md`). Project
  teams are 2–3 (`project/README.md`). `instructor/CTFd-SETUP.md` §5 is explicit that "the graded
  project teams of 2–3 are *not* CTFd teams … CTFd's single team layer **is** the House". Fix and
  announce the competing unit before the day: ⬚. It determines whose `.env` a team's targets are
  built from, and how one team score is entered against several students (§5).
- **Sharing inside a team is permitted; per-student flags therefore detect *cross-team* sharing
  only.** This is the opposite of the Week 9 individual sitting and changes what §6 can promise.
- Room / seating / invigilator count / demo room(s): ⬚ (not recorded in this repository).
- Students work on their own machines; "phones away; one device" (`instructor/anti-cheating.md` §C).
- Network is needed for image pulls, `pip install` at container start-up, Trivy's vulnerability
  database, Cosign's OIDC flow and the submission Form — **not** for solving once targets are up.
- The class size the timetable assumes is N≈80–120 (`AGENDA.md`) — see the demo-throughput
  arithmetic in §9, which needs a decision *before* the day.

### 3.4 Test the day before

- [ ] **Team unit fixed and announced** (§3.3), and the flag-planting model chosen and recorded
      (`instructor/anti-cheating.md` §A: local build per student, or instructor-seeded).
- [ ] `docker pull python:3.12-slim` — the base image W4, W5, W6, W10 and W14 all use.
- [ ] Bring each web target up **once, one at a time** (they collide on 8080 — §9) and confirm it
      answers: W4, W5, W6 and W10's `vulnerable-api` on `http://localhost:8080`; W10's
      `solution-api` on `http://localhost:8081`; W14's chatbots on `http://localhost:6000` and
      `http://localhost:6001`.
- [ ] `docker compose config` in `labs/week04-injection`, `labs/week06-authn-authz`,
      `labs/week10-api-security` and `labs/week14-ai-llm-security` shows real `FLAG_*` values, not
      `null` (§3.2).
- [ ] `python3 instructor/seed_flags.py verify '<one issued flag>' students.txt` resolves to the
      right student, **using the same salt** that `gen` ran with. Run `gen` the day before, not on
      the morning — the shim needs the sibling monorepo (§3.2).
- [ ] `python3 instructor/check_flag_keys.py` exits 0 (flag-key vocabulary in sync across the
      manifest, the deployment whitelist, the challenge CSV and `ctfd/challenges.yml`).
- [ ] **W11 builds on the machines in the room.** `make` in `labs/week11-memory-safety-exploitation`
      produces `vuln` and `vuln-hardened`; the Makefile's own note says `-z execstack` and `-no-pie`
      are GNU ld / Linux flags and "On macOS the *link* step of these targets may fail". Have the
      toolbox image built (`docker build -t softsec-toolbox labs/toolbox`) and the run line ready —
      it is the documented escape hatch, since "Apple clang ships no libFuzzer runtime, and `gdb` is
      painful on macOS" (`labs/toolbox/README.md`). Delete `vuln`, `vuln-*` and `fuzz` afterwards.
- [ ] **W12/W13 tool pulls.** `bash sca_scan.sh` and `bash sign.sh` (W12) and `bash scan.sh` (W13)
      run `aquasec/trivy:latest` in throwaway containers and mount the Docker socket; Trivy also
      needs to fetch its database. Pull the image and warm the DB before the room does.
- [ ] **Cosign is not an offline step.** `sign.sh`'s own note: "keyless signing needs a browser/OIDC
      flow and registry push access; in class this is a guided demo, not an offline step". Do not
      make a challenge or a demo depend on live signing succeeding in the room.
- [ ] CTFd (if in use) up on `:8000`, challenges imported with this cohort's rotated flag suffixes,
      dynamic scoring and first-blood on, scoreboard **frozen** for the window
      (`CTFd-SETUP.md` §3–§4).
- [ ] Submission Form open/close times set, with the settings from `instructor/anti-cheating.md` §C
      (restrict to the cohort's accounts, collect email, one response, auto-close).
- [ ] **Video-submission deadline and Q&A schedule published to teams in advance** —
      `slides/week19.md`: "Tell teams their demo slot up front"; each team's **3-minute live Q&A**
      slot follows submission of its pre-recorded video walkthrough before the session.
- [ ] The Week 16 scrimmage and the Week 17 mock CTF have been run — both state they are the same
      format as this tournament (`labs/week16-capstone/scrimmage.md`,
      `labs/week17-review-final-prep/mock-ctf.md`).
- [ ] Projector/display for the leaderboard and the demos: ⬚.

## 4. Run of show — the 240-minute block

Timings are `AGENDA.md`'s (*Week 19 — Final CTF + project demos*): `0:00–2:30` capstone CTF
tournament, `2:30–4:00` graded final project demos.

| Time | Block | Instructor does | Students do |
|---|---|---|---|
| 0:00–0:10 *(inside the 150)* | **Briefing + target check** | Run `slides/week19.md`: the two parts, the 150-minute window, the submit format (flag/proof + payload/command + one-line mitigation), the rules (provided targets only, one submission per team per challenge, document method), that flags are per-student where they exist and copying across teams is traceable, and the **port-8080 warning** (below). Confirm Docker works across the room | Stand their targets up; report anything that will not start **now**, not at 1:00 |
| 0:10–2:30 | **Competition window** | Invigilate; answer environment questions only, not challenge questions; announce first bloods aloud for hype (`slides/week19.md`); watch for placeholder flags (§3.2) | Solve challenges 1–12 in any order; fill the three columns per challenge as they go |
| 2:30 | **Submission cutoff** | Close the Form / collect the paper tables | Submit flags + payload/command + one-line mitigation |
| 2:30–4:00 | **Graded live Q&A** | Each team gets a **3-minute live Q&A** slot; ask one or two unscripted probing questions ("why this fix and not X?", "what does this SBOM line mean?") — the built-in viva (`anti-cheating.md` §D). Confirm the CI pipeline failing on a finding was shown in the submitted video (`slides/week19.md`) rather than re-demoing it live | Per team: answer the live Q&A on the video already submitted **before** the session (graded asynchronously on the project rubric) — not a re-demo, per `labs/week19-final-ctf-capstone/README.md` |

**Port warning to give in the briefing.** `labs/week04-injection`, `labs/week05-xss-client-side`,
`labs/week06-authn-authz`, `labs/week10-api-security` (`vulnerable-api`) and
`project/starter-app` **all publish host port 8080**. Unlike the Week 9 individual sitting, a team
here will want several up at once. See §9 for the fix.

**Two demands competing for the same 240 minutes, both real:**
1. `slides/week19.md`'s closing note records that the research **post-test + post-survey happen
   now** (`instructor/research/`; the post-test is 20 MCQ + 2 applied items). No slot for it exists
   in `AGENDA.md`'s 240 minutes; duration and placement: ⬚.
2. Even at 3 minutes/team the live Q&A block may not fit the largest cohorts — resolve before the
   day (§9).

## 5. Scoring — how points become marks

| Step | Rule | Source |
|---|---|---|
| Per challenge | Flag/proof + payload/command + one-line mitigation = full points | `ctf.md` (submission requirement) |
| Paper total | **150 pts** across 12 challenges (values 10–20) | `ctf.md` |
| First blood | Bonus "at instructor's discretion" | `ctf.md`, *Rules* |
| Into the gradebook (CTF) | **Final % = average** of the W18 written and the W19 CTF | `instructor/GRADEBOOK.md` |
| Into the final mark (CTF) | Final block = **25%** — so this tournament carries half of it | `syllabus.md` §6; course specification §4 |
| Into the gradebook (demo) | **Project % = min(100, rubric × peer multiplier)**, multiplier 0.8–1.1 | `instructor/GRADEBOOK.md`; `project/README.md` |
| Into the final mark (demo) | Term project = **15%**, team-graded, per-member scaled | `syllabus.md` §6 |
| Normalisation | Classroom import maps `grade ÷ maxPoints × 100` | `instructor/GRADEBOOK.md` |

**Which demo rubric.** Two 100-point rubrics exist and they are not identical: `project/README.md`
(threat model 20 / findings 25 / remediation 25 / supply chain 15 / CI 10 / presentation 5) and
`labs/week16-capstone/worksheet.md` (threat model 15 / exploitation 20 / remediation 20 / SBOM +
signing 15 / CI 15 / demo & Q&A 15), plus that worksheet's 1–5 peer-review rubric.
`instructor/GRADEBOOK.md` names **`project/README.md`'s** as *the* project rubric. Note a defect to
fix in the lab folder rather than in this plan: `ctf.md` line 6 points at
`../week16-capstone/worksheet.md` and calls it "the Week 19 worksheet" — there is no `worksheet.md`
in `labs/week19-final-ctf-capstone/`.

**Individual vs team.** Both instruments in this session are team-graded, which is unusual for this
course: individual work is ~75% of the mark (course specification §8), and the bounded team
components are the project (15%) and this capstone CTF. Two consequences to settle:

- **One team score, several students.** Whatever the CTF team unit turns out to be (§3.3), the CTF
  score is entered per student in the *Final written / CTF* column. Whether a team's CTF score is
  differentiated between members at all: ⬚.
- **Does the peer multiplier touch the CTF?** Course specification §8 reads "Team-graded work is
  bounded: the term project (15%) and the Week 19 capstone CTF, with each project member's mark
  scaled by a peer-contribution evaluation", which can be read either way.
  `instructor/GRADEBOOK.md` applies the 0.8–1.1 multiplier to the **Project** column only. Flagged,
  not resolved: ⬚.
- **First blood can exceed the maximum.** A bonus on top of 150 collides with `grade ÷ maxPoints ×
  100`. Cap it, or record the bonus as CTFd participation instead: ⬚.
- The Houses / CTFd leaderboard remains **non-graded engagement** (`syllabus.md`, *Teams & Houses*;
  course specification §7) and feeds only the *Participation %* column. Nothing else from the
  scoreboard is transcribed into the gradebook.

**Make-up sittings.** `instructor/exams/` holds a parallel **Form B for the written papers only**
(W8 and W18); there is no Form B for a practical. The rotation pool is `instructor/exams/item-bank.md`.
Absence / make-up / late policy for an exam sitting: ⬚ (institutional). The general late rule
(−10%/day, up to 3 days) is `syllabus.md` §6.

## 6. Academic-integrity controls actually used

| Control | How it is operated | What it catches |
|---|---|---|
| **Per-student flags** | `seed_flags.py gen` before the day; `verify '<flag>' students.txt` at marking | A flag submitted by one team but *issued* to a student on another — reaches challenges 1, 2, 4, 5, 6, 11 only (§3.2) |
| **Per-team NoteVault marker** | `TEAM_ID` seeds an `hmac(TEAM_SALT, TEAM_ID)`-derived marker into the app's own data (`project/starter-app/README.md`; `anti-cheating.md` §A) | A demo, report or screenshot carrying another team's marker |
| **Identity-stamped evidence** | Screenshots must carry the student's terminal `whoami` / login email / student ID **and** a timestamp | Borrowed or generic screenshots (`anti-cheating.md` §B) |
| **Method note per challenge** | The payload/command + mitigation columns of `ctf.md` | A flag held without the mechanism; also the basis for partial credit |
| **Live viva at the demo** | One or two unscripted questions per team, scored as part of Q&A | A team that copied a report or a fix and cannot improvise on it (`project/README.md`; `anti-cheating.md` §D) |
| **Similarity checking** | The same MOSS/JPlag pass used on weekly forks, run on **team project repos** at the Week 19 milestone — report PDFs through MOSS's plain-text mode too | Verbatim copying between teams (`anti-cheating.md` §B) |
| **Scoreboard freeze** | CTFd → Settings → Freeze time for the window | Progress leaking between teams mid-sitting (`CTFd-SETUP.md` §4) |
| **Dynamic scoring + first blood** | Already configured (`initial: 500`, `minimum: 100`, `decay: 15`) | Reduces the incentive to pool answers (`anti-cheating.md` §C) |
| **Rotation each cohort** | New `FLAG_SALT`, new data seeds, new CTFd flag suffixes, at least one target changed per topic | Last year's flag dump (`anti-cheating.md` §E; `CTFd-SETUP.md` §7) |

**Known limits, so they are covered deliberately rather than assumed away:**

- **Sharing within a team is allowed** — that is what "team-based" means. Per-student flags here
  prove *which team* a flag reached, not which student typed it. Individual mastery is evidenced
  elsewhere in the course (worksheets, quizzes, W8/W9/W18), not by this tournament.
- **Challenges 3, 8, 9, 10 and 12 carry no per-student flag at all**, and 7 only if `FLAG_PWN` was
  exported (§3.2). Their attribution rests on identity-stamped evidence, the method note and the
  demo viva — weight the spot-checks towards them.
- A placeholder flag is a **seeding failure**, not cheating (§3.2). Check `docker compose config`
  before accusing anyone.
- `verify` only resolves flags generated with the **same salt**; a salt mismatch looks like an
  unattributable flag.
- CTFd's own flags are **shared and static** by design (`CTFd-SETUP.md`) — a matching CTFd flag
  proves nothing about authorship.
- Red flags to carry into marking (`anti-cheating.md` §F): identical screenshots across teams, a
  flag `verify` attributes to another team's member, a NoteVault marker that resolves to a different
  team, code that appears fully formed in one commit with no history, prose that does not match the
  team's own data seed.
- If copying is found: [ETHICS.md](../../ETHICS.md) + the conduct process; keep the `verify` output,
  the MOSS report and the commit log as evidence (`anti-cheating.md` §G).

## 7. After the session — debrief and how results feed the final mark

- **Debrief.** `AGENDA.md` allocates no debrief inside the 240 minutes, and this is the last week of
  term — there is no following session to borrow an opening block from, as Week 9 borrows Week 10's.
  What `slides/week19.md` closes with instead: name the arc (threat-model → break → fix → ship),
  point to next steps (OWASP, CTFs, the readings), and celebrate. Where a real
  post-mortem/results debrief happens, if at all: ⬚.
- **Marking.** Keys are instructor-only and git-ignored:
  `instructor/exams/week19-final-ctf-capstone-ctf-answers.md` for the tournament; the project rubric
  in `project/README.md` for the demo. Never copy any key content into this repository's public files.
- **Into the mark.** Enter the CTF score under *Final written / CTF*; the sheet recomputes **Final % =
  average** of W18 and W19 (`instructor/GRADEBOOK.md`), and Final is **25%** of the mark. Enter the
  demo score under *Project rubric*, then each member's **peer multiplier** (0.8–1.1); Project % =
  min(100, rubric × multiplier) and Project is **15%**. `gradebook_sync.gs` pulls Classroom and CTFd
  automatically; the subjective rubric scores are graded once in Classroom and synced.
- **Term close-out.** Read **FINAL %** + **Letter** from the Master Sheet, export a PDF/CSV
  snapshot, and enter the official grade into the institutional system (`instructor/GRADEBOOK.md`).
  Grading scale: ⬚ (institutional; the template's default bands are editable on its *Scale* sheet).
- **Outcome attainment.** Map the assessment scores back to the CLO table in course specification §4
  (§9 of that document).
- **Into next time.** A challenge nobody solved, or everybody solved, is an item-bank note
  (`instructor/exams/item-bank.md`).

## 8. Materials

- Paper + brief: `labs/week19-final-ctf-capstone/ctf.md`, `labs/week19-final-ctf-capstone/README.md`
- Deck: `slides/week19.md`
- Targets (`docker compose up` in each unless noted): `labs/week04-injection/`,
  `labs/week05-xss-client-side/`, `labs/week06-authn-authz/`, `labs/week10-api-security/`,
  `labs/week11-memory-safety-exploitation/` (`make`; no compose),
  `labs/week12-supply-chain/` (`bash sca_scan.sh`, `bash sign.sh`; no compose),
  `labs/week13-cloud-container/` (`bash scan.sh`; no compose), `labs/week14-ai-llm-security/`
- Demo target and rubric: `project/README.md`, `project/REPORT-TEMPLATE.md`,
  `project/starter-app/` (NoteVault — `export TEAM_ID=<your-team-name> && docker compose up`)
- Toolbox for W11 on macOS/Windows hosts: `labs/toolbox/` —
  `docker build -t softsec-toolbox labs/toolbox`
- Dry runs students should have done: `labs/week16-capstone/scrimmage.md`,
  `labs/week17-review-final-prep/mock-ctf.md`
- Instructor-only (git-ignored): `instructor/seed_flags.py`, `instructor/check_flag_keys.py`,
  `instructor/anti-cheating.md`, `instructor/CTFd-SETUP.md`, `instructor/GRADEBOOK.md`,
  `instructor/ctfd/challenges.yml`, `instructor/exams/week19-final-ctf-capstone-ctf-answers.md`,
  `instructor/exams/item-bank.md`, `instructor/research/`
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement:
  [ETHICS.md](../../ETHICS.md)

## 9. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **The demo block does not fit the largest cohorts.** `AGENDA.md` gives 90 min (2:30–4:00); a strict live 10-min-demo + 5-min-Q&A format would be **15 min/team → 6 slots**, which cannot seat the ~27–60 teams N≈80–120 (`AGENDA.md`) implies in teams of 2–3 | **Resolved by `AGENDA.md`:** each team submits a pre-recorded video walkthrough before the session (graded asynchronously on the project rubric), and the in-class block is a **3-minute live Q&A per team**, which fits ~30 teams in 90 min. Above ~30 teams: run parallel rooms with a second assessor, or split the Q&A across the Week 16 studio and Week 19 (`AGENDA.md` §*Week 19*) |
| **Five-way port-8080 collision.** W4, W5, W6, W10 (`vulnerable-api`) and `project/starter-app` all publish 8080; a team wants several up at once | Brief at 0:00–0:10: `docker compose down` one before the next, or override the **left** side of the ports mapping. The Flask apps listen on 5000 *inside* the W4/W5/W6/W10 containers — do not republish 5000 (macOS AirPlay squats 5000, not 8080). W10's `solution-api` already takes 8081; W14 uses 6000/6001; CTFd uses 8000 |
| **Burp on its default listener.** The Week 6 worksheet's optional Burp step proxies through `127.0.0.1:8080` — the same port the targets publish | Move either Burp's listener or the target's published port |
| **Missing `.env` → no per-student flag.** Verified: with no `.env`, compose renders `FLAG_*: null` in all four seeded folders and the app falls back to its committed placeholder | `docker compose config` in W4, W6, W10 and W14 the day before; treat a placeholder flag on a sheet as a seeding failure, not cheating |
| **`seed_flags.py` cannot find the curriculum monorepo** — the shim `sys.exit`s with `ERROR: curriculum monorepo not found` and generates nothing | Run `gen` the **day before**; the sibling `KOSEN69 - curriculum` directory must be present. `check_flag_keys.py` (same shim pattern) is the cheap pre-flight |
| **Salt mismatch** between `gen` and `verify` — attribution silently returns nothing | Record this cohort's `FLAG_SALT` alongside the `flags.csv` it produced; export the same value before `verify` |
| **W11 will not link on a macOS host.** The Makefile's own note: `-z execstack` and `-no-pie` are GNU ld / Linux flags, so "on macOS the *link* step of these targets may fail"; `make syntax` still works. Apple clang also ships no libFuzzer runtime (`labs/toolbox/README.md`), which is challenge 8 | Have `softsec-toolbox` **built before the day** and the run line on a slide: `docker run -it --rm --cap-add=SYS_PTRACE --security-opt seccomp=unconfined -v "$PWD":/work -w /work softsec-toolbox`. `--cap-add=SYS_PTRACE` + relaxed seccomp are what make `gdb`/ASan work |
| **Challenge 7's flag needs a manual export.** `vuln.c:47` reads `FLAG_PWN`, but there is no compose to inject it | Either instruct `export FLAG_PWN=…` before `./vuln`, or accept that challenge 7 is attributed by evidence and viva like 3/8/9/10/12 |
| **W12/W13 need the network and the Docker socket.** `sca_scan.sh`, `sign.sh` and `scan.sh` run `aquasec/trivy:latest` with `-v /var/run/docker.sock:/var/run/docker.sock`, and Trivy fetches its vulnerability DB | Pre-pull `aquasec/trivy:latest` and warm the DB the day before. A locked-down machine that forbids socket mounts cannot run these — check in the target check, not at 1:00 |
| **Cosign needs a browser OIDC flow and registry push access** — `sign.sh` says so itself, and calls it "a guided demo, not an offline step" in class | Do not gate challenge 9 or a demo on live keyless signing. Accept a previously produced signature + the verification command as the evidence (`week16-capstone/worksheet.md` Part 3 A, deliverable 5) |
| **PyPI reachability at start-up.** W4/W5/W6/W10 `pip install flask` (W6 also `pyjwt`, W14 `flask`) at container start; a whole room starting at once needs the network | Pre-pull `python:3.12-slim`; keep a USB `docker save`/`docker load` copy; use the 0:00–0:10 target check to surface failures before the clock matters |
| **CTFd unavailable, or never deployed for this cohort** | The board is engagement only; the submission of record is the Form / Classroom ([SUBMISSION.md](../../SUBMISSION.md)), and `ctf.md`'s submission table works on paper |
| **The CTFd board and the paper disagree** — different point values, "Raid the API" split in two, an extra "Capture the Hash", and a 15th "Boss: Breach NoteVault" that is not on the paper | Announce at 0:00 which board is graded (the paper is), and either hide the extras or state that they score participation only |
| **NoteVault is not hardened for shared hosting.** `instructor/PLATFORM-ROADMAP.md` records that `project/starter-app/app.py` runs with Flask `debug=True` — an active Werkzeug console — and must be turned off before any lab is baked for shared multi-tenant spawning | Keep NoteVault on the team's own machine for the demo, as the delivery model already assumes; do not stand it up on a shared host for this session |
| **A team's Docker will not run at all** | No spare-machine provision is recorded in this repository — decide and record it: ⬚ |
| **Build artefacts left behind.** `make` in `labs/week11-memory-safety-exploitation` produces `vuln`, `vuln-*` and `fuzz` | `make clean`, or delete them — the curriculum monorepo's parity gate compares every file in the lab directory |

**If it fails mid-session — decision order**

1. **Network drops.** Solving is local and the targets are already up; keep going. Hold submissions
   and collect `ctf.md`'s table on paper at 2:30, transcribe afterwards. Challenges 9 and 10 are the
   exception — they depend on Trivy's DB fetch; note the outage against those items for partial credit.
2. **One target dies for one team.** The twelve challenges are independent — they lose that item's
   points, not the paper. Note it against their sheet.
3. **The Form / CTFd dies.** The paper table becomes the record; nothing else changes.
4. **A team's pre-recorded video is missing or will not play.** The pre-recorded format removes
   the live-exploit-fails failure mode from this block — there is no live attack segment left to
   fall back from. A missing/unplayable video is a missing deliverable against `project/README.md`'s
   rubric, not a live-demo contingency; run the 3-minute Q&A anyway on whatever artefacts the team
   can show and record the gap for marking. Exactly how the rubric penalizes a missing video: ⬚.
5. **Widespread failure to start targets inside the first 10 minutes.** That is exactly what the
   0:00–0:10 target check exists to expose. The repository defines no fallback adjustment to the
   150-minute window, and this is the last session of term so there is nothing to postpone into —
   the decision and its justification are the instructor's, and must be recorded: ⬚.

## 10. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per block (vs. plan) — did the CTF hold to 150 min and did every team demo: ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Challenge with the lowest solve rate, and what that says about the week it came from: ⬚
- Integrity flags raised by `seed_flags.py verify` / the NoteVault `TEAM_ID` marker, and how each resolved: ⬚
- Anything to change before this week runs again: ⬚
