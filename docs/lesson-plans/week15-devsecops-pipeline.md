# Lesson Plan — Week 15: DevSecOps — Putting It Together

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 15 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week15-devsecops-pipeline` |
| **Slides** | `slides/week15.md` |
| **Standards** | OWASP 2025 **A09 Security Logging & Alerting Failures** · **A10 Mishandling of Exceptional Conditions** (the scanners also cover A02/A03) · CWE-636 (fail open), CWE-532 (logging sensitive data), CWE-209, CWE-489, CWE-798 · CISA **"Secure by Design"** |
| **CLOs addressed** | **CLO4** operate security tooling across the SDLC · **CLO5** evaluate & communicate (course-spec §6). The recurring *Audit the AI* / *EiPE* + *Prompt Problem* parts carry **CLO5**, and *Evidence & Integrity* carries **CLO6** (course-spec §4). |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**

- K1 — Explain why each tool in `security-ci.yml` runs **twice** — a report step (`exit-code: "0"` / `|| true`, with an `if: always()` SARIF upload) then a gate step (`exit-code: "1"` / `--error`) — and why a single failing scan would *hide* the findings it just produced.
- K2 — Distinguish **fail-closed** from **fail-open**, and state why fail-open is **A10 / CWE-636**.
- K3 — Justify the least-privilege CI token `permissions: contents: read` / `security-events: write`, and say what a broad `write-all` token would put at risk.
- K4 — Explain why logging the token value would be **CWE-532**, and what to log instead (`reason=bad_token`, not the token) so a SIEM can still alert on it (**A09**).
- K5 — Name the three scanners and what each catches — **Semgrep** (SAST), **Trivy** (SCA + IaC/secret), **Gitleaks** (secrets + git history) — and the mapping in the `README-pipeline.md` §2 table (OWASP Top 10 rules · A03 / A02 · CWE-798).

**Skills (P)**

- P1 — Stand up `sample-service.py` and produce the structured `event=…` security log lines for `authn_failure`, `authz_failure` and `authz_success`.
- P2 — Read `/admin` in `sample-service.py` and explain why the broad `except Exception` returns **403, not the secret**, why `type(exc).__name__` (not the message) is logged (CWE-209), and identify the commented INSECURE variant that would make it fail *open*.
- P3 — Exploit a real fail-open: reach the insecure `/admin` with no `Authorization` header, capture the leaked `FLAG{devsecops_…}`, contrast it with the secure service's `403`, and quote the exact line in `insecure_service.py` that fails open.
- P4 — Wire `security-ci.yml` into a repo they own and show the three jobs (`semgrep`, `trivy`, `gitleaks`) running with SARIF appearing in the Security tab.
- P5 — Drive the gate green: no HIGH/CRITICAL findings and no secrets, by fixing or by documenting a justified, time-boxed exception — never a blanket ignore (`README-pipeline.md` §4).
- P6 — Make the gate say **no**: inject one planted defect on a PR (an outdated vulnerable dependency such as an old `urllib3`, a `chmod 777` in a Dockerfile, or a hard-coded token) and identify which job caught it and which `exit-code: "1"` / `--error` step enforced it.

**Attitude (A)**

- A1 — Run the security gate and every "Red team" bypass attempt **only against a repo they own** (their fork or a throwaway repo); never push deliberately-vulnerable code or planted secrets to shared or production repositories — under [ETHICS.md](../../ETHICS.md) and the worksheet's ethics note.
- A2 — Submit identity-stamped evidence (`whoami` / login email / student ID + timestamp) that is identifiably their own work, and be able to reproduce it live on request.
- A3 — Treat AI-generated security code and advice as something to be verified, not trusted.

## 2. Key ideas (the through-line)

This is the synthesis week: every tool the course used by hand — SAST in Week 2, SCA and image
scanning in Weeks 12–13, secret scanning in Week 2 — now runs automatically on every push and PR.
Two ideas carry the session. First, **a gate must be able to say no**: `|| true` everywhere makes
the gate decorative, so each scanner runs once to *report* (producing SARIF that uploads under
`if: always()`, even when the build is about to fail) and once to *gate* (`exit-code: "1"` /
`--error`, which turns the PR red). Second, **when something breaks, deny**. A09 and A10 are the
two halves of what happens after prevention fails: you cannot respond to what you never logged, and
an error path that grants access on exception (`except Exception:` → `panel="UNLOCKED"`) converts an
ordinary bug into an authentication bypass. The same endpoint appears twice in this lab — once
failing open and silent, once failing closed and logged — and the only difference is a `.get()` and
a log line.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop running (Week 1 *Lab 0*); skim the Week 14 recap.
  Bring a **GitHub repo you own** (a fork or a throwaway) with **Actions enabled**, plus `git`,
  Docker, and Python + Flask for the local service (worksheet Part 3 prerequisites).
- **Instructor, before class:** pre-pull `python:3.12-slim` so the room is not pulling it at once —
  `docker compose up` in the lab folder runs `pip install --no-cache-dir flask` on *every* start,
  which needs the network as well as the image. **Seed the per-student flag** before the session:
  `docker-compose.yml` passes `FLAG_DEVSECOPS` through to both services, and if it is unset both
  fall back to the hard-coded default in `insecure_service.py` — every student then submits the
  same flag and the integrity control fails silently. Confirm the local pair actually behaves:
  `curl -s localhost:8090/admin` with no header must return `panel: UNLOCKED` with the secret, and
  `curl -s localhost:8091/admin` must return `{"error":"forbidden"}` with a `403` (verified on the
  reference machine, 2026-07-26). Decide in advance which repository students will push
  `security-ci.yml` to, and confirm SARIF upload and the Code scanning alerts page behave as
  expected for **that** repository's visibility (see §8).
- **Prerequisite concepts:** what a CI job, a pull request and a build failure are; that an
  exception handler chooses what happens after a failure; and — from Weeks 2, 12 and 13 — what
  SAST, SCA, IaC scanning and secret scanning each look for.

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | ~10-min retrieval quiz on Week 14 (AI/LLM application security — "Gandalf Challenge" + tool poisoning); today's agenda. This is the **last weekly quiz** of the term | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concept | The whole course in one pipeline: SAST (Wk2) · SCA + image scan (Wk12–13) · secret scanning (Wk2) become *automated gates* instead of one-off scans, with **Secure by Design** as the default. Walk `security-ci.yml` on the projector: the three jobs, the least-privilege `permissions:` block, report-then-gate (`exit-code: "0"` + `if: always()` SARIF upload, then `exit-code: "1"` / `--error`), and SARIF → the GitHub **Security** tab. Close with the managed equivalent: GitHub Advanced Security (CodeQL code scanning, secret scanning + push protection, Dependabot), and SonarQube as a quality/SAST gate alongside | Lecture + live walk-through of `security-ci.yml` |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | **A09** — without logs you cannot detect or respond: log authn/authz failures and anomalies, alert on suspicious patterns. The defender's toolkit: NIDS (Snort / Suricata), HIDS (OSSEC), SIEM stack (Security Onion), and TAP (lossless) vs SPAN (cheap, drops under load). The alert confusion matrix: a **false negative** is the missed attack, but unsilenced false positives cause alert fatigue — tune, don't mute. When something does happen: NIST SP 800-86 **Collection → Examination → Analysis → Reporting**, order of volatility (memory → temp files → disk → logs), Windows Event **4625 / 4624**. **Real case:** the class supplies it — this is Worksheet 15 Part 4 Q2, "a real breach worsened by missing logging/alerting or by a fail-open error path". Instructor's own worked example: ⬚ (no breach is named in `slides/week15.md` or in the lab) | Lecture + short discussion: *"which control here would have changed the outcome?"* |
| 1:35–1:55 | Defences | **Fail closed** (A10): on error, deny — never bypass the check; never expose stack traces or secrets in errors. Diff the two halves of the target live: `insecure_service.py:46–49` (`except Exception:` → returns `panel="UNLOCKED"`, silently) against `secure_service.py:69–76` (`except Exception as exc:` → logs `type(exc).__name__`, returns `403`), and `USERS[token]` against `USERS.get(token)`; then the commented INSECURE variant at `sample-service.py:105–111`. Log the event, not the secret (`reason=bad_token` — CWE-532; `type(exc).__name__` not the message — CWE-209); `debug=False` because the Werkzeug debugger is an RCE vector (CWE-489). Close on vulnerability management: triage by severity and track to remediation with SLAs; fix or document a justified, time-boxed exception rather than blanket-ignoring (`README-pipeline.md` §4); coordinated disclosure, bug bounties, `security.txt` | Lecture with code-diff comparisons |
| 1:55–2:00 | Brief the game | 🔴🔵 "Break the Build" (Red vs Blue) — Blue builds the gate (Semgrep + Trivy + Gitleaks, fail on HIGH/CRITICAL, security logging that fails closed); Red submits PRs sneaking a vuln or secret past it; Blue scores per catch, Red per bypass | Instruction |

**Checks for understanding during lecture**

- After the core concept: cold-call — *"why must the gate FAIL the build, not just warn?"* (slide
  deck's own closing cold-call; the answer is in `README-pipeline.md` §3 — a warning-only gate is
  decorative).
- Before the break: one-minute paper — *"why does each tool have to run twice?"*

## 5. Laboratory — 180 min

This week has **three targets**, and they are not interchangeable — different files, different
ports, different install commands.

**(a) `sample-service.py` on `localhost:5001`** — bare Python, for Tasks 0 and 1:

```bash
pip install flask
python labs/week15-devsecops-pipeline/sample-service.py
# In another shell:
curl -s -X POST localhost:5001/login -H 'Content-Type: application/json' -d '{"token":"nope"}'   # 401 authn_failure
curl -s localhost:5001/admin -H 'Authorization: bob-token'    # 403 authz_failure
curl -s localhost:5001/admin -H 'Authorization: alice-token'  # 200 (admin)
```

**(b) the fail-open / fail-closed pair via Docker** — for Task 1b. `cd labs/week15-devsecops-pipeline && docker compose up`
spawns the **insecure** service on `:8090` (`insecure_service.py`) and the **secure** one on `:8091`
(`secure_service.py`); the compose file installs Flask itself with `pip install --no-cache-dir flask`.

```
curl -s localhost:8090/admin                                  # {"panel":"UNLOCKED","secret":"FLAG{devsecops_...}"}  <- fail OPEN
curl -s localhost:8091/admin                                  # {"error":"forbidden"}   (403)  <- fail CLOSED + logged
curl -s localhost:8091/admin -H 'Authorization: alice-token'  # still UNLOCKS for a real admin (anti-cheat)
```

**(c) GitHub Actions on a repo the student owns** — for Tasks 2–4, wired in per `README-pipeline.md` §1:

```bash
mkdir -p .github/workflows
cp labs/week15-devsecops-pipeline/security-ci.yml .github/workflows/security-ci.yml
git add .github/workflows/security-ci.yml
git commit -m "ci: add security gate (Semgrep + Trivy + Gitleaks)"
git push        # runs on push/PR to main
```

Each task submits the command / PR link, the relevant output or log lines / Actions step result, a
screenshot, and a 2–3 sentence note on the control involved, citing the A0x / CWE.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:15 | **Task 0 — Onboarding** (15 min) | Run the sample service; fire the three `:5001` curls above | Screenshot of the structured `event=…` security log lines for `authn_failure`, `authz_failure` and `authz_success` |
| 0:15–0:50 | **Task 1 — Logging & fail-closed** (35 min, A09/A10) | Read `/admin` in `sample-service.py`; explain why the broad `except Exception` returns **403, not the secret**, and why `type(exc).__name__` (not the message) is logged (CWE-209); identify the line that would make it fail *open* — the commented INSECURE variant | The log lines + a 2–3 sentence explanation of fail-closed vs fail-open |
| 0:50–1:15 | **Task 1b — Break the Build, live** (25 min, A10 / CWE-636) | `cd labs/week15-devsecops-pipeline && docker compose up`; as **Red**, hit the insecure admin route with **no** `Authorization` header — the fail-open path leaks the admin panel *and* the per-student flag; compare with `:8091` | The leaked `FLAG{…}`, the two contrasting `/admin` responses (`:8090` leak vs `:8091` deny), and the exact line in `insecure_service.py` that fails open |
| 1:15–1:50 | **Task 2 — Stand up the gate** (35 min) | Push `security-ci.yml`, open the Actions run, confirm the three jobs (`semgrep`, `trivy`, `gitleaks`) execute and SARIF appears in the Security tab | Screenshot of the Actions run + the Code scanning alerts page |
| 1:50–2:20 | **Task 3 — Blue team: pass the gate** (30 min) | Ensure the protected repo has no HIGH/CRITICAL findings and no secrets; fix or justify-and-document any (no blanket-ignore, per README §4) | Link to the passing run |
| 2:20–3:00 | **Task 4 — Red team: Break the Build** (40 min) | On a branch/PR, inject *one* planted defect (per README §5): an outdated vulnerable dependency (e.g. an old `urllib3`), a `chmod 777` in a Dockerfile, or a hard-coded token; open the PR and watch the matching gate step fail | Screenshot of the **failing** gate step + which job caught it (Trivy SCA / Trivy config / Gitleaks) and which `exit-code: "1"` / `--error` step enforced it |
| ⬚ (see note) | **Task 5 — Score Break-the-Build** (25 min) | One Blue point per finding the gate caught, one Red point per finding that slipped through; for any bypass, propose the rule that would have caught it | Scoreboard + one proposed gate improvement |
| carry-over | **AI-resilient tasks + micro-demo + submit** | *Audit the AI* (critique an AI-written exploit or fix, quote the wrong line, produce the verified version), *Explain-in-Plain-English*, *Prompt Problem*; 2–3 rotating students give a 2–3 min "show your exploit/fix"; everyone submits | Written answers (start in class, finish as homework); worksheet PDF → Classroom; code → GitHub; weekly quiz → Google Form |

**Timing note — the worksheet over-books this block, and that is a decision for you, not a silent trim.**
The worksheet's own budgets are Task 0 (15) + Task 1 (35) + Task 1b (25) + Task 2 (35) + Task 3 (30)
+ Task 4 (40) + Task 5 (25) = **205 min against a 180-min lab**, before the standard AI-resilient and
micro-demo/submit blocks. The table above runs Tasks 0–4 as written and leaves Task 5 unplaced (⬚)
because there is no honest slot for it. Pick one before the session and write it in:
- **run Task 5 as homework** — the scoreboard needs the Red/Blue results, which only exist after the PRs land; or
- **compress Tasks 2–4** — their budgets are dominated by Actions queue and scan wall-clock, not classroom
  work, and all three deliverables (Actions run screenshot, link to a passing run, failing-gate screenshot)
  are asynchronous: students can push in class and write up at home; or
- **drop Task 1b's in-class run** to a demo from the front (it is the only task duplicated by Week 12's
  flag workflow), recovering 25 min.
Tasks 0, 1 and 1b run entirely on the student's own machine and fit the first 75 minutes as written.
The AI-resilient tasks start in class and finish as homework, as the worksheet and
[AGENDA.md](../../AGENDA.md) already specify; the micro-demo can roll to the next week or be sampled by viva.

**Formative checkpoints.** If a student's Task 1b `curl` against `:8090` returns
`{"error":"forbidden"}`, they are on `:8091` — check the port before debugging anything else; the
same mistake in reverse makes the "secure" service look broken. Task 2 should be *pushed* as early
as possible even if the write-up comes later, because everything after it waits on an Actions run;
a student blocked on GitHub (no repo, Actions disabled, no network) should complete Tasks 0, 1 and
1b locally — run paths (a) and (b) above (`sample-service.py` on `:5001`, then the `docker compose`
pair on `:8090`/`:8091`) — and carry Tasks 2–4 forward (the week's README numbers its two run paths
differently). A student who
cannot get Task 3 green is usually being failed by the Semgrep gate rather than by Trivy (see §8).

## 6. Assessment for this week

Graded against Worksheet 15's own rubric (100 pts):

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 15 — Lecture questions (Part 2) | Written answers to Q1–Q5 | K1–K5 | 20 pts of the worksheet |
| Worksheet 15 — Tasks + evidence (Part 3) | Tasks 0–5 complete; PR/run links, log lines, screenshots | P1–P6, A2 | 40 pts of the worksheet |
| Worksheet 15 — Defense (gate + fail-closed) | Gate shown to fail closed on a planted defect; fail-closed path explained | K1–K2, P5–P6 | 25 pts of the worksheet |
| Worksheet 15 — Reflection (Part 4) | Control → A09/A10 (or A02/A03) → CWE mapping, real incident, best-mitigation argument | K2, K4, A3 | 15 pts of the worksheet |
| Weekly quiz (start of lecture) | Quiz score (Week 14 retrieval) | — | Part of the 10% quiz/participation component |
| *Audit the AI* + *EiPE / Prompt Problem* | Critique + plain-English + verified prompt | CLO5 (course-spec §4) | Within the Defense / Reflection score |
| Viva spot-check / micro-demo | Live reproduction and explanation | P1–P6 | Pass/flag for follow-up |
| Per-student flag (`FLAG_DEVSECOPS`) | Flag value tied to the individual student | A2 / CLO6 | Integrity control, not a mark |

The worksheet component is part of the 30% weekly-worksheet weight in the course spec. Partial
credit is available where a student explains the mechanism correctly but could not land the
exploit. Note that the worksheet also states an instructor auto-grader re-runs these exploits
against the student's hardened box: a pass requires that every bypass is blocked **and** a valid
admin token still works.

## 7. Materials

- Lab: `labs/week15-devsecops-pipeline/` — `README.md`, `README-pipeline.md`, `worksheet.md`,
  `security-ci.yml`, `sample-service.py`, `insecure_service.py`, `secure_service.py`,
  `docker-compose.yml`
- The repo's own live pipeline, offered by the week's README as the template to study:
  `.github/workflows/security-ci.yml`
- Slides: `slides/week15.md`
- References (from the week's README): OWASP Logging Cheat Sheet
  (<https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html>) ·
  GitHub Actions docs (<https://docs.github.com/actions>)
- Term project tie-in: apply this week's lesson to the [NoteVault project](../../project/README.md)
  where it fits
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| `pip install flask` (worksheet step B, Tasks 0–1) fails on a modern macOS/Homebrew Python with `error: externally-managed-environment` (PEP 668) — and bare `pip` may not exist at all (`command not found: pip`). Reproduced on the reference machine | Use `python3 -m venv path/to/venv` and install Flask inside it, as the error message itself instructs; or skip the host install entirely and reach the same fail-closed code through the compose path — `secure_service.py` on `:8091` carries the identical `/admin` logic |
| Port clash / wrong port. Three ports are in play (`5001`, `8090`, `8091`) and the two `/admin` services look alike. On macOS, ControlCenter/AirPlay squats **5000** (confirmed on the reference machine) — and `insecure_service.py` records that 8090 was chosen because ControlCenter squats **7000** | Keep the ports exactly as shipped; do not "tidy" `5001` to `5000`. Diagnose by response, not by memory: an unauthenticated `/admin` that returns `403` is `:8091`, one that returns `panel: UNLOCKED` is `:8090` |
| Image-pull / install stampede: `docker compose up` runs `pip install --no-cache-dir flask` on **every** start for **both** services, on top of pulling `python:3.12-slim` | Pre-pull `python:3.12-slim` before the session and keep a USB copy (`docker save`/`docker load`); warn students that the first `docker compose up` needs the network even when the image is cached |
| `FLAG_DEVSECOPS` not seeded. Both services do `os.environ.get("FLAG_DEVSECOPS", …)`, so an unset variable silently falls back to the hard-coded default — every student then leaks and submits the *same* flag, and the per-student integrity control fails without any error | Seed the per-student value before class, per the comment in `docker-compose.yml` (`… seed_flags.py env <STUDENT_ID> > .env`); spot-check one container's `/admin` response before the room starts Task 1b |
| GitHub Actions is the only SaaS dependency in the whole course. Tasks 2–4 need network access, a repo the student **owns**, and Actions **enabled** — and the ethics note forbids pushing planted secrets or vulnerable code anywhere shared | Make "bring a fork or throwaway repo with Actions on" an explicit pre-class instruction (worksheet Part 3 prerequisites). Students who cannot get one still complete Tasks 0, 1 and 1b locally and carry 2–4 forward |
| SARIF upload and the **Code scanning alerts** page may behave differently depending on repository visibility, so Task 2's second deliverable can be the step that fails | Confirm on the exact repository type students will use — ⬚ (not recorded in the repo, and not verified here). If the upload is rejected, Task 2's evidence falls back to the Actions run log, which still shows the three jobs executing |
| Task 3 will not go green: the **Semgrep gate** step is `semgrep scan --config p/default --config p/owasp-top-ten --error`, which fails on **any** finding — it has no severity filter, unlike Trivy's `severity: HIGH,CRITICAL`. `README-pipeline.md` §4 describes the gate as HIGH/CRITICAL, so students reasonably expect low-severity Semgrep hits to pass | Tune the Semgrep ruleset in the workflow, which §4 explicitly invites ("rulesets for Semgrep … as the class matures"), and document it as a justified, time-boxed exception — not a blanket ignore. Do this *before* class if you intend Task 3 to be achievable in 30 min |
| Gitleaks' gate step fails on **any** secret in the repo *or its history* (`fetch-depth: 0`), so a repo that already carries a committed secret can never go green. This repository handles that with a root `.gitleaks.toml` whose allowlist covers `labs/week15-devsecops-pipeline/.*` (among the other planted-secret labs) — a bare throwaway repo built from copied lab files has no such config | Point Task 3 at a clean repo, or carry the `.gitleaks.toml` allowlist across and have the student document it as the justified exception the task asks for. Do not solve it by deleting the gate step |
| Task 4's `chmod 777` variant produces nothing to catch unless the repo actually contains a Dockerfile or IaC file — Trivy's `scan-type: config` has no target otherwise | Steer students without a Dockerfile to the vulnerable-dependency or hard-coded-token variants, both of which the Trivy `fs` and Gitleaks gates catch in any repo |
| Floating upstream tags. The Semgrep job runs in `container: image: semgrep/semgrep:latest` and pulls `p/default` / `p/owasp-top-ten` from the registry; the Gitleaks job runs `zricethezav/gitleaks:latest`. A run that was green last term can be red this term without the repo changing | Expect it, and use it — a gate whose ruleset moves under you is exactly the vulnerability-management point in §1:35–1:55. Have one known-good run screenshotted in advance as a reference |
| Version drift between the lab template and the repo's own gate: the lab file pins `github/codeql-action/upload-sarif@v3`, while `.github/workflows/security-ci.yml` was bumped to a v4 SHA | Leave the lab template as it stands — `labs/` is deliberately excluded from Dependabot (see `.github/dependabot.yml`) and the pins are teaching material. Mention the drift in class as a live example of what Dependabot exists to surface |
| Copy-paste of a classmate's evidence | The per-student `FLAG_DEVSECOPS` makes the Task 1b flag attributable; Actions run links and Code scanning alert pages are repo-specific; viva spot-check the pair |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚
