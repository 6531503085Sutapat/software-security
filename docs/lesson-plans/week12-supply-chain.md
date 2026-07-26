# Lesson Plan — Week 12: Software Supply-Chain Security

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 12 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week12-supply-chain` |
| **Slides** | `slides/week12.md` |
| **Standards** | OWASP 2025 **A03 Software Supply Chain Failures** · **A08 Software or Data Integrity Failures** · CWE-1104 (unmaintained third-party component), CWE-829 (inclusion of functionality from untrusted control sphere), CWE-1357 (reliance on insufficiently trustworthy component), CWE-1395 (dependency on vulnerable third-party component) |
| **CLOs addressed** | **CLO4** operate security tooling across the SDLC · **CLO5** evaluate & communicate · **CLO6** evidence & ethics |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — State why the supply chain is now a top-tier risk (A03:2025) and name the four vectors from the
  slides: typosquatting, dependency confusion, malicious updates from a compromised maintainer, and
  transitive risk.
- K2 — Explain **dependency confusion** (substitution): why a public `acme-internal-utils==99.0.0` wins
  over a private `==1.4.0` when a resolver shops both indexes.
- K3 — Explain how **typosquatting** (`reqeusts`, `urlib3`) achieves code execution *at install time*,
  before any of the project's own code runs.
- K4 — Define an **SBOM** (CycloneDX/SPDX) and say why it is a prerequisite for both incident response
  and SLSA provenance.
- K5 — Explain why Sigstore **keyless** signing — Fulcio (CA) + Rekor (transparency log) tied to an OIDC
  identity — is safer than a long-lived private key (CWE-321).
- K6 — Summarise the **SLSA** Build Track levels and place "signed artefact + SBOM + provenance gate
  before deploy" on that ladder, naming what is still missing.

**Skills (P)**
- P1 — Run `bash sca_scan.sh` and read both halves: the `trivy fs` table (CVE, installed vs. fixed
  version) and the `pip-audit` advisory IDs.
- P2 — Turn that output into a 3-row remediation table (package → current → fixed) with each finding's
  advisory ID and severity.
- P3 — Run the confusion: `pip install -v acme-internal-utils`, record the source URL/version served,
  then re-resolve so the higher-versioned public look-alike (`==99.0.0`) wins, and point at the
  `PWNED.txt` marker as proof that install-time code ran.
- P4 — Generate a CycloneDX SBOM from the built image and locate a named component's entry in it.
- P5 — Read a `cosign verify` PASS, and show that an unsigned image **fails** verification.
- P6 — Apply the four defences from `dependency-confusion.md` and `sign.sh`: pin + hashes, a single
  trusted index, namespace scoping, and a provenance gate before deploy.
- P7 — Map each finding to its OWASP 2025 id and CWE with a fix, in the Part 4 mapping table.

**Attitude (A)**
- A1 — Run the dependency-confusion / typosquat exercise **only** against the instructor-provided private
  registry in the isolated lab network; never plant or publish look-alike packages on the real PyPI or
  npm — that is an attack on every downstream user ([ETHICS.md](../../ETHICS.md)).
- A2 — Submit evidence that is identifiably their own work — `whoami` / login email / student ID and a
  timestamp on every screenshot — and be able to reproduce it live on request.
- A3 — Treat AI-generated security code and advice as something to critique and verify, not to trust.

## 2. Key ideas (the through-line)

Your code is roughly 10% yours and 90% other people's, so most of your attack surface is code you never
read and never chose — and the decision to trust it was not made by you but by a *resolver*, at install
time, on the basis of a name and a version number. Every attack this week exploits that delegated
decision: a name that is one keystroke off, a version number one order of magnitude too high, a
maintainer who was patient for two years. The defences all work by taking the decision back — pin what
you meant (hashes, lockfile), ask exactly one index (`--index-url`, not `--extra-index-url`), and refuse
to deploy anything you cannot verify. Three verbs carry the week: **know** your ingredients (SBOM),
**prove** your build (SLSA), **sign** your artefacts (Cosign). The second half of the idea is a tooling
lesson students meet the hard way in Task 1: the same nine pinned packages produce four different
answers depending on which scanner is asked, at what severity, and whether the question is about the
requirements file, the resolved tree or the whole image. The count is not the finding; the triage is.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
- **Instructor, before class:**
  - **Pre-pull the three images** — `aquasec/trivy:latest`, `python:3.9-slim`,
    `gcr.io/projectsigstore/cosign:latest` — and run Trivy once on the room's network so its
    vulnerability database is warm. Verified 2026-07-26: the first `trivy fs` run downloads
    **102.36 MiB** of DB before printing anything.
  - **Pre-build the image**: `docker build -t week12-supplychain:lab .` inside the lab folder. Verified
    2026-07-26 on Apple Silicon (arm64): it builds in seconds, all wheels resolve, and no `--platform`
    flag is needed. Building it in advance also switches on step 3/3 of `sca_scan.sh`, which otherwise
    prints `(image 'week12-supplychain:lab' not built yet …)` and skips.
  - **Stand up Task 2's registries.** Both `worksheet.md` and `dependency-confusion.md` say the exercise
    runs against an *instructor-provided* private registry plus a lab "public" index hosting the
    higher-versioned look-alike. ⬚ — **the repository does not ship that registry**, so it must exist
    before the session or Task 2 cannot run as written (see §8).
  - **Decide the registry for signing.** `sign.sh`'s own header says keyless signing "needs a
    browser/OIDC flow and registry push access; in class this is a guided demo, not an offline step."
    ⬚ — the repository names no registry.
- **Prerequisite concept:** what a CVE identifier is, how to read a pinned version specifier, and the
  `trivy fs` run from Week 2's tooling lab.

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | ~10-min retrieval quiz on Week 11 (memory safety & exploitation — "Fuzzing Race → Pwn the Binary"); bridge — last week the class fuzzed and pwned a binary it built from source in the room, this week the target is code nobody in the room has read; today's agenda | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concepts | The hook from the slide deck: how many lines did you write in your last project vs. how many did you ship? Your code is ~10% yours, ~90% dependencies — and that gap is the attack surface. **A03:2025 Software Supply Chain Failures**, new at the top of the list. Then the four attack vectors: typosquatting (`reqeusts` vs. `requests`), dependency confusion (public package shadows an internal name), malicious updates from a compromised maintainer, and transitive risk (deps of deps you never chose). Define dependency confusion carefully — it is the game | Lecture + live `trivy fs` run on the projector |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | The case table from the slides: **SolarWinds** (2020) trojanised vendor update → 18k orgs · **Log4Shell** (2021) RCE in a ubiquitous logging dependency · **event-stream** (npm) malicious dep stole crypto-wallet keys · **XZ Utils** (2024) backdoor planted in `liblzma` · **CircleCI** (2023) stolen CI tokens → customer secrets. Attacks are shifting **upstream**: registry → maintainer → CI/CD. Spend the time on XZ (the worksheet's Part 4 Q2 asks for it): a patient attacker became a trusted maintainer over years, and the lesson is that trust in maintainers is itself attackable | Lecture + short discussion: "what would have caught this?" |
| 1:35–1:55 | Defences | SCA and what it produces (CVE + fixed version) — `npm audit`, `trivy fs`, OWASP dependency-check; CWE-1104 / CWE-829. Then integrity: **SBOM** (CycloneDX/SPDX) as the ingredient list, **SLSA** Build Track levels **L0–L3** (the old "1–4" numbering is v0.1 and deprecated), **A08:2025**. Keyless signing with Cosign — `trivy image --format cyclonedx` → `cosign sign` → `cosign verify`, identity-based via OIDC so there is no key to leak; an unsigned or tampered image fails. The managed option they will meet in industry: GHAS — secret scanning + push protection, CodeQL, Dependabot. The closing checklist: pin versions + lockfiles, scope internal registries, verify signatures before deploy (admission policy), store an SBOM per release, MFA on dev/CI/cloud accounts, automate SCA in CI (Week 15) | Lecture with the sign → verify loop demonstrated live |
| 1:55–2:00 | Brief the game | 📦 **"Dependency Confusion Heist"** — Round 1 attack: plant/identify a typosquat or higher-version public package and watch it get pulled into a build. Round 2 defend: pin + scope, SBOM, sign & verify, provenance gate. State the ethics boundary here, not in the lab: controlled registry only, never the real PyPI/npm | Instruction |

**Checks for understanding during lecture**
- After the attack-vector slide: cold-call *"your internal package is called `acme-internal-utils`. What
  does an attacker have to publish, and what number do they have to choose?"*
- Before the break: one-minute paper — *"you vetted your ten dependencies. How many packages are
  actually in your build?"*
- At the end (from the slide notes): *"the next Log4Shell drops at 2am — what artefact tells you whether
  you are affected?"* (the SBOM).

## 5. Laboratory — 180 min

Target: `cd labs/week12-supply-chain` → `bash sca_scan.sh` (kickoff) → `docker build -t
week12-supplychain:lab .` → `bash sign.sh week12-supplychain:lab`. There is no running service this
week: `app.py` exists only so the image has something to be built, scanned and signed. Rows below use
Worksheet 12's own task names and minute budgets.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:15 | **Task 0 — Onboarding (15 min)** | Read `requirements.txt` and list the pinned packages with their versions; note why they are intentionally outdated (each is deliberately an old release so SCA tools flag its known CVEs) | The package/version table + which OWASP/CWE this maps to |
| 0:15–0:50 | **Task 1 — SCA scan: build the remediation worklist (35 min)** | `bash sca_scan.sh`; read the `trivy fs` table (CVE, installed vs. fixed version) and the `pip-audit` advisory IDs (GHSA-/PYSEC-); pick three findings and record CVE/advisory id, severity and the fixed version | The SCA output + a 3-row remediation table (package → current → fixed) |
| 0:50–1:25 | **Task 2 — Dependency Confusion Heist (35 min)** | Against the lab's private + "public" indexes, per `dependency-confusion.md`: `pip install -v acme-internal-utils` and note the source URL/version served; then re-resolve so the higher-versioned public look-alike (`==99.0.0`) wins, and observe the `PWNED.txt` marker proving install-time code ran | The source URL/version before vs. after confusion + the marker proof |
| 1:25–1:55 | **Task 3 — SBOM + signing/verification (30 min)** | After `bash sign.sh week12-supplychain:lab`, open `sbom.cdx.json` and find Flask's entry; read the `cosign verify` PASS; negative test `cosign verify --certificate-identity-regexp '.*' --certificate-oidc-issuer-regexp '.*' python:3.9-slim` and confirm the unsigned image fails with `Error: no signatures found` | The SBOM Flask component entry + the verify PASS + the negative-test failure |
| 1:55–2:30 | **Task 4 — Defend / fix it (35 min)** | **Pin + hashes:** convert to `pip install --require-hashes -r requirements.txt` (or a committed lockfile); re-run Task 2 step 2 and show a hash mismatch blocks the substitution. **Single trusted index:** use one `--index-url` instead of `--extra-index-url` and explain why the resolver stops shopping around. **Namespace scoping:** describe reserving/namespacing the internal package name. **Provenance gate:** state how the `cosign verify` from `sign.sh` becomes a gate before a simulated deploy | Before/after of which registry served the package + the one defence they found most effective and why |
| 2:30–2:55 | **AI-resilient tasks (25 min)** | *Audit the AI* (critique an AI-written exploit or fix, quoting the exact wrong line), *Explain-in-Plain-English*, *Prompt Problem* | Written answers (start in class, finish as homework) |
| 2:55–3:00 | **Micro-demo + submit (5 min)** | 2–3 rotating students give a 2–3 min "show your exploit/fix"; everyone submits | Worksheet PDF → Classroom; code → GitHub |

> **Scheduling note.** Worksheet 12's Part 3 budgets total 150 min (15 + 35 + 35 + 30 + 35), which is one
> of the light weeks [AGENDA.md](../../AGENDA.md) flags itself. The 30 minutes left over are spent by
> giving the *AI-resilient* block 25 min rather than AGENDA's 20, and merging micro-demo and submission
> into the closing 5. Nothing is cut.

**Formative checkpoints.**
- **The scanners disagree, loudly, and that is the lesson.** Verified on the current files
  (2026-07-26): `sca_scan.sh`'s `trivy fs` step runs with `--severity HIGH,CRITICAL` and reports
  **9 findings — all HIGH, 0 CRITICAL — against only Flask, Werkzeug and urllib3**. Drop the severity
  filter and the same scan reports **26**. `pip-audit`, in the very next step, reports **31 known
  vulnerabilities in 7 packages**. And once the image exists, step 3/3's `trivy image` adds a
  `week12-supplychain:lab (debian 13.1)` row with **48** more, none of which come from
  `requirements.txt` at all — they are the base image's OS packages. That is the script's own
  "image scanning is a superset" claim, made concrete. Say this before Task 1's table is started, or
  half the room will conclude one of the tools is broken.
- **Two packages named in `requirements.txt`'s own comments behave differently.** urllib3's
  **CVE-2021-33503** does appear in the `trivy fs` output (HIGH, fixed in 1.26.5). Jinja2's
  **CVE-2020-28493** does **not** — verified 2026-07-26, it is reported by neither `trivy fs` at any
  severity nor `pip-audit` against `Jinja2==2.11.3`. A student who picks Jinja2 for their three-row table
  because the file comment names a CVE will not find it. Excellent 60 seconds on "the comment is not the
  evidence; the tool output is".
- **`pip-audit` printed only `PYSEC-` IDs**, no `GHSA-` (verified 2026-07-26), although the worksheet
  writes "GHSA-/PYSEC-". Accept either.
- **`pip-audit` sees a package that is not in `requirements.txt`.** It flags `idna 2.10`, pulled in
  transitively by `requests` — the concrete instance of the lecture's "transitive risk" slide. Worth
  pointing at rather than letting a student mark it as tool noise.
- **Task 4 step 1's command does not run as printed.** Verified 2026-07-26:
  `pip install --require-hashes -r requirements.txt` against the current file stops at the first package
  with `ERROR: Hashes are required in --require-hashes mode, but they are missing from some
  requirements.` and helpfully prints the `--hash=sha256:…` line to add for `Flask==1.1.4`. That error
  *is* the teaching moment — hashes have to be generated (or a lockfile committed) before the defence
  exists — but budget for it, and note that pip demands hashes for transitives too, so a hand-written
  three-line attempt will keep failing.
- Tasks 0–1 must be finished by 0:50 or Task 2 slips into the SBOM slot. A student still fighting the
  Trivy DB download at that point should read a classmate's output for the table and come back to their
  own run later.

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 12, Part 2 (lecture questions) | Written answers on dependency confusion, typosquatting, SBOM, keyless signing, SLSA | K1–K6 | 20 of the worksheet's 100, within the 30% worksheet component |
| Worksheet 12, Part 3 Tasks 1–3 — exploitation + evidence | SCA findings, confusion proof, SBOM/verify transcript | P1–P5, A1 | 40 of 100 |
| Worksheet 12, Part 3 Task 4 — defence | Pinning/hashes, single index, scoping, provenance gate | P6 | 25 of 100 |
| Worksheet 12, Part 4 (reflection) | Mapping table, XZ Utils breach analysis, SLSA self-assessment | K4, K6, P7 | 15 of 100 |
| Weekly quiz (start of lecture) | Quiz score | K1–K3 | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation | P1–P6, A2 | Pass/flag for follow-up |
| Per-student flag | ⬚ — the worksheet issues one only conditionally ("if this lab issues one"); the repository does not record a Week 12 flag | A2 | Integrity control, not a mark |

*Audit the AI* and the *EiPE / Prompt Problem* count toward the Defense + Reflection score, per the
worksheet. Partial credit is available where a student explains a mechanism correctly but could not land
the tool run — which matters more than usual this week, because two of the tasks depend on
infrastructure outside the student's control (§8).

## 7. Materials

- Lab: `labs/week12-supply-chain/` — `README.md`, `worksheet.md`, `dependency-confusion.md`,
  `requirements.txt`, `Dockerfile`, `app.py`, `sca_scan.sh`, `sign.sh`
- Slides: `slides/week12.md`
- Tooling images: `aquasec/trivy:latest` (SCA + SBOM), `python:3.9-slim` (pip-audit host and the lab
  image's base), `gcr.io/projectsigstore/cosign:latest` (signing/verification)
- Task 2 infrastructure: ⬚ instructor-provided private registry + lab "public" index (not in this
  repository)
- References (from the lab README): https://slsa.dev/ · https://www.sigstore.dev/ ·
  https://cyclonedx.org/ · https://owasp.org/www-project-dependency-check/
- Project tie-in: apply the week's lesson to [NoteVault](../../project/README.md) where it fits
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Task 2 — the signature game — needs a registry this repository does not ship.** `worksheet.md` and `dependency-confusion.md` both say "instructor-provided private registry"; there is no compose file, script or fixture for it in `labs/week12-supply-chain/`, and an unfiltered `grep -r acme-internal-utils .` (2026-07-26) finds the name only inside those two documents — there is no package to serve | Stand it up (⬚ — the method is not recorded here) and smoke-test `pip install -v acme-internal-utils` on the room's network *before* the session. If it is not available, Task 2 degrades to a walkthrough of `dependency-confusion.md` on the projector and the deliverable becomes written: which index would have served the package, and why. Say so at 0:00 so nobody burns 35 minutes on a broken `pip` invocation |
| **The registry gap also removes the only hands-on part of Task 4.** Task 4 step 1 ends "re-run Task 2 step 2 and show a hash mismatch blocks the substitution" — that needs the same two indexes. Steps 2–4 are written as *explain* / *describe* / *state* and survive as prose | Without the registry, 25 marks of defence become written work plus the local half of step 1 (generating hashes and watching `--require-hashes` reject an unhashed requirement, which does run offline). Grade the mechanism, and mark the before/after registry line as ⬚ rather than penalising it |
| **`sign.sh` step 2 fails on a local-only image, and `set -e` then kills step 3.** Verified 2026-07-26: `cosign sign --yes week12-supplychain:lab` resolves the bare tag to Docker Hub and errors with `Error: signing [week12-supplychain:lab]: accessing entity: GET https://index.docker.io/v2/library/week12-supplychain/manifests/lab: UNAUTHORIZED: authentication required`. Cosign works against a *registry*, not the local daemon, so the "verify PASS" half of Task 3 never prints | Push the image to a registry the class can write to first (⬚ — none is named in the repo), or run step 2 as the guided demo `sign.sh`'s own header says it is. Step 1 (SBOM) and the negative test both run standalone, so Task 3's other two deliverables are unaffected — run the three commands separately rather than the whole script when signing is a demo |
| **Students omit the `--certificate-identity*` flags on the negative test.** Bare `cosign verify python:3.9-slim` stops at `Error: --certificate-identity or --certificate-identity-regexp is required for verification in keyless mode` — a *usage* error that proves nothing about signatures (verified against cosign v3.1.2). With the flags it prints `Error: no signatures found`, which is the real evidence | The worksheet now carries both flags. If a student submits the usage error, send them back: the deliverable is proof that verification **failed closed** on an unsigned image, not any failure at all |
| **`sbom.cdx.json` is not git-ignored.** `sign.sh` writes it into the lab folder; `.gitignore` lists `sbom.json` and `sbom.xml` but not `sbom.cdx.json`, so it shows up as an untracked file (verified 2026-07-26 — 229 KB, CycloneDX 1.7, 119 components) | Have students keep the file with their evidence and delete it from the working tree at the end of the session. The curriculum monorepo's parity gate compares every file in the lab directory, so a leftover SBOM breaks it |
| **The Docker-socket mount.** `sca_scan.sh` step 3/3 and `sign.sh` step 1/3 both mount `/var/run/docker.sock`. On this machine that path is a symlink to `$HOME/.docker/run/docker.sock` (verified 2026-07-26); on a Docker Desktop install where the symlink is absent, both `trivy image` steps fail while every other step keeps working | Check it before class with `ls -l /var/run/docker.sock`. Fallback: mount the real path, `-v "$HOME/.docker/run/docker.sock:/var/run/docker.sock"`. Task 1's marks come from steps 1/3 and 2/3, which need no socket at all, so this is survivable mid-session |
| **The Trivy database is re-downloaded on *every* invocation, not just the first.** ~102 MiB before any output. `sca_scan.sh` and `sign.sh` run Trivy in throwaway `--rm` containers with no cache volume mounted, so nothing persists between runs — verified 2026-07-26, two runs ten minutes apart each downloaded 102.3 MiB. There are three Trivy steps across the two scripts, so one student's afternoon is ~300 MiB and a room of 40 is a network incident. Add the pulls of `aquasec/trivy:latest`, `python:3.9-slim` and `gcr.io/projectsigstore/cosign:latest`, plus step 2/3's `pip install pip-audit` inside the container, which needs PyPI reachable | Pre-pull the images and keep a USB copy (`docker save` / `docker load`). Warn the class that a re-run is not free — this is also the natural moment to explain why a real CI job caches the DB. If the room is behind a proxy that blocks `gcr.io`, discover that in advance: it is the one registry here that is neither Docker Hub nor a mirror |
| **A student publishes a typosquat for real.** The whole exercise is one `twine upload` away from an attack on strangers | Brief the ethics boundary in the lecture at 1:55, not in the lab: controlled registry only, never the real PyPI/npm ([ETHICS.md](../../ETHICS.md), worksheet ethics note). Any student who asks "could I test this on real PyPI?" is the one to watch |
| **Students `docker run` the image and hit a port clash.** Nothing this week needs the container to run — `app.py` exists to be scanned — but `EXPOSE 5000` invites it | Tell them not to. If someone does, note that on macOS AirPlay squats on 5000; publish another host port instead |
| A student finishes Tasks 0–3 by 1:25 | Extension: generate a full hashed lockfile and prove `--require-hashes` now installs cleanly; or write the CI job that fails the build when `cosign verify` does — a preview of Week 15 |
| Copy-paste of a classmate's SCA table or SBOM entry | Identity-stamped screenshots (`whoami` / student ID + timestamp) plus the viva spot-check. The remediation reasoning and the "which defence was most effective and why" note are the parts that cannot be copied without being explainable |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚
