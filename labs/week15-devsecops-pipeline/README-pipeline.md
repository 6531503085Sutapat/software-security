<!-- Sandbox/teaching only; for authorized lab use. -->

# DevSecOps Pipeline — Wiring & Interpreting Results

**OWASP 2025:** A09 Security Logging & Alerting Failures, A10 Mishandling of
Exceptional Conditions (plus the scanners cover A02/A03).

This folder is a **lab template**. The workflow does not run from here; you
copy it into a repo's `.github/workflows/` directory.

---

## 1. Wire it in

```bash
# From the root of the repo you want to protect:
mkdir -p .github/workflows
cp path/to/labs/week15-devsecops-pipeline/security-ci.yml \
   .github/workflows/security-ci.yml
git add .github/workflows/security-ci.yml
git commit -m "ci: add security gate (Semgrep + Trivy + Gitleaks)"
git push        # the workflow runs on push/PR to main
```

No secrets are required: Semgrep, Trivy, and Gitleaks all run with the
free/public rule sets in this template.

---

## 2. What each job does

| Job | Tool | Scans for | Maps to |
|-----|------|-----------|---------|
| `semgrep`  | Semgrep  | Insecure code patterns (SAST) | OWASP Top 10 rules |
| `trivy`    | Trivy    | Vulnerable deps (SCA), IaC/Dockerfile misconfig, secrets | A03 / A02 |
| `gitleaks` | Gitleaks | Hard-coded secrets in code + git history | CWE-798 |

---

## 3. How the gate works (the important part)

Each tool runs **twice** on purpose:

1. **Report step** (`exit-code: 0` / `|| true`) — produces a SARIF file and
   uploads it to the GitHub **Security** tab. Uses `if: always()` so the
   SARIF uploads *even when the build is about to fail*.
2. **Gate step** (`exit-code: 1`, `--error`) — re-runs and **fails the build**
   if any HIGH/CRITICAL finding (or any secret) exists.

This ordering is deliberate: a single failing scan would abort before the
SARIF could upload, hiding the findings. Report-then-gate gives you both the
visible results *and* a red build.

> Why not just `|| true` everything? Because then the build never fails and
> the "gate" is decorative. Real gates must be able to say **no**.

---

## 4. Reading results

- **GitHub UI:** Security tab -> Code scanning alerts (from the SARIF uploads),
  and the Actions run log for the gate step that failed.
- **Severity:** the template gates on `HIGH,CRITICAL`. Tune in the workflow
  (`severity:` for Trivy, rulesets for Semgrep) as the class matures.
- **Triage:** fix, or document a justified, time-boxed exception. Do not
  blanket-ignore.

---

## 5. "Break the Build" game (see week15 README)

- **Blue:** keep the gate green by fixing findings.
- **Red:** open PRs that try to sneak past — e.g. add an old `urllib3` (Trivy
  SCA), a Dockerfile that runs as **root** — no `USER` line, or `USER root`
  (Trivy config, `DS-0002`, HIGH), or a hard-coded token (Gitleaks). One
  defect per job. A correctly-built gate turns the PR red.
- Don't reach for `chmod 777` here: both gate steps filter to
  `--severity HIGH,CRITICAL` and Trivy's Dockerfile scanner has no `chmod`
  rule at all, so it returns nothing and the build stays green. That makes it
  a *Red point* under §6 scoring, not a failing-gate screenshot.

## 6. Run the sample service locally (logging + fail-closed demo)

```bash
pip install flask
python sample-service.py
# In another shell:
curl -s -X POST localhost:5001/login -H 'Content-Type: application/json' \
     -d '{"token":"nope"}'                       # -> 401, logs authn_failure
curl -s localhost:5001/admin -H 'Authorization: bob-token'   # -> 403 authz_failure
curl -s localhost:5001/admin -H 'Authorization: alice-token' # -> 200 (admin)
```
Watch the structured `event=...` security log lines — those are what a SIEM
would alert on (A09). Note that errors deny by default (A10, fail-closed).
