---
marp: true
theme: default
paginate: true
header: "Software Security · Week 12"
---

# Week 12
## Software Supply-Chain Security
Software Security · Nutthakorn Chalaemwongwan

<!-- Hook: ask how many lines of code they wrote in their last project vs how many they shipped. The gap is dependencies — and that's the attack surface this week. One poisoned package = thousands of victims. ~2 min. -->

---

## Today

- Why the supply chain is now top-tier
- Dependency confusion & typosquatting
- SBOMs, SLSA provenance
- Signing with Sigstore/Cosign
- 🎮 Game: **Dependency Confusion Heist**

<!-- Roadmap, 1 min. Three verbs to remember all week: KNOW your ingredients (SBOM), PROVE your build (SLSA), SIGN your artifacts (Cosign). -->

---

## The new #1 design risk

- Your code is ~10% yours, ~90% dependencies
- One bad package → thousands of victims (xz, event-stream, SolarWinds)
- **OWASP A03:2025 Software Supply Chain Failures**

<!-- New in OWASP 2025 — promoted to A03, reflecting reality. The 10/90 ratio shocks students. You can write perfect code and still be owned through a dependency you never read. ~4 min. -->

---

## Real supply-chain attacks

| Case | What happened |
|---|---|
| **SolarWinds** (2020) | trojanized vendor update → 18k orgs |
| **Log4Shell** (2021) | RCE in a ubiquitous logging dep |
| **event-stream** (npm) | malicious dep stole crypto-wallet keys |
| **XZ Utils** (2024) | backdoor planted in `liblzma` upstream |
| **CircleCI** (2023) | stolen CI tokens → customer secrets |

> Attacks are shifting **upstream**: registry → maintainer → CI/CD.

<!-- Spend time on xz (2024): a patient attacker became a trusted maintainer over years, then planted a backdoor caught only by luck (a 0.5s SSH delay). The lesson: trust in maintainers is itself attackable. ~5 min. -->

---

## Attack vectors

- **Typosquatting** — `reqeusts` vs `requests`
- **Dependency confusion** — public pkg shadows internal name
- **Malicious updates** — compromised maintainer
- **Transitive risk** — deps of deps you never chose

<!-- Define dependency confusion clearly (it's the game): if your internal pkg "acme-utils" isn't scoped, a public "acme-utils" with a higher version number can get pulled instead. Transitive = you vet your 10 deps, but they pull 800 you never saw. ~5 min. -->

---

## SCA — find vulnerable deps

```bash
npm audit
docker run --rm -v "$PWD:/src" aquasec/trivy fs /src
owasp/dependency-check --scan /src --format HTML
```

- Produces CVEs + fix versions
- CWE-1104 (unmaintained), CWE-829 (untrusted inclusion)

<!-- Hands-on tooling (ties to W2 SCA). Run trivy live on the project — it lists CVEs + the fixed version. Q6 of the quiz asks for one real vulnerable dependency they found + remediation. ~4 min. -->

---

## Integrity: prove what you shipped

- **SBOM** (CycloneDX/SPDX) — ingredient list of the build
- **SLSA** — levels of build provenance & tamper-resistance
- **A08:2025** Software/Data Integrity Failures

<!-- SBOM = the food-label analogy: you can't manage what you can't list. When the next Log4Shell drops, an SBOM answers "are we affected?" in seconds. SLSA Build Track = levels L0–L3 of build provenance / tamper-resistance (L3 is the top; the old "1–4" numbering was v0.1 and is deprecated). ~5 min. -->

---

## Signing with Cosign (keyless)

```bash
trivy image --format cyclonedx -o sbom.json myapp:lab   # SBOM
cosign sign myapp:lab                                   # sign (OIDC)
cosign verify myapp:lab                                 # verify
```

- Unsigned/tampered image → verification fails

<!-- Demo the sign→verify loop. Keyless (Sigstore) = identity-based signing via OIDC, no key to leak. The deploy gate: refuse any image that doesn't verify → a tampered artifact can't ship. This is the lab's defend step. ~4 min. -->

---

## Tooling — GitHub Advanced Security (GHAS)

- **Secret scanning** + **push protection** — block secrets at push time (before they reach the remote)
- **CodeQL** code scanning — semantic SAST queries
- **Dependabot** — alerts + auto-PRs for vulnerable deps
- Native in the repo → results in the Security tab

<!-- The managed option students will meet in industry. Dependabot is the practical supply-chain workhorse: it opens PRs bumping vulnerable deps automatically. Push protection stops secrets at push time — local commits with a secret are allowed, the block fires on push to the remote (recall W2). ~3 min. -->

---

## Defenses

- Pin versions + lockfiles; scope internal registries
- Verify signatures before deploy (admission policy)
- Generate + store SBOMs per release
- 2FA/MFA on dev/CI/cloud accounts; least privilege
- Automate SCA in CI (next week)

<!-- The payoff checklist. Pin + scope kills dependency confusion; verify-before-deploy kills tampered artifacts; MFA on maintainer/CI accounts kills the xz/CircleCI vector. "Automate in CI" sets up W15. ~4 min. -->

---

## 📦 Game — Dependency Confusion Heist

1. **Attack:** in a controlled registry, plant/identify a typosquat or higher-version public pkg that gets pulled in
2. **Defend:** pin + scope; generate SBOM; sign & verify with Cosign; add a provenance gate

<!-- Explain before lab — all in a controlled local registry (ethics: never publish a real typosquat). Defend side is graded. The SLSA self-assessment makes them reason about their own pipeline. ~3 min. -->

---

## Deliverable

> 📋 **Worksheet 12** — `labs/week12-supply-chain/worksheet.md` (Part 3) · **kickoff:** `bash sca_scan.sh` (trivy fs + pip-audit)

- SCA report + remediation plan
- SBOM file + sign/verify transcript
- One-paragraph SLSA self-assessment (which level + why)
- **+ Audit the AI / EiPE / Prompt Problem** (see worksheet)

<!-- The SLSA self-assessment is the thinking part — they place their own build on the ladder and justify it. AI-resilient tasks count. -->

---

## Key takeaways

- Most of your attack surface is other people's code
- Know your ingredients (SBOM), prove your build (SLSA), sign your artifacts
- Verify before you trust

<!-- Recap with the three verbs. Cold-call: "the next Log4Shell drops at 2am — what artifact tells you if you're affected?" (the SBOM). ~2 min. -->

---

# Questions?
Next week: Cloud & container security

<!-- Cliffhanger: "Next week — where your code runs. We'll hunt cloud/container misconfigs, the #1 real-world breach cause." -->
