# Week 2 — Secure SDLC & Tooling

**Concepts:** SAST · DAST · SCA · IAST · secret scanning · **fuzzing** · shift-left / DevSecOps

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week02.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 2** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `bash scan.sh`.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Place security activities across the SDLC.
- Distinguish SAST vs DAST vs SCA vs **fuzzing** and when each applies.
- Run a static analyzer and a secret scanner and triage findings by CWE.
- Understand coverage-guided **fuzzing** as the dominant modern bug-finding technique.

## 🏁 Signature game — "Bug Triage Race"
Teams race to scan a flawed repo and triage accurately. Score = true positives − misclassified. Live scoreboard.
Target: an intentionally insecure repo (provided).
Run these from `labs/week02-sdlc-tooling`, or just `bash scan.sh`, which runs
both against the same target.
```bash
# SAST
docker run --rm -v "$PWD/vulnerable-repo:/src" semgrep/semgrep semgrep --config p/default /src
# Secret scanning — --no-git is required, and the path must be vulnerable-repo/
docker run --rm -v "$PWD/vulnerable-repo:/repo" zricethezav/gitleaks:latest detect --no-git -s /repo -v
```
> **Why `--no-git`.** Without it `gitleaks detect` runs in git mode and walks
> commit history, and `vulnerable-repo/` is a plain directory with no `.git` —
> so it aborts with *"not a git repository"*, reports **`no leaks found`**, and
> you get zero rows for the triage table. Pointing it at the repo root instead
> is no better: the root `.gitleaks.toml` allowlists this lab's directory on
> purpose, so the two planted secrets are suppressed there by design.
> Run as written above you get **2 findings** — `AWS_SECRET_ACCESS_KEY` and
> `DB_PASSWORD` in `app.py`, both rule `generic-api-key` — which are the two
> worksheet Task 2 asks you to identify.
1. Run both tools; export findings.
2. Categorize each finding by CWE and severity.
3. Mark 3 true positives and 1 likely false positive; justify.

## Mini-lab — "Fuzzing Race" (intro)
First team to make the target crash wins. `harness.c` (in this folder) has one planted
memory-safety bug for libFuzzer to find. A deeper fuzzing+exploit lab follows in [Week 11](../week11-memory-safety-exploitation/).
```bash
# run inside labs/toolbox (Apple clang has no libFuzzer runtime)
clang -g -fsanitize=address,fuzzer harness.c -o fuzz && ./fuzz
# expect an AddressSanitizer heap-buffer-overflow within seconds + a crash-* reproducer file
```

## Deliverable
A findings triage table (tool, CWE, severity, TP/FP, fix idea) + one fuzzing crash with a one-line root-cause note.

## References
- https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html
- https://semgrep.dev/  ·  https://github.com/gitleaks/gitleaks
- https://llvm.org/docs/LibFuzzer.html  ·  https://github.com/AFLplusplus/AFLplusplus
