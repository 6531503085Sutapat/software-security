# Lesson Plan — Week 16: Capstone Studio & CTF Warm-up

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 16 · ⬚ |
| **Contact time** | 300 min (course specification §1 records 2 lecture + 3 laboratory hours; `AGENDA.md` runs Week 16 as one continuous studio block — its per-week table gives lecture "—" and lab 300) |
| **Lab folder** | `labs/week16-capstone` — `README.md`, `worksheet.md`, `scrimmage.md`; it ships no target of its own |
| **Slides** | `slides/week16.md` — studio deck, not a teaching deck |
| **Type** | **Capstone studio — no new content.** Project work-in-progress + practice CTF |
| **Targets** | The teams' own term-project builds (`project/README.md`, default `project/starter-app` — *NoteVault*) plus the prior weeks' lab targets used by `scrimmage.md` |
| **Standards** | `worksheet.md` header: "All prior weeks + OWASP Top 10 (2025) — https://owasp.org/Top10/2025/ ; CWE mapping required throughout". Week 16 introduces no ids of its own |
| **CLOs addressed** | **CLO1** model · **CLO3** remediate · **CLO5** evaluate & communicate (course specification §6, row 16) |

---

## 1. Session objectives

This is a studio, not a lecture. What the session is designed to produce:

**Knowledge (K)**
- K1 — State the team's project **top-3 risks** and the STRIDE/attack category each falls under (`worksheet.md` Part 2, Q1).
- K2 — Give the headline vulnerability's **CWE id** and **OWASP 2025** category, plus a one-sentence root cause (Part 2, Q2).
- K3 — Explain what the team's **SBOM** covers, how it was generated, and what they would do if a dependency in it got a new CVE next week (Part 2, Q3).
- K4 — Explain how the build artifact is **signed** and how a consumer verifies the signature (Part 2, Q4).
- K5 — Name which **Week 15 CI gate(s)** — Semgrep / Trivy / Gitleaks, fail-closed on HIGH/CRITICAL — the pipeline enforces, and describe what a failing build looks like (Part 2, Q5).

**Skills (P)**
- P1 — Deliver the 10-minute demo to the segment structure in `worksheet.md` §3B: Context (0:00–1:30) → **Attack** (1:30–4:30) → **Root cause** (4:30–6:30) → **Fix + verify** (6:30–9:00) → Supply chain (9:00–10:00), then handle 5 minutes of Q&A.
- P2 — Re-run the team's own exploit against the patched build, live, and show it blocked (§3B, 6:30–9:00).
- P3 — Peer-review another team against the seven criteria of `worksheet.md` §3C, scoring each 1–5, and convert those scores into a written punch-list.
- P4 — Stand up prior weeks' targets unaided and capture flags/proof on the `scrimmage.md` board, recording per challenge the **flag/proof + payload/command + one-line mitigation**.
- P5 — Say, out of the six deliverables in `worksheet.md` §3A, exactly which are done, which are partial, and who owns the remainder before Week 19.

**Attitude (A)**
- A1 — Demo the attack → root cause → fix **only** against the team's own term-project application or the provided practice-CTF targets (`worksheet.md` ethics note), under [ETHICS.md](../../ETHICS.md).
- A2 — Show identity-stamped evidence — `whoami` / login email / student ID plus a timestamp on every screenshot and diagram (`worksheet.md`, *Evidence & Integrity*).
- A3 — Take peer criticism as a punch-list to work, not a verdict to argue with; give criticism the same way.
- A4 — Treat AI-generated security code as something to be verified, not trusted (`worksheet.md`, *Audit the AI*).

## 2. Key ideas (the through-line)

Everything the term taught in isolated weeks now has to hold together in **one** application the
team owns. A finding is not finished when the exploit works; it is finished when the root cause is
named (CWE + OWASP 2025), the fix is in a commit, the original attack has been re-run and fails,
the dependency inventory that shipped alongside it is known (SBOM), the artifact is signed, and a
pipeline gate will fail the build if any of it regresses. That chain — *attack → root cause → fix →
prove → keep it fixed* — is what `worksheet.md` §3B asks the team to narrate in ten minutes, and it
is what the Week 19 rubric marks.

Today's second job is calibration. `scrimmage.md` is the same shape as the Week 19 tournament,
"lighter and with hints — so teams calibrate strategy, division of labor, and the submit format
before it counts". A team that discovers on the day of the final that nobody knows how to stand up
the Week 11 binary has lost points to logistics, not to difficulty.

## 3. What teams bring in, and what they leave with

**Coming in — the six deliverables** (`README.md`, *Bring*; `worksheet.md` §3A). By the
`project/README.md` timeline these are all past due at Week 14, so today is a check, not a start:

| # | Deliverable | Evidence to show (`worksheet.md` §3A) | Timeline milestone (`project/README.md`) |
|---|---|---|---|
| 1 | **Threat model** | Data-flow diagram + trust boundaries; top risks ranked (STRIDE) | Week 7 |
| 2 | **Vulnerability report** | Each finding mapped to **CWE + OWASP 2025**, with severity and PoC | Week 11 (draft) |
| 3 | **Fixed code** | Before/after diff for each finding; root cause noted | Week 14 |
| 4 | **SBOM** | Machine-readable (CycloneDX / SPDX) covering all dependencies | Week 14 |
| 5 | **Signed artifact** | Signature + the exact verification command a consumer runs | Week 14 |
| 6 | **CI pipeline** | Security gate (Week 15 style) that **fails closed** on HIGH/CRITICAL; link to a run | — |

Plus, from `README.md`: **the project runnable** (work-in-progress), and **a 10-minute demo +
5-minute Q&A** prepared.

**Leaving with** — four artefacts, all produced during the session:

| Artefact | Produced in | Source |
|---|---|---|
| A written **punch-list** of gaps, with an owner per item | WIP review block | `slides/week16.md` speaker note: "Peer feedback in writing → the presenting team gets a punch-list. This is the main value of the session." |
| **Peer scores** — 7 criteria × 1–5 | WIP review block | `worksheet.md` §3C |
| A **ticked §3A checklist** showing which of the six deliverables are real | WIP review block | `worksheet.md` §3A |
| A **scrimmage retro**: what slowed us down, and who owns what in Week 19 | End of the CTF block | `scrimmage.md`, *After the scrimmage*; `worksheet.md` Part 4 Q3 |

**Instructor, before class.** Bring every scrimmage target up once on a representative machine the
day before (see §8 — three of the nine are not `docker compose up`). Pre-pull `python:3.12-slim`
and `aquasec/trivy`. Decide the pod split and the rotation order (§4.2) from the actual team count.
Confirm whether the CTFd scoreboard is running — `AGENDA.md` hedges it as "if running", while
`scrimmage.md` promises a live leaderboard.

## 4. Studio timetable — 300 min

The four block boundaries below are `AGENDA.md`'s (*Week 16 — Capstone Studio (300 min)*) and are
fixed. Everything finer is derived, and each derivation names its arithmetic.

| Time | Block | What happens | Source |
|---|---|---|---|
| 0:00–0:10 | **Studio stand-up** | Every team, standing, 60 seconds or less: what is demo-ready, what is broken, what you want from the room today. Instructor records the "broken" column — it is the triage list for §7 | Derived: taken *out of* the 0:00–2:00 block, leaving 110 min |
| 0:10–1:55 | **WIP review slots** | 7 × 15 min, run in parallel pods (§4.2 Variant B; single strand under Variant A). Each slot runs the `worksheet.md` §3B clock; peer team scores §3C live | Derived: 110 min ÷ 15 min per team (`worksheet.md` §3B) = 7 slots + 5 min slack |
| 1:55–2:00 | **Punch-list handover** | Reviewing teams hand the presenting team the written punch-list; instructor collects the §3A checklists | Derived from the same block |
| 2:00–2:15 | **Break** | | `AGENDA.md` |
| 2:15–2:25 | **Scrimmage rules + target check** | Read out the submit format; every team proves at least one target is up before the clock starts | Derived, mirroring `AGENDA.md`'s Week 9 CTF line ("0:00–0:10 rules + target check") |
| 2:25–4:30 | **Practice CTF tournament** | The `scrimmage.md` board, cross-team, live leaderboard, first-blood bonus per challenge | Derived: the remainder of `AGENDA.md`'s 2:15–4:45 scrimmage block, which `scrimmage.md` budgets at "~150 min" |
| 4:30–4:45 | **Scrimmage retro** | "What slowed you down? Who owns what in Week 19?" | `scrimmage.md`, *After the scrimmage* |
| 4:45–5:00 | **Feedback + finalise the checklist** | Each team states one §3A item it will close before Week 19 and who owns it; instructor confirms the Week 17/18/19 sequence | `AGENDA.md` |

> `worksheet.md`'s title says "(4 hrs)" while `AGENDA.md` budgets 300 min. Plan to `AGENDA.md`; the
> worksheet's own parts are homework-completable (see §6).

### 4.1 Why the demos must run in parallel

Straight arithmetic, all of it repo-sourced:

- `AGENDA.md` gives the demo block **120 min**; `worksheet.md` §3B gives **15 min per team**
  (10 demo + 5 Q&A) → **8 slots**, and 7 once the stand-up is taken out.
- `AGENDA.md` puts the cohort at **N≈80–120**; `project/README.md` and `syllabus.md` §*Teams &
  Houses* put project teams at **2–3** → on the order of **27–60 teams**.
- Actual cohort size and team count for this cohort: ⬚.

Unless the team count for this cohort is ≤ 7, a single plenary strand cannot seat everyone. Two
variants:

- **Variant A — plenary.** Use when the team count is ≤ 7. One strand, the table in §4 as written,
  every team seen by the instructor.
- **Variant B — parallel pods (the default at N≈80–120).** Pods = ⌈teams ÷ 7⌉, so the 27–60 teams
  above imply **4–9 pods**; the exact pod count and teams-per-pod for this cohort are ⬚. Each pod
  runs its own 15-minute slots on the §3B clock, in a corner of the room or a breakout space.
  Within a pod, the non-presenting teams are the peer reviewers. The instructor rotates (§4.2).

Pods are drawn **within a House** where possible — Houses are the persistent mixed-ability grouping
project teams nest inside (`syllabus.md`, *Teams & Houses*), so the peer reviewers already know each
other, and cross-House copying is not being invited.

### 4.2 Instructor rotation

The instructor cannot sit through every slot in Variant B. Rotate on the §3B clock, one whole
15-minute slot per pod, and make the rotation **visible** — teams should know which slot the
instructor will be in theirs, because that is the slot in which they ask their hardest question.

| Rotation | Time | Pod visited | Instructor's job in the slot |
|---|---|---|---|
| R1 | 0:10–0:25 | Pod 1 | Sit the full slot. Ask one unscripted follow-up — the `project/README.md` deliverable 6 style: *"why this fix and not X?"* This is the same live-viva spirit the Week 19 demo is graded under |
| R2 | 0:25–0:40 | Pod 2 | As R1 |
| R3 | 0:40–0:55 | Pod ⬚ | As R1 |
| R4 | 0:55–1:10 | ⬚ | As R1 |
| R5 | 1:10–1:25 | ⬚ | As R1 |
| R6 | 1:25–1:40 | ⬚ | As R1 |
| R7 | 1:40–1:55 | Triage sweep | Do not sit a slot. Walk the §7 triage list from the stand-up: the teams that said "broken" |

Fill the pod column from the actual pod count; with more pods than rotations, prioritise the teams
that reported a broken deliverable at stand-up, and cover the rest from their written punch-lists.

**Rotation discipline.** Pods keep running while the instructor is elsewhere — the peer review is
the primary mechanism, not a filler. Leave each pod a printed §3C rubric and a timer instruction:
slots start on the quarter-hour whether or not the previous team finished.

## 5. The work-in-progress review

### 5.1 What is checked

Two instruments, both already in `worksheet.md`, used together:

**(a) The six-deliverable checklist — §3A.** Binary, per deliverable, and checked against the
*evidence*, not the claim. "We have an SBOM" is not a tick; a machine-readable CycloneDX/SPDX file
covering all dependencies, shown on screen, is. Likewise deliverable 5 is not ticked without **the
exact verification command a consumer runs**, and deliverable 6 is not ticked without **a link to a
run** where the gate failed closed on a HIGH/CRITICAL finding.

**(b) The peer-review rubric — §3C**, scored 1–5 on each of seven criteria:

| Criterion | 1 (weak) → 5 (strong) |
|---|---|
| Threat model completeness | Missing boundaries → thorough, ranked, realistic |
| Vulnerability mapped to CWE/OWASP | Vague → precise id + accurate severity |
| Exploit clarity | Hand-wavy → clear, reproducible PoC |
| Remediation quality | Superficial → root-cause fix, re-tested |
| SBOM + signing | Absent → complete + verifiable |
| Pipeline / fail-closed | None → gate fails closed on HIGH/CRITICAL |
| Demo & Q&A | Unclear → confident, handles tough questions |

The four rubric criteria that most often score low without the team noticing are the last four —
they are exactly the deliverables due at Week 14 and the ones a demo can talk around. Insist the
**Fix + verify** segment (§3B, 6:30–9:00) is *shown*, not described: patch on screen, attack re-run,
failure visible.

### 5.2 The feedback format teams receive

`slides/week16.md` is explicit that peer feedback goes to the presenting team **in writing, as a
punch-list**, and calls it the main value of the session. One sheet per presenting team, filled by
the reviewing team during the slot and handed over at 1:55:

```
PUNCH-LIST — team: ______________  reviewed by: ______________  date: ______

§3C scores (1–5): threat model __ · CWE/OWASP __ · exploit clarity __ ·
                  remediation __ · SBOM+signing __ · pipeline __ · demo/Q&A __

§3A checklist:   1 threat model ☐  2 vuln report ☐  3 fixed code ☐
                 4 SBOM ☐  5 signed artifact ☐  6 CI pipeline ☐

| # | Gap observed (one line)            | Fix before Week 19 | Owner | Done ☐ |
|---|------------------------------------|--------------------|-------|--------|
| 1 |                                    |                    |       |        |
| 2 |                                    |                    |       |        |
| 3 |                                    |                    |       |        |

One thing this team does better than us: ______________________________________
```

Three rules that make the format work:

1. **Every gap gets a named owner and a date.** The owner column is the same question
   `scrimmage.md`'s retro asks ("who owns what in Week 19?") — ask it while the gap is fresh.
2. **Gaps are phrased against a rubric line**, not as taste. "Deliverable 5 has no verification
   command" is actionable; "supply chain felt thin" is not.
3. **Cap it at three.** A punch-list of twelve items is a punch-list of none.

The presenting team's own §3A checklist, the punch-list and the peer scores are all inputs to
`worksheet.md` Part 4 (*Reflection*), which is submitted afterwards.

## 6. CTF warm-up for the Week 19 tournament

`scrimmage.md`: teams of 2–4, **ungraded** ("bragging rights + a leaderboard"), live leaderboard,
**first-blood bonus per challenge**, sandbox only. Submit per challenge: **flag/proof + payload/command
+ one-line mitigation** — the identical three-column format the Week 19 paper
(`labs/week19-final-ctf-capstone/ctf.md`) requires. Drilling the submit format is half the point.

> Team size differs by document: `scrimmage.md` says teams of 2–4 for the scrimmage;
> `project/README.md` and `syllabus.md` put *project* teams at 2–3. Today's scrimmage teams need not
> be the project teams — but the retro is more useful if they are.

### 6.1 The board (`scrimmage.md`) — and how each target actually starts

`scrimmage.md` says "Challenges are drawn from the term's lab targets (`docker compose up` each)".
That is true of six of the nine. The last column is the correction; brief it at 2:15–2:25.

| Pts | Challenge | Target | Hint (as printed) | How the target actually starts |
|---:|---|---|---|---|
| 10 | SQLi login bypass | week04 | username not parameterized | `docker compose up` in `labs/week04-injection` → host **8080** |
| 10 | Stored XSS | week05 | raw comment render | `docker compose up` in `labs/week05-xss-client-side` → host **8080** |
| 15 | IDOR + forged JWT chain | week06 | read others' orders, then `alg:none` to admin | `docker compose up` in `labs/week06-authn-authz` → host **8080** |
| 15 | BOLA + mass assignment | week10 | id in URL; `is_admin` in body | `docker compose up` in `labs/week10-api-security` → vulnerable API host **8080**, solution API host **8081** |
| 20 | ret2win | week11 | offset 72 → `&win` | **No compose file** — `make` in `labs/week11-memory-safety-exploitation` (targets `vuln`, `vuln-hardened`, `syntax`, `clean`); use `labs/toolbox` for clang/gdb |
| 10 | Find the vulnerable dep | week12 | `trivy fs` | **No compose file** — `bash sca_scan.sh`, or `docker run --rm -v "$PWD:/src" aquasec/trivy fs /src` |
| 15 | Cloud misconfig hunt | week13 | `trivy config` + IAM `*:*` | **No compose file** — `bash scan.sh`, or `docker run --rm -v "$PWD:/src" aquasec/trivy config /src` |
| 10 | Jailbreak the chatbot | week14 | override the system prompt | `docker compose up` in `labs/week14-ai-llm-security` → insecure **6000**, guarded **6001** |
| 15 | **Boss:** chain two bugs on the NoteVault starter | project | recon → exploit → escalate | `cd project/starter-app && export TEAM_ID=<your-team-name> && docker compose up` → host **8080** |

Board total: **120 points**. Difficulty is mixed by design; the 20-point `ret2win` and the 15-point
boss are where teams that have divided labour badly will stall.

### 6.2 Running it

- **Sequence the 8080 targets.** Five of the nine want host port 8080. `docker compose down` one
  before starting the next, or override the **left** side of the `ports` mapping (see §8).
- **Order for a team of four**, if they ask: put two people on the four web/API challenges (they
  share the port and must be sequenced anyway), one on week12/week13 (no port, tool-driven), one on
  week14, then converge everyone on the boss. Say this at the retro if nobody found it.
- **Hints are on the board deliberately.** `scrimmage.md` is the lighter, hinted version of Week 19
  on purpose. Week 19's `ctf.md` states only the goal — say so, so nobody calibrates on hints.
- **Solutions exist**: "Solutions live in each lab's `solution_*`/`attack.md`". Point a fully stuck
  team at them near the end rather than letting the block end in zero — nothing today is graded.
- **Leaderboard.** If CTFd is up, run it there. If not, tally on the whiteboard and enter CTFd
  Awards afterwards (`instructor/CTFd-SETUP.md` §6) — the points feed the Houses engagement layer,
  which `syllabus.md` states is not graded.

### 6.3 The retro (4:30–4:45) — three questions

1. `scrimmage.md`: **what slowed you down?** Force a concrete answer — a target that would not
   start, a technique nobody had practised, or duplicated effort.
2. `scrimmage.md`: **who owns what in Week 19?** Write the names down; this is the same column as
   the punch-list owner.
3. `worksheet.md` Part 4 Q3: **which category was hardest, and what will you drill before Week 19?**
   Map the answer onto Week 17's mock CTF so the drill has a scheduled slot.

Close by naming what changes in Week 19: it is graded, it is 150 min for 12 challenges over 150
points (`labs/week19-final-ctf-capstone/ctf.md`), the hints are gone, and the project demo is scored
separately.

## 7. Support for teams that are behind

"Behind" has a repo definition today — the `project/README.md` milestone table. Triage at the
stand-up (0:00–0:10) and assign a tier; the tier decides what the team spends the 120-minute block
on.

| Tier | Definition (`project/README.md` milestones) | What they do today |
|---|---|---|
| **Green** | All six §3A deliverables present; demo rehearsed | Normal slot. Push them: ask the unscripted follow-up, and set the punch-list at polish level (severity accuracy, Q&A handling) |
| **Amber** | Threat model (W7) and vuln report draft (W11) exist; the W14 group — remediation, SBOM, signed artifact — is partial or missing | Demo the part that works, then **spend the rest of their own slot building**, in the room, with the peer team watching. SBOM and signing are the two most recoverable in a session: `docker run --rm -v "$PWD:/src" aquasec/trivy image --format cyclonedx -o /src/sbom.json myapp:lab` then `cosign sign` / `cosign verify` (`labs/week12-supply-chain/README.md`), and `labs/week12-supply-chain/sign.sh` |
| **Red** | No working exploit against their own app, or the app will not run | Drop the demo for today. Reset them onto the default target: `cd project/starter-app && export TEAM_ID=<your-team-name> && docker compose up`. Point them at `project/starter-app/README.md`'s *Suggested attack surface* — login, register, note, search, admin and export endpoints; the session cookie; `requirements.txt`; the `Dockerfile` — with seeded logins `alice / alicepw` and `admin / admin123`. One reproducible finding with a CWE/OWASP mapping by 1:55 is the target |

Three further supports, all cheap:

- **The scrimmage is the recovery path.** A Red team that lands the boss challenge — "chain two bugs
  on the NoteVault starter", the same codebase as their project — has just produced the PoC their
  vulnerability report was missing. Say this explicitly at 2:15.
- **The pipeline is the smallest deliverable.** `labs/week15-devsecops-pipeline/security-ci.yml` is
  a working starting point for §3A deliverable 6; a team with nothing there can have a failing-closed
  gate before the end of the day.
- **Milestone dates are not the mark.** `project/README.md`'s rubric scores the artefacts, not their
  punctuality; the Week 19 demo is the graded event. Tell Amber and Red teams that, and then hold
  them to the punch-list.

**Peer-contribution fairness.** If the stand-up or the rotation exposes a team where one member is
carrying everything, note it now — `project/README.md` scales each member's mark by the private
peer-contribution rating (typically ×0.8–1.1), and an unjustified low score is discussed before it
is applied. Raising it in Week 16 gives the team five weeks to fix the split; raising it at the
Week 19 submission does not.

## 8. Assessment for this week

Three regimes run today and they must not be blended.

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 16 (Parts 1–4 + *Audit the AI* + *EiPE/Prompt*) | Team answers to the five Part 2 questions, the §3A checklist, the peer review, Part 4 reflection | K1–K5, P3, P5, A2, A4 | Part of the 30% worksheet component (course specification §4) |
| Today's WIP demo | Live attack → root cause → fix walkthrough | P1, P2, A1 | **Ungraded.** `README.md`: "The graded final presentation + full CTF tournament happen in **Week 19**"; `slides/week16.md`: "Demo format (today, ungraded)" |
| Practice CTF scrimmage | Flags/proof + payloads + mitigations | P4 | **Ungraded** — `scrimmage.md`: "Ungraded (bragging rights + a leaderboard)". Points feed the non-graded Houses leaderboard |
| Term project (graded at Week 19) | The six deliverables + the graded demo | CLO1, CLO3, CLO4, CLO5, CLO6 (course specification §4, term-project row) | 15% of the final mark, scored on `project/README.md`'s own 100-point rubric, with each member's mark scaled by peer contribution |

Two separate 100-point rubrics exist and grade different things — keep them apart:

| Rubric | Lives in | Weighting |
|---|---|---|
| **Worksheet 16** | `labs/week16-capstone/worksheet.md` | Threat model 15 · Exploitation 20 · Remediation 20 · SBOM & signing 15 · CI pipeline 15 · Demo & Q&A 15 |
| **Term project** | `project/README.md` | Threat model 20 · Vulnerability findings 25 · Remediation 25 · Supply-chain hardening 15 · CI pipeline 10 · Presentation & report 5 |

No weekly quiz this week — `AGENDA.md`'s per-week table gives Week 16 a quiz column of "—", and the
retrieval quizzes belong to teaching weeks.

## 9. Materials

- Lab: `labs/week16-capstone/` — `README.md`, `worksheet.md`, `scrimmage.md`
- Slides: `slides/week16.md`
- Project: `project/README.md` · `project/REPORT-TEMPLATE.md` · `project/starter-app/` (*NoteVault*)
- Scrimmage targets: `labs/week04-injection` · `labs/week05-xss-client-side` ·
  `labs/week06-authn-authz` · `labs/week10-api-security` ·
  `labs/week11-memory-safety-exploitation` · `labs/week12-supply-chain` ·
  `labs/week13-cloud-container` · `labs/week14-ai-llm-security` · `project/starter-app`
- `labs/toolbox` — clang 19 + libFuzzer/ASan, gdb, nmap, sqlmap, python3, git, curl; built once with
  `docker build -t softsec-toolbox labs/toolbox`
- Week 15 pipeline reference for §3A deliverable 6: `labs/week15-devsecops-pipeline/security-ci.yml`
  and `README-pipeline.md`
- Instructor-side: `instructor/CTFd-SETUP.md` (§5 Houses/Teams mode, §6 Awards for non-flag games) ·
  `instructor/anti-cheating.md` · `instructor/seed_flags.py`
- Forward pointer: `labs/week19-final-ctf-capstone/ctf.md` — the graded tournament this warms up for
- Printing list for the session: §3C rubric × one per reviewing team; the §5.2 punch-list sheet ×
  one per presenting team; the §6.1 board
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 10. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Host port 8080 is a five-way clash — worse than in Weeks 7 and 9.** `labs/week04-injection`, `labs/week05-xss-client-side` and `labs/week06-authn-authz` publish `8080:5000`, `labs/week10-api-security` publishes `8080:5000` (plus `8081:5001`), and `project/starter-app` publishes `8080:8080`. The scrimmage needs four of those *and* NoteVault for the boss challenge — and NoteVault may still be bound from a team's own demo in the morning block | Brief it at 2:15–2:25: run **one 8080 target at a time**, `docker compose down` before the next, or override the **left** side of the `ports` mapping. The nine challenges are independent, so a sequence works: week04 → week05 → week06 → week10 → NoteVault. Note that macOS AirPlay squats on **5000**, which here is the *container-side* port and is therefore not the cause of this clash. Have teams `docker compose down` their demo stack at the break |
| **Three of the nine challenges have no `docker compose up`**, contradicting `scrimmage.md`'s "(`docker compose up` each)". A team following the file literally loses 45 of the 120 points to a missing command | Correct it on the board at 2:15–2:25 using §6.1: week11 is `make`; week12 is `bash sca_scan.sh`; week13 is `bash scan.sh` |
| **Apple-Silicon platform mismatch kills the 20-point ret2win challenge.** `scrimmage.md`'s hint is "offset 72 → `&win`"; on an arm64 host the build is aarch64 and that offset and the addresses do not apply. The `Makefile` also warns that `-z execstack` / `-no-pie` are GNU ld/Linux flags and the *link* step may fail on macOS | Run the build forced to amd64 under Rosetta (`docker run --platform linux/amd64 …`), as already documented in [`week11-memory-safety-exploitation.md`](week11-memory-safety-exploitation.md) §8, or use `labs/toolbox`. A team that cannot build should be told to skip it rather than burn 40 minutes — it is 20 of 120 ungraded points |
| **Trivy needs to pull an image and download a vulnerability database.** `trivy fs` (week12) and `trivy config` (week13) run from `aquasec/trivy`; a room of teams pulling the image and the DB at 2:25 on a weak network stalls two challenges at once | Pre-pull `aquasec/trivy` before the session and warm the DB cache on a representative machine; keep an offline image copy (`docker save` / `docker load`). `trivy config` is the more resilient of the two — it checks IaC/Dockerfile misconfiguration and is less DB-hungry than the CVE scan |
| **Port 6000 may not open in the demo browser.** `labs/week14-ai-llm-security/docker-compose.yml` publishes the insecure chatbot on **6000** and the guarded one on **6001**; Chromium-family browsers block a set of low ports outright | Pre-flight check the day before: confirm `http://localhost:6000` opens in the browser you will demo with. If it is blocked, override the **left** side of the `ports` mapping and tell teams the new port at 2:15 |
| **Cosign is not installed, or keyless signing needs network + OIDC.** `project/README.md` deliverable 4 requires the release artifact signed with Cosign, and `worksheet.md` §3A deliverable 5 wants the exact verification command — an Amber team trying to close that gap in-session hits an install and an interactive browser sign-in | Check `cosign version` on a representative machine beforehand. If keyless is not workable in the room, a team may show a key-pair signature plus the verification command; what §3A actually asks for is a signature and the command a consumer runs. `labs/week12-supply-chain/sign.sh` is the reference |
| **The CTFd leaderboard may not be up.** `AGENDA.md` hedges it as "if running" while `scrimmage.md` promises a live leaderboard and a first-blood bonus | Tally on the whiteboard during the scrimmage and enter CTFd Awards afterwards (`instructor/CTFd-SETUP.md` §6). Nothing today is graded on those points, so a missing scoreboard costs energy, not marks |
| **Duplicate flags in a team scrimmage are not an integrity event.** Lab flags are per *student* (`instructor/seed_flags.py`, seeded via `python3 ../../instructor/seed_flags.py env <STUDENT_ID> > .env`), but the scrimmage is played in teams of 2–4 and is ungraded — teammates will legitimately submit each other's values | Do not escalate a duplicate today. `scrimmage.md` accepts "flag/proof", so proof is sufficient; `labs/week05-xss-client-side/docker-compose.yml` injects no `FLAG_*` at all, so the Stored XSS challenge is scored on proof by construction. Reserve `seed_flags.py verify` for the graded Weeks 9 and 19 (the two CTF-format assessments; Week 18 is the written final exam and issues no flags) |
| **More teams than slots** — 120 min ÷ 15 min gives 8, and the cohort is N≈80–120 in teams of 2–3 (§4.1) | Run Variant B pods (§4.2). If even pods overflow, cut the demo to the §3B *Attack* + *Fix + verify* segments (1:30–4:30 and 6:30–9:00 — 3:00 + 2:30 = 5½ min of demo) and keep the full 5-minute Q&A only for the pod the instructor is sitting in |
| **A team demos against something that is not theirs.** `worksheet.md`'s ethics note limits today's demos to the team's own term-project application or the provided practice-CTF targets | State the boundary at the stand-up. A demo against anything else stops there and is handled under [ETHICS.md](../../ETHICS.md) |
| **Peer review degenerates into praise.** Ungraded feedback between friendly teams tends to score 5s | Require a *number* on all seven §3C criteria and *three* punch-list lines with owners; a punch-list handed in with fewer than three gaps goes back to the reviewing team. The "one thing this team does better than us" line is where the praise goes |
| **A team's own app will not run at all in the room** | They present from a recorded fallback — `worksheet.md` §3B allows "(or recorded fallback)" for the Attack segment — and spend the rest of the slot on the environment, not the slides. Log it on the §7 triage list |

## 11. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per block (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Teams triaged Amber/Red at the stand-up, and whether they closed the gap by 1:55: ⬚
- Scrimmage challenges left unsolved by more than a third of the teams: ⬚
- Anything to change before this week runs again: ⬚
