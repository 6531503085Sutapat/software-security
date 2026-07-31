# Week 12 — Software Supply-Chain Security

*(Merges the former Dependencies and Integrity/Provenance weeks into one.)*

**OWASP 2025:** A03 Software Supply Chain Failures, A08 Software or Data Integrity Failures · **CWE:** CWE-1104, CWE-829

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week12.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 12** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `bash sca_scan.sh`.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Explain why the supply chain is now a top-tier risk; recognize dependency confusion, typosquatting, malicious packages, transitive risk.
- Run SCA tooling and interpret results.
- Generate/read an SBOM (CycloneDX/SPDX); explain SLSA provenance levels.
- Sign and verify an artifact with Sigstore/Cosign (keyless/OIDC).

## 📦 Signature game — "Dependency Confusion Heist"
**Round 1 — Attack:** in an instructor-provided private registry, plant/identify a typosquatted or higher-version public package and watch it get pulled into a build instead of the intended internal one.
```bash
# SCA options
npm audit
docker run --rm -v "$PWD:/src" aquasec/trivy fs /src
docker run --rm -v "$PWD:/src" owasp/dependency-check --scan /src --format HTML
```
**Round 2 — Defend:** pin versions / add a lockfile + registry scoping, then lock down integrity:
```bash
docker build -t myapp:lab .
docker run --rm -v "$PWD:/src" aquasec/trivy image --format cyclonedx -o /src/sbom.json myapp:lab  # SBOM
cosign sign myapp:lab && cosign verify myapp:lab                                                     # sign + verify
```
- Produce an SBOM and identify the component inventory.
- Show a tampered/unsigned image **fails** verification.
- Add a provenance/attestation gate before a simulated deploy.

## Deliverable
SCA report + remediation plan + SBOM file + signing/verification transcript + a one-paragraph SLSA self-assessment (which level you reach and why).

## References
- https://slsa.dev/  ·  https://www.sigstore.dev/  ·  https://cyclonedx.org/
- https://owasp.org/www-project-dependency-check/
