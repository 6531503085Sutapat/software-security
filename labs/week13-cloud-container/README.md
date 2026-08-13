# Week 13 — Cloud & Container Security

**OWASP 2025:** A02 Security Misconfiguration · **CWE:** CWE-732, CWE-16

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week13.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 13** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `bash scan.sh`.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Apply the shared-responsibility model and least privilege (IAM).
- Manage secrets safely; harden container images.
- Find and fix common cloud/container misconfigurations.

## 🔍 Signature game — "Misconfig Hunt" (CloudGoat-style)
Scavenger hunt: each misconfiguration you find **and** fix = a flag — **9 flags, two categories**.
```bash
docker run --rm -v "$PWD:/src" aquasec/trivy config /src     # IaC/Dockerfile misconfig
docker run --rm aquasec/trivy image week13-hardened:lab       # image CVEs
```
1. **Container (6):** `:latest` tag, root user, secret-in-`ENV`, `COPY . .`, `chmod -R 777`, unpinned `pip install`. Only 3 of the 6 map to a Trivy rule — the rest need manual review.
2. **IAM (3):** given an over-permissive policy (`Action:"*"`, `Resource:"*"`), fix `Resource:"*"` (CWE-732), `Action:"*"` (CWE-269), and add a missing `Condition` scope. Trivy does not parse standalone IAM JSON — entirely manual review.

Use a minimal/distroless base, drop root, pin versions; re-scan to show fewer findings.

## Deliverable
Before/after policy + Dockerfile + Trivy reports showing reduced risk.

## References
- https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- https://kubernetes.io/docs/concepts/security/
