<!-- Sandbox/teaching only; for authorized lab use. -->

# Dependency Confusion / Typosquat — Controlled Walkthrough

**OWASP 2025:** A03 Software Supply Chain Failures
**CWE:** CWE-1357 (reliance on insufficiently trustworthy component),
CWE-829 (inclusion of functionality from untrusted control sphere)

> This lab does not run a live private/public registry — `acme-internal-utils` is a worked example with
> no installable package behind it, on either side. The mechanism below is taught with the resolver's own
> rule and an interactive simulation (embedded in Worksheet 12 Task 2), not a real package pull. Never
> plant packages on the real PyPI/npm.

---

## The two attacks

### 1. Typosquatting
The attacker publishes a package whose name is a near-miss of a popular one
and waits for a fat-fingered `pip install`.

| Legit | Typosquat |
|-------|-----------|
| `requests` | `reqeusts`, `request` |
| `urllib3`  | `urlib3` |
| `python-dateutil` | `python-dateutil3` |

A single typo pulls attacker code that runs at install time
(`setup.py` / build scripts execute as you).

### 2. Dependency confusion (substitution)
A company uses an **internal** package, e.g. `acme-internal-utils`, that
exists only on its private registry. The attacker publishes a package with the
**same name** but a **higher version number** on the *public* registry. If the
build resolver checks both registries and simply prefers the highest version,
it pulls the attacker's public package instead of the internal one.

```
private registry:  acme-internal-utils == 1.4.0   (the real one)
public  registry:  acme-internal-utils == 99.0.0  (the attacker's)
resolver picks: ----------------------> 99.0.0     # confusion!
```

---

## Lab steps (simulated — there is no live registry)

1. **Read the rule.** In `--extra-index-url` (merged) mode, pip's resolver compares every version it can
   see across every configured index and installs whichever number is highest — it has no concept of which
   source is "trusted." In `--index-url` (single) mode, only the one configured index is ever queried; a
   same-named package on any other index is never fetched, regardless of its version.
2. **Watch it happen.** Worksheet 12 Task 2 embeds an interactive simulation that computes this rule live
   for the `acme-internal-utils` `1.4.0` (private) vs. `99.0.0` (public) example — set the mode, watch the
   verdict flip. This stands in for literally running `pip install acme-internal-utils`: there is no
   instructor registry serving that package in this lab, and the name does not exist on real PyPI either.
3. **The payload, conceptually.** If the public look-alike were real, its `setup.py` would run at install
   time — before any of your own code — and a benign version of that attack typically just writes a marker
   file (e.g. `PWNED.txt`) to prove code executed. No such file exists in this lab; it is the standard
   illustration of CWE-829 (functionality pulled from an untrusted control sphere), not something to
   reproduce here.

---

## Defenses (apply, then re-run step 2 — confusion should stop)

- **Pin + lockfile with hashes.** `pip install --require-hashes -r requirements.txt`
  (or a committed lockfile). A hash mismatch blocks substitution.
- **Scope / namespace internal packages.** Reserve the public name, or use a
  private namespace so a public package can never collide.
- **Single trusted index.** Don't merge public + private indexes; use
  `--index-url` (one source) not `--extra-index-url` (resolver shops around).
- **Allow-list / proxy registry.** Pull everything through one curated mirror
  (e.g. Artifactory/Nexus) that you control.
- **SCA in CI.** Flag newly-introduced or suspiciously-versioned packages
  (tie back to `sca_scan.sh`).

## Deliverable
A short note: the simulation's verdict in merged vs. single-index mode for the same version pair, plus
the one defense you found most effective and why.
