---
marp: true
theme: default
paginate: true
header: "Software Security · Week 13"
---

# Week 13
## Cloud & Container Security
Software Security · Nutthakorn Chalaemwongwan

<!-- Hook: most cloud breaches aren't clever zero-days — they're a public S3 bucket or a `*:*` IAM policy. Today we hunt and fix those misconfigs. ~2 min. -->

---

## Today

- Shared-responsibility model
- IAM & least privilege
- Secrets management
- Container/image hardening
- 🎮 Game: **Misconfig Hunt**

<!-- Roadmap, 1 min. Theme: the cloud is secure; your CONFIGURATION usually isn't. Lab = find + fix misconfigurations, each one a flag. -->

---

## Recap & framing

- Supply chain → what you build with
- Today → where you run it
- **OWASP A02:2025 Security Misconfiguration** (now #2)

<!-- 1-min bridge. Misconfiguration jumped to A02 in 2025 — it's not a footnote, it's the second most critical web risk. ~2 min. -->

---

## Shared responsibility

- Cloud secures *of* the cloud; you secure *in* the cloud
- Misconfig — not provider bugs — causes most breaches
- Defaults are rarely safe

<!-- The mental model students most misunderstand: AWS secures the hardware/hypervisor; YOU secure your buckets, IAM, security groups. Almost every headline cloud breach is the customer's config, not the provider. ~4 min. -->

---

## IAM & least privilege

```json
{ "Effect":"Allow", "Action":"*", "Resource":"*" }   // 🚩
```

- Over-broad policies = blast radius
- `Resource:"*"` → **CWE-732** (incorrect permission assignment); `Action:"*"` → **CWE-269** (improper privilege management) — they're graded as two distinct findings on the *same* policy, not one
- Fix: scope to one bucket + one action, add a `Condition` (e.g. `s3:prefix`) — not just a narrower ARN

```sim
iam-scope
```

<!-- The worked example — this `*:*` policy is the Misconfig Hunt round 1 and the quiz. If a credential with this leaks, the attacker owns everything. This is 100% manual review — Trivy's config scanner does not parse standalone IAM JSON at all, say so explicitly so students don't wait for a scanner to flag it. The sim scores Action and Resource independently, live, so "two findings, not one" is something they watch instead of a claim on a slide. Least privilege = smallest possible blast radius. ~6 min. -->

---

## Secrets management

- Secrets in env vars / Dockerfile / git = leaked
- Use a secrets manager / vault; rotate
- Scan history (Gitleaks) — recall Week 2

<!-- Connect to W2 (Gitleaks) and W12. A secret baked into an image layer is in every copy of that image forever — `docker history` reveals it. Fix = inject at runtime from a vault + rotate. ~4 min. -->

---

## Storage & network exposure

- Public buckets, open ports, default creds
- Encrypt at rest + in transit
- Private by default; explicit allow

<!-- The classic trio behind most breaches. `0.0.0.0/0` on a DB port = the internet can reach your database. Default creds = free entry. Principle: deny by default, open deliberately (echoes W6 access control). ~4 min. -->

---

## Container image hardening

```bash
docker run --rm -v "$PWD:/src" aquasec/trivy config /src                    # misconfig
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image week13-hardened:lab                              # image CVEs
```

- Multi-stage build: `python:3.11-slim@sha256:...` (compiles) → **distroless** `gcr.io/distroless/python3-debian12@sha256:...` (runs) — a smaller runtime image with no shell/package manager, `USER 65532:65532` (non-root)
- `@sha256:...` **digest** pins, not just a version tag — a tag can be repointed later, a digest can't
- Re-scan to prove reduced findings
- **Trivy only catches 3 of 6 planted defects** (`:latest`, root user, secret-in-ENV) — `COPY . .`, `chmod -R 777`, and unpinned `pip install` need **manual review**, no rule fires

<!-- Hands-on — this is the lab's insecure→hardened Dockerfile, always run dockerized (never a bare local trivy binary), against week13-hardened:lab (not a generic myapp:lab). The Trivy-blind-spot point is the actual lesson of this lab, not an aside — half the graded findings need a human, not a tool. Re-scan to prove improvement. ~5 min. -->

---

## Kubernetes basics (awareness)

- Pod security, network policies, RBAC
- Don't run privileged; limit service-account tokens

<!-- Awareness only (K8s is its own course). Key takeaways: a privileged pod ≈ host root; mounted service-account tokens are a lateral-movement prize. Keep it brief. ~3 min. -->

---

## Same app, shipped twice

![The same app as two container images side by side, insecure vs hardened, six layers compared: mutable :latest tag vs a pinned digest, a baked-in secret vs runtime injection, root user vs distroless non-root, COPY-everything vs a minimal context, world-writable permissions vs read-only, and an unpinned pip install vs a discarded build stage. Below both, the same argument one layer up: the wildcard IAM policy vs the scoped one. The conclusion: Trivy flags only three of the seven defects shown here — the tag, the root user, and the secret. COPY .., chmod 777, the unpinned install, and the IAM JSON all need manual review; there is no rule for any of them.](img/container-hardening.svg)

<!-- The whole lab's argument as one picture — walk it row by row once, landing on the Trivy split at the bottom: 3 rows have a rule ID to cite, 4 don't. That 3-of-7 (or "3 of 6" container-only, per the earlier slide) split is Task 1's actual grading rubric, not trivia. ~5 min. -->

---

## 🔍 Game — Misconfig Hunt

**9 flags** — each misconfiguration **found + explained** = a flag:

1. **Container (6):** `:latest` tag, root user, secret-in-ENV, `COPY . .`, `chmod -R 777`, unpinned `pip install`
2. **IAM (3):** `Resource:"*"` (CWE-732), `Action:"*"` (CWE-269), missing `Condition` scoping

<!-- Explain before lab: 9 flags total, two categories only — no separate bucket/storage flag, no IaC/localstack target exists in this lab. Find AND explain (why it's a finding, which fix applies) = the flag. Q6 of the quiz asks for one misconfig they explained + the principle it violated. ~3 min. -->

---

## Deliverable

> 📋 **Worksheet 13** — `labs/week13-cloud-container/worksheet.md` (Parts 1–4) · **kickoff:** `bash scan.sh` (trivy config over the **Dockerfiles only** — IAM JSON is manual review, Trivy doesn't parse it)

- Before/after IAM policy + Dockerfile, all 9 flags explained
- Trivy reports showing reduced risk (container half only)
- Note on secrets remediation
- **+ Audit the AI / EiPE / Prompt Problem** (see worksheet)

<!-- Before/after artifacts + the trivy delta prove the container-side fix; IAM has no scanner delta to show, it's reasoned/written. Don't let "trivy over Dockerfiles + IAM JSON" stand — that's the exact misconception this lab's own history already fixed once. AI-resilient tasks count. -->

---

## Key takeaways

- Misconfiguration > zero-days as a breach cause
- Least privilege, private-by-default, no secrets in code
- Scan IaC and images in CI

<!-- Recap. Cold-call: "what does a `*:*` IAM policy cost you if the key leaks?" (everything — full blast radius). "Scan in CI" sets up W15. ~2 min. -->

---

# Questions?
Next week: AI / LLM application security

<!-- Cliffhanger: "Next week — the newest attack surface: make an AI assistant ignore its rules and leak secrets, with nothing but text." -->
