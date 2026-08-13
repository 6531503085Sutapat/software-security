# Week 15 — DevSecOps: Putting It Together

**OWASP 2025:** A09 Security Logging & Alerting Failures, A10 Mishandling of Exceptional Conditions

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week15.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 15** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Two run paths: **(a)** spawn the local target `docker compose up` → the **insecure** service on `:8090` (fails OPEN) vs the **secure** service on `:8091` (fails CLOSED + logs); **(b)** `push security-ci.yml → GitHub Actions` for the pipeline gate.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Add logging/monitoring/alerting and fail-safe error handling.
- Build a CI/CD pipeline that enforces security gates.
- Understand vulnerability management and coordinated disclosure, framed by **CISA "Secure by Design"**.

## 🔴🔵 Signature game — "Break the Build" (Red vs Blue)
Use this lab's own pipeline template as the starting point: [`security-ci.yml`](security-ci.yml) (wiring steps in [`README-pipeline.md`](README-pipeline.md)).
- **Blue team** builds the gate:
  1. Add **SAST** (Semgrep), **SCA + IaC** (Trivy), and **secret scanning** (Gitleaks) jobs.
  2. Configure the build to **fail** on HIGH/CRITICAL findings; upload SARIF to the GitHub Security tab.
  3. Add structured security logging + an alert on auth failures; ensure errors **fail closed**, not open.
- **Red team** submits PRs trying to sneak a vuln/secret past the gate.
- **Score:** Blue gets points for each catch, Red for each bypass.

## Deliverable
A passing PR that adds the pipeline, plus a screenshot of a build failing on an injected vulnerable dependency.

## References
- https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- https://docs.github.com/actions
