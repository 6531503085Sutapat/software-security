---
marp: true
theme: default
paginate: true
header: "Software Security · Week 2"
---

# Week 2
## Secure SDLC, Tooling & Fuzzing
Software Security · Nutthakorn Chalaemwongwan

<!-- Hook: open by running a scanner live on a flawed repo and let a finding pop up in seconds — "this is how the industry finds bugs at scale." Today = the tools + the mindset of catching bugs early. ~2 min. -->

---

## Today

- Security across the SDLC ("shift left")
- SAST · DAST · SCA · secret scanning · **fuzzing**
- Triaging findings by CWE
- 🏁 Game: **Bug Triage Race** + a **Fuzzing Race**

<!-- Roadmap, 1 min. Flag the lab: scan a deliberately flawed repo, triage by CWE, then fix. Bonus: first team to crash a target with a fuzzer. -->

---

## Recap — Week 1

- Threat modeling finds *design* flaws (before code)
- This week: find *implementation* flaws — automatically, at scale
- Same goal: catch it early, cheap to fix

<!-- Bridge from W1. W1 = think (design). W2 = automate (code). Remind the cost curve: a bug caught in CI costs ~1×, in production ~100×. ~2 min. -->

---

## Security across the SDLC

Requirements → Design → Code → Build → Test → Deploy → Operate

- Each phase has security activities
- **Shift left:** find issues early — cheaper to fix
- DevSecOps = security automated into the pipeline

<!-- Walk the phases on the board; ask "where can security live?" (answer: every phase). Threat modeling = design; SAST/secret scan = code/commit; DAST = test; monitoring = operate. "Shift left" = move detection earlier. ~5 min. -->

---

## The tooling families

| Tool | What it sees | When |
|---|---|---|
| **SAST** | source code | code/commit |
| **DAST** | running app | test/staging |
| **SCA** | dependencies | build |
| **Secret scanning** | secrets in code/history | commit/CI |
| **Fuzzing** | runtime + random inputs | **build** (compiled harness, not the text) |

<!-- The mental map for the whole unit. Stress: no single tool finds everything — they see different things. Tie each to a later week (SCA → W12, DAST → Burp in W4-6). ~5 min. -->

---

## SAST vs DAST in one line

- **SAST** — reads the code, finds bug patterns (no running). Many false positives.
- **DAST** — attacks the live app from outside. Fewer FPs, misses source-level issues.

> Use both — they find different things.

<!-- The classic comparison students confuse. Analogy: SAST = proofreading the recipe; DAST = tasting the cooked dish. SAST sees a hardcoded secret DAST never will; DAST sees an auth bypass SAST can't. ~4 min. -->

---

## Worked example: what each tool catches

```python
@app.route("/user")
def user():
    name = request.args.get("name")
    q = "SELECT * FROM users WHERE name='%s'" % name   # SAST → CWE-89
    return db.execute(q).fetchall()
AWS_SECRET_ACCESS_KEY = "hK8pQ2mN5vX9wZ3rT6yU1sA4bC7dE0fG2hJ5kL8"  # Gitleaks → CWE-798
```

- **Semgrep (SAST):** flags the string-built SQL query (CWE-89)
- **Gitleaks (secret scan):** flags the hardcoded key — *must be a real-looking secret;* the AWS-docs example key (`wJalr...EXAMPLEKEY`) is a known public string and **won't fire any rule**
- **DAST/fuzzer:** would catch a crash/SQLi by *hitting* `/user`, not reading it
- Same file also plants command injection, a weak `md5` hash, and `debug=True` — Task 1 grades all five

<!-- The make-it-concrete slide — point at the exact lines each tool fires on. This is the `vulnerable-repo/app.py` they'll scan in the lab. Ask: "which tool finds the secret? which finds the SQLi? could one tool find both?" ~6 min. -->

---

## Fuzzing — how real CVEs are found

- Feed **random/mutated inputs**, watch for crashes
- **Coverage-guided** (libFuzzer/AFL++) explores new code paths
- Pair with sanitizers (ASan) to pinpoint the bug

```bash
# run inside labs/toolbox — Apple clang has no libFuzzer runtime
clang -g -fsanitize=address,fuzzer harness.c -o fuzz
mkdir -p corpus && printf 'FUZ' > corpus/seed && ./fuzz corpus
```

<!-- Fuzzing is the highest-yield bug finder in industry (most memory CVEs come from it). Explain coverage-guided = the fuzzer "learns" inputs that reach new code. The seed corpus matters — unseeded, this exact harness crashes in roughly 1 of 6 short runs; seeded, it's reliable every time. Deep dive + exploit comes in W11. ~5 min. -->

---

## Triage: not every finding is a bug

- **True positive** vs **false positive**
- Map each to a **CWE** + severity
- Prioritize by exploitability × impact
- Noise kills trust in tools — triage well

<!-- Crucial professional skill: a scanner that cries wolf gets ignored. Show a likely false positive vs a real one. Teach: every finding gets a CWE + a TP/FP call + a one-line justification. ~4 min. -->

---

## Tools you'll meet

- **Trivy** — the SCA scanner *you'll actually run this lab* (dependency scan today; image + IaC scanning return in W12/13)
- **SonarQube**, **GitHub Advanced Security (GHAS)** — quality-gate/SAST-in-the-repo tools you'll see in industry/internships, not used in this lab
- Address **technical debt** early — cheaper than re-work later

<!-- Trivy is the one they'll type today (Task 5, scanning the NoteVault target) — say so explicitly so "tools you'll meet" doesn't read as "tools this lab uses." SonarQube/GHAS are real-world awareness. Connect "technical debt" to the cost curve from the recap. ~3 min. -->

---

## 🏁 Game — Bug Triage Race

- Run **Semgrep + Gitleaks** on the flawed repo
- Score = true positives − misclassified · live scoreboard

```bash
docker run --rm -v "$PWD/vulnerable-repo:/src" semgrep/semgrep \
  semgrep --config p/default --config p/owasp-top-ten /src
docker run --rm -v "$PWD/vulnerable-repo:/repo" zricethezav/gitleaks:latest \
  detect -s /repo -v --no-git
```

<!-- Explain the game before lab: speed + accuracy. Penalize wild guessing (misclassified subtracts) so they must justify each finding. Mirrors a real bug-bounty triage queue. Warn about the two gotchas up front: Gitleaks needs `--no-git` or it silently reports zero leaks; the repo root's own `.gitleaks.toml` deliberately allowlists this lab's secrets, so scan `vulnerable-repo/` specifically, not the repo root. ~3 min. -->

---

## 🐝 Mini-game — Fuzzing Race

- First team to make the provided target **crash** wins
- One crash → one root-cause note
- Full fuzz→exploit lab returns in **Week 11**

<!-- Quick, fun, instant feedback (it crashes or it doesn't). Sets up W11. If short on time, make this a demo. ~2 min. -->

---

## Lab 2 — deliverable

> 📋 **Worksheet 2** — `labs/week02-sdlc-tooling/worksheet.md` (Part 3) · **kickoff:** `bash scan.sh` (Semgrep ×2 rulesets + Gitleaks `--no-git` on `./vulnerable-repo`)

- A findings **triage table**: tool, CWE, severity, TP/FP, fix idea (3 TP + 1 FP, justified)
- 1 fuzzing crash with a one-line root cause
- Trivy SCA scan of the **NoteVault** project target
- A security **CI gate** built from Week 15's `security-ci.yml`
- One **SAST blind spot** you found by hand
- **Defend/fix: remediate all 5 planted flaws**, before/after diff — this alone is 25 of 100 rubric points
- **+ Audit the AI** and **EiPE / Prompt Problem** (see worksheet)

<!-- The graded output — six tasks, not three. The defend/fix task (25 pts, "Defense") is the single biggest score component and is easy to undersell if you only recap the triage table. Point to scan.sh. -->

---

## Key takeaways

- No single tool finds everything — layer SAST/DAST/SCA/fuzzing
- Triage by CWE + severity; kill the noise
- Fuzzing is the highest-yield bug finder — automate it

<!-- Recap, 3 lines. Cold-call: "name a bug SAST would miss but DAST would catch." ~2 min. -->

---

# Questions?
Next week: Cryptography used correctly

<!-- Cliffhanger: "Next week we break crypto — crack passwords and decrypt a secret in minutes." Remind: scanners ready in their VM. -->
