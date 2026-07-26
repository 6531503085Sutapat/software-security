# Lesson Plan — Week 13: Cloud & Container Security

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 13 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week13-cloud-container` |
| **Slides** | `slides/week13.md` |
| **Standards** | OWASP 2025 **A02 Security Misconfiguration** · CWE-732 (incorrect permission assignment), CWE-16 (configuration), CWE-798, CWE-250, CWE-538, CWE-269, CWE-1104 |
| **CLOs addressed** | **CLO3** remediate · **CLO4** operate security tooling (the course specification's weekly-schedule row for Week 13), plus **CLO5** evaluate & communicate and **CLO6** evidence & ethics through the recurring worksheet parts |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — State the shared-responsibility model in the form `harden.md` uses — "the cloud provider secures *of* the cloud; you secure what you put *in* it" — and give one concrete example of each side for an S3-backed app.
- K2 — Explain why `"Action": "*"` / `"Resource": "*"` violates least privilege, and distinguish CWE-269 (improper privilege management) from CWE-732 (incorrect permission assignment) on that policy.
- K3 — Explain why `FROM python:latest` is both a security and a reproducibility problem (CWE-1104 / CWE-16), how an `@sha256:` digest pin fixes it, and what a distroless base removes relative to `python:3.11-slim`.

**Skills (P)**
- P1 — Run the lab's scanner (`bash scan.sh`, or `trivy config` directly) and record a baseline finding count against `Dockerfile.insecure`.
- P2 — Produce the six-row defect → CWE → Trivy rule/severity table for `Dockerfile.insecure`, writing "manual review — no Trivy rule" for the three defects no Trivy Dockerfile check covers.
- P3 — Explain how `ENV API_TOKEN` / `AWS_SECRET_ACCESS_KEY` are recovered from a shipped image via `docker history` / `docker inspect`, and write the `.dockerignore` entries that stop `COPY . .` leaking `.git` / `.env` (CWE-538).
- P4 — Re-scan `Dockerfile.hardened`, capture the reduced finding count, and map every Task-1 defect to its fix (digest pin, multi-stage venv, distroless runtime, `USER 65532:65532`, no secrets in `ENV`, copy only `app.py`).
- P5 — Show that the IAM rewrite scopes `s3:GetObject` to `arn:aws:s3:::lab-app-bucket/app/*` and adds the `s3:prefix` `Condition`, and list the deploy-time flags from `harden.md` (`--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`).
- P6 — Tally the hunt: one flag per misconfiguration found **and** fixed (6 container + 3 IAM = 9), and name the single biggest-risk misconfiguration with a reason.

**Attitude (A)**
- A1 — Scan, exploit and harden only these lab files or systems they own / are authorised to test; never point Trivy or these techniques at third-party cloud accounts or images without written permission ([ETHICS.md](../../ETHICS.md), worksheet ethics note).
- A2 — Submit identity-stamped evidence that is their own work, and be able to reproduce it live on request.
- A3 — Treat AI-generated security advice as something to be verified, not trusted.

## 2. Key ideas (the through-line)

Cloud breaches are rarely clever zero-days; they are defaults nobody changed. The provider's half of
the contract is well-run infrastructure — the customer's half is configuration, and configuration is
where the failures happen. That is why misconfiguration sits at **A02** in OWASP 2025. Every artifact
in this lab is the same mistake in a different medium: a permission granted wider than the job needs
(`Action: *` on `Resource: *`, `chmod -R 777`, running as root), or a boundary that was never drawn
(a secret baked into an image layer, an unpinned base image, a `COPY . .` that sweeps in `.git`).
The fix is always to grant the minimum, on the minimum, under the right conditions — and then to
*prove* it with a re-scan, because "we hardened it" is a claim and the before/after finding count is
evidence. Week 12 was what you build with; this week is where you run it.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop running (Week 1 *Lab 0*); skim last week's recap
  (supply chain).
- **Instructor, before class:**
  - Pre-pull the scanner — `docker pull aquasec/trivy:latest` — and let Trivy download its checks
    bundle on your connection. If you plan to demo the optional CVE step, also build the image
    (`docker build -f Dockerfile.hardened -t week13-hardened:lab .`) **and then run** `scan.sh`'s
    step [2/2] against it (`docker run --rm -v /var/run/docker.sock:/var/run/docker.sock
    aquasec/trivy:latest image week13-hardened:lab`) so the ~100 MiB vulnerability database is
    already cached — `docker build` alone never invokes Trivy and does not populate that cache; a
    room of students pulling both at once is the standard way to lose twenty minutes.
  - **Run both scan commands yourself, then pick ONE command for all counting — Tasks 0, 1 and 4.**
    `bash scan.sh` carries `--severity HIGH,CRITICAL`, and `DS-0001` (the unpinned `:latest`) is
    MEDIUM — so the rule the worksheet names in Task 1 does **not** appear in the kickoff output.
    The unfiltered `docker run --rm -v "$PWD:/src" aquasec/trivy:latest config /src` does show it,
    which makes it the command that leaves Task 1 completable. Under the unfiltered command the
    hardened "after" count is **2, not 0** — that is a number students explain (an untagged
    distroless `FROM` and a missing `HEALTHCHECK`), not a failed defence. Mixing the two commands
    across Tasks 0/1/4 makes the before/after delta meaningless, so announce the choice once. See
    §8, rows 1–2.
  - Have the offline fallback ready (`docker save` / `docker load` of `aquasec/trivy:latest`).
- **Prerequisite concepts:** what a Docker image layer is; how to read an AWS IAM policy document
  (`Effect` / `Action` / `Resource` / `Condition`).

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | ~10-min retrieval quiz on Week 12 (supply chain); today's agenda; the bridge from the slides — "supply chain → what you build with; today → where you run it", and A02:2025 is now #2 | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concepts | Shared responsibility ("cloud secures *of* the cloud; you secure *in* the cloud"; defaults are rarely safe). IAM & least privilege on the worked example `{ "Effect":"Allow", "Action":"*", "Resource":"*" }` — blast radius, then have the class rewrite it as read-only on one bucket. Secrets management: a secret in an image layer is in every copy of that image forever; `docker history` reveals it; inject at runtime from a vault and rotate (callback to Gitleaks, Week 2) | Lecture + live rewrite of the policy on the projector |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | Storage and network exposure — public buckets, open ports (`0.0.0.0/0` on a database port), default credentials; encrypt at rest and in transit; private by default. Container image hardening: what `trivy config` finds (misconfiguration) versus what `trivy image` finds (CVEs in the base). Kubernetes awareness only — pod security, network policies, RBAC; a privileged pod ≈ host root; mounted service-account tokens are a lateral-movement prize. Two real incidents of the two types the worksheet's Part 4 Q2 names — a public S3 bucket leak and an over-permissive IAM role (⬚ instructor's chosen incidents) | Lecture + short discussion: "what single control from this lab would have prevented it?" |
| 1:35–1:55 | Defences | The least-privilege rewrite line by line: enumerate only the actions used (`s3:GetObject`), scope to a specific ARN and prefix, add a `Condition`. Digest pin instead of `:latest`; multi-stage build with the dependencies installed in a stage you throw away; distroless runtime; `USER 65532:65532`; no secrets in `ENV` plus a `.dockerignore`. Deploy-time hardening from `harden.md`: `--read-only --cap-drop ALL --security-opt no-new-privileges`, `--memory` / `--pids-limit`, never `--privileged`, never mount the Docker socket into untrusted containers | Lecture with `Dockerfile.insecure` / `Dockerfile.hardened` shown side by side |
| 1:55–2:00 | Brief the game | "Misconfig Hunt" **as the worksheet implements it**: 9 flags = 6 container defects in `Dockerfile.insecure` + 3 IAM defects in `iam-policy-insecure.json`; a flag counts only when the misconfiguration is found **and** fixed. Say explicitly that the IAM policies are reviewed by hand — Trivy does not scan them | Instruction |

**Checks for understanding during lecture**
- After the IAM slide: cold-call *"what does a `*:*` policy cost you if that key leaks?"*
- Before the break: one-minute paper — *"name one thing that is the provider's job and one that is yours, for an S3-backed app"* (this is Part 2 Q1 in miniature).
- After the hardening slide: *"which of the six defects would a scanner never tell you about?"*

## 5. Laboratory — 180 min

Targets: the files in `labs/week13-cloud-container/` — `Dockerfile.insecure` (the "before"),
`Dockerfile.hardened` (the "after"), `iam-policy-insecure.json` / `iam-policy-leastpriv.json`, and
`harden.md` (the misconfig → fix mapping students cite IDs from). **There is no `docker compose` file
this week** — the kickoff is `bash scan.sh`, and the graded evidence is scanner output plus code
review, not a running web app. Per task, students submit the command(s) they ran, the relevant
output or finding line, an identity-stamped screenshot, and a 2–3 sentence mitigation citing the CWE.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:15 | **Task 0 — Onboarding (15 min)** | `docker version`; `cd labs/week13-cloud-container`; `bash scan.sh`; record the **baseline finding count** against `Dockerfile.insecure` (the IAM JSON is not scanned — it is reviewed by hand in Task 2) | Screenshot of the baseline scan + the count |
| 0:15–0:55 | **Task 1 — Misconfig Hunt: container image (40 min)** | Read each `# DEFECT:` comment in `Dockerfile.insecure`, then locate the matching Trivy finding where one exists — only 3 of the 6 (unpinned `:latest`, runs as root, secrets in `ENV`) map to a rule (`DS-0001`, `DS-0002`, `DS-0031`); `COPY . .`, `chmod -R 777` and the unpinned `pip install` are found by code review | Completed 6-row table: defect → CWE → Trivy rule/severity, using the IDs from `harden.md`, with "manual review — no Trivy rule" where none exists |
| 0:55–1:25 | **Task 2 — Misconfig Hunt: IAM (30 min)** | Read `iam-policy-insecure.json`; identify the `Action:*` / `Resource:*` / no-`Condition` problems and map them to CWE-269 / CWE-732 | 3-row table + one sentence on the blast radius if these credentials leak |
| 1:25–1:50 | **Task 3 — Secrets & storage (25 min)** | Explain how `ENV API_TOKEN` / `AWS_SECRET_ACCESS_KEY` are exposed via `docker history`; propose where they belong instead (secrets manager / mounted secret / orchestrator secret, per `harden.md`) | 2–3 sentence remediation + the `.dockerignore` entries that stop `COPY . .` leaking `.git` / `.env` (CWE-538) |
| 1:50–2:40 | **Task 4 — Hardened-Dockerfile + least-priv-IAM defense (50 min)** | (a) Re-run `bash scan.sh` (or `trivy config`) and capture the **reduced** count for `Dockerfile.hardened`, confirming the IAM fix manually by diffing `iam-policy-leastpriv.json` against the insecure policy; (b) point to the fix for each Task-1 defect (digest pin, multi-stage venv, distroless runtime, `USER 65532:65532`, no secrets in `ENV`, copy only `app.py`); (c) confirm the rewrite scopes `s3:GetObject` to `arn:aws:s3:::lab-app-bucket/app/*` and adds the `s3:prefix` `Condition`; (d) list the extra runtime flags from `harden.md` | Before/after finding counts **labelled with the command that produced them**, the defect→fix mapping, and the diffed policy/Dockerfile with one sentence per fix |
| 2:40–3:00 | **Task 5 — Flag tally (20 min)** | Score the hunt: one flag per misconfiguration found **and** fixed (6 container + 3 IAM = 9) | Flag count + the single biggest-risk misconfiguration and why |
| carry-over | **AI-resilient tasks** | *Audit the AI* (critique an AI-written exploit or fix, quoting the exact bad line), *Explain-in-Plain-English*, *Prompt Problem* | Written answers (start in class only if ahead of budget; otherwise homework) |
| carry-over | **Micro-demo + submit** | 2–3 rotating students give a 2–3 min "show your misconfig/fix"; everyone submits | Worksheet PDF → Classroom; hardened artifacts → GitHub; weekly quiz → Google Form |

**Timing note — this block is over-subscribed.** The worksheet's Part-3 tasks (0, 1, 2, 3, 4, 5) sum
to **180 min exactly**, so they fill the entire lab. The standard *AI-resilient* and
*micro-demo/submit* blocks therefore have no dedicated slot this week: run them in class only if the
room is ahead of budget; otherwise the AI-resilient tasks start in class and finish as homework (as
the worksheet and [AGENDA.md](../../AGENDA.md) already specify), and the last minutes of Task 5's slot
double as the submit-and-wrap window. The rotating micro-demo can roll to the next week or be sampled
by viva.

**Formative checkpoints.**
- A student who reports that "one of the three Trivy rules doesn't exist" is usually right about
  their command, not wrong about the lab. `bash scan.sh` filters to `HIGH,CRITICAL`; `DS-0001` is
  MEDIUM and is filtered out. Have them re-run without the severity filter (§8, row 1) — do not mark
  this as a missed finding.
- Task 1's table has six rows but only three scanner findings. A student waiting for `COPY . .`,
  `chmod -R 777` and the unpinned `pip install` to light up should be sent back to the `# DEFECT:`
  comments in `Dockerfile.insecure` and told to write "manual review — no Trivy rule". The point of
  the task is that a clean scan is not a clean image.
- Task 2 produces **no scanner output at all**, by design — the deliverable is a three-row table
  written from reading the JSON. Students who keep re-running Trivy hoping for an IAM finding have
  misread the task; `scan.sh`'s own header comment says so.
- Task 4 alone carries a dedicated 25-point Defense line (on top of its share of Part 3's 40-point
  Tasks-0–5 lump sum). A student behind at 1:50 should move to Task 4 now and come back to Tasks
  2/3 afterwards.
- Insist the before/after counts name the command that produced them; the two commands give
  different numbers (§8, row 2).

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 13, Part 2 (lecture questions) | Five written answers with CWE / A02 reasoning | K1–K3 | 20 of the worksheet's 100 |
| Worksheet 13, Part 3 (Tasks 0–5) | Commands, Trivy output, screenshots, the defect and IAM tables | P1–P3, P6, A2 | 40 of 100 |
| Defence — Task 4 hardening | Before/after counts, per-defect fix mapping, diffed policy and Dockerfile | K3, P4, P5 | 25 of 100 |
| Worksheet 13, Part 4 (reflection) | Line → CWE → A02 mapping, real incident, best-mitigation argument | K1, K2, A3 | 15 of 100 |
| Weekly quiz (start of lecture) | Quiz score (Week 12 retrieval) | — | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation | P2, P4, A2 | Pass/flag for follow-up |

The worksheet total feeds the 30% weekly-worksheet component. *Audit the AI* counts toward the
Defence + Reflection score, as the worksheet states; *Explain-in-Plain-English* and *Prompt Problem*
are graded on prompt precision and verification (per the worksheet's Comprehension & Prompt section)
and are folded into the same score as instructor policy, not a worksheet-stated rule. Partial credit
is available where a student maps and justifies a fix correctly but could not get the scan to run.

## 7. Materials

- Lab: `labs/week13-cloud-container/` — `Dockerfile.insecure`, `Dockerfile.hardened`, `harden.md`,
  `iam-policy-insecure.json`, `iam-policy-leastpriv.json`, `scan.sh`, `app.py`, `requirements.txt`,
  `worksheet.md`, `README.md`
- Slides: `slides/week13.md`
- Tooling: `aquasec/trivy:latest` (pulled and run in throwaway containers by `scan.sh`)
- Reading list ([readings.md](../../readings.md), W13): OWASP Docker Security Cheat Sheet ·
  NIST SP 800-190 · CIS Benchmarks · AWS Well-Architected Security Pillar. The lab README also links
  the Kubernetes security-concepts documentation.
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Task 1 names `DS-0001`, but the kickoff command hides it.** `bash scan.sh` runs `trivy config --severity HIGH,CRITICAL`; `DS-0001` (unpinned `:latest`) is MEDIUM, so it never appears — a graded deliverable is unreachable via the documented command | For Task 1, have the class run `docker run --rm -v "$PWD:/src" aquasec/trivy:latest config /src` with no severity flag. Verified 26 Jul 2026: the unfiltered run reports `DS-0001` (MEDIUM) at `Dockerfile.insecure:11`; `bash scan.sh` does not. Announce this at 1:55 in the lecture, before students lose time hunting |
| **Before/after counts differ depending on which command produced them** | Verified 26 Jul 2026 — filtered (`bash scan.sh`): `Dockerfile.insecure` 3 (HIGH 1, CRITICAL 2), `Dockerfile.hardened` 0. Unfiltered: `Dockerfile.insecure` 5, `Dockerfile.hardened` **2** — `DS-0001` (MEDIUM) at `Dockerfile.hardened:34`, because the distroless `FROM gcr.io/distroless/python3-debian12` carries no tag, plus `DS-0026` (LOW, missing `HEALTHCHECK`). Require the submitted pair to state its command; grade the **delta and the defect→fix mapping**, not the absolute number — counts move whenever Trivy's checks bundle updates |
| **Students wait for an IAM finding that never comes.** Trivy's config scanner does not parse standalone AWS IAM policy JSON (verified: the scan reports `Detected config files num=2` — the two Dockerfiles only). `slides/week13.md` still describes the kickoff as "trivy config over Dockerfiles + IAM JSON" | Correct that slide line verbally when briefing the game; `worksheet.md` Task 2 and `scan.sh`'s header comment already say the IAM policies are reviewed manually |
| **The game brief promises a round the lab does not ship.** `README.md` and `slides/week13.md` list four rounds including "Storage: lock down a publicly-exposed bucket (provided as IaC/localstack)"; no localstack or IaC artifact exists in the lab folder, and the worksheet's tally is 6 container + 3 IAM = 9 flags, where "storage" means the `COPY . .` / `.dockerignore` leak (CWE-538) | Brief the game from the worksheet, not the slide: 9 flags, container + IAM. If a student asks for the bucket round, point them at Part 4 Q2 (a real public-bucket breach) as the written substitute |
| **Slow or failed pulls; Docker Hub rate limits** | Pre-pull `aquasec/trivy:latest`. The first `trivy config` downloads the checks bundle; the first `trivy image` downloads a ~100 MiB vulnerability database. Keep a `docker save` / `docker load` copy on a USB stick, and stagger the room if bandwidth is thin |
| **The optional CVE scan needs the Docker socket.** Step [2/2] of `scan.sh` mounts `-v /var/run/docker.sock:/var/run/docker.sock`, which fails on setups where the socket is elsewhere (rootless, Colima) | Step [2/2] is explicitly optional and all of Task 4's graded evidence comes from `trivy config`. `scan.sh` already prints a skip message when the image has not been built. Do not widen the task to depend on it |
| **Apple Silicon platform mismatch** | Verified 26 Jul 2026 on an arm64 Mac: `docker build -f Dockerfile.hardened -t week13-hardened:lab .` succeeds, the image reports Architecture `arm64` and `Config.User` `65532:65532`, and the container answers `{"app":"week13-demo","status":"ok"}`. The pinned build-stage digest is an OCI **image index** — `docker buildx imagetools inspect python:3.11-slim@sha256:cdbd05…` lists `linux/amd64` and `linux/arm64/v8` among its platforms — so it resolves on both halves of the room. Warn any student who refreshes it with the command in the Dockerfile comment (`docker buildx imagetools inspect python:3.11-slim`) to take that **index** digest, not one of the per-platform manifest digests underneath it, which would pin the build to a single architecture |
| **Port clash if anyone runs the demo app** | `app.py` binds `0.0.0.0:5000` and the Dockerfiles `EXPOSE 5000`; on macOS AirPlay Receiver squats host 5000, and on a busy machine 8080 may already be allocated (`Bind for 0.0.0.0:8080 failed: port is already allocated` happened while verifying this plan). No graded task needs a published port — if demoing, publish any free host port |
| **"Prove it runs as non-root" from inside the container fails.** The hardened runtime is distroless: no shell, so `docker run -it … sh` and `docker exec … sh` both fail | Have students use `docker image inspect --format '{{.Config.User}}' week13-hardened:lab` (verified: returns `65532:65532`), or cite `USER 65532:65532` in the Dockerfile plus the cleared `DS-0002` finding |
| **`docker compose up` muscle memory** | There is no compose file this week. The kickoff, per `README.md`, is `bash scan.sh` from inside `labs/week13-cloud-container` |
| **A student finishes the hunt early** | Extensions: write the `.dockerignore` from Task 3 and show `COPY . .` no longer pulls `.git`; add the missing `HEALTHCHECK` and re-scan to clear `DS-0026`; or add a digest pin to the distroless `FROM` and watch `DS-0001` clear on `Dockerfile.hardened:34` |
| **Copy-pasted tables between students** | The six defect rows are fixed by the file, so the tables converge — grade the mitigation sentences and the flag-tally reasoning, keep the identity-stamped screenshots, and viva spot-check any pair whose wording matches |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚
