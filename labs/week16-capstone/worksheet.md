# Worksheet 16 — Capstone Studio & CTF Warm-up (4 hrs)

> **Course:** Software Security (KOSEN69) · Week 16
> **Aligned to:** All prior weeks + OWASP Top 10 (2025) — https://owasp.org/Top10/2025/ ; CWE mapping required throughout.
> **Signature game:** practice **CTF tournament** (web · API · supply-chain · LLM) previewing Week 19, plus cross-team peer review.

> ⚠️ **Ethics note:** This is a **project studio**, not an exploit lab. Demo your attack → root cause → fix **only** against your own term-project application (the [term project](../../project/README.md)) or the provided practice-CTF targets. The graded final presentation + full CTF tournament are in **Week 19**; this week is the work-in-progress warm-up.

---

## Part 1 — Student Information

| Name | Student ID | Date | Group |
|------|-----------|------|-------|
|      |           |      |       |

---

![A capstone lookup table pairing each OWASP Top 10 (2025) category with the week that taught it, the lab file that demonstrated it and a representative CWE, with A01, A03 and A05 marked as the course's deepest coverage.](img/owasp-map.svg)

## Part 2 — Lecture Questions

Answer as a team (2–4 sentences each).

1. State your project's **top-3 risks** from your threat model and the STRIDE/attack category each falls under.
2. For your headline vulnerability, give its **CWE id** and **OWASP 2025** category, and one sentence on root cause.
3. What does your **SBOM** cover, how was it generated, and what would you do if a dependency in it got a new CVE next week?
4. How is your build artifact **signed**, and how would a consumer verify the signature (and why does signing matter for supply-chain trust)?
5. Which **CI gate(s)** from Week 15 (Semgrep / Trivy / Gitleaks, fail-closed on HIGH/CRITICAL) does your pipeline enforce, and what does a failing build look like?

---

## Part 3 — Project Checklist & Demo Rubric

> Replaces the hands-on exploit lab. Bring the deliverables below to the studio; run the 10-min demo + 5-min Q&A; complete a peer review of another team.

### A) Deliverables checklist (bring all six)

| # | Deliverable | Done? | Evidence to show |
|---|-------------|:-----:|------------------|
| 1 | **Threat model** | ☐ | Data-flow diagram + trust boundaries; top risks ranked (STRIDE) |
| 2 | **Vulnerability report** | ☐ | Each finding mapped to **CWE + OWASP 2025**, with severity and PoC |
| 3 | **Fixed code** | ☐ | Before/after diff for each finding; root cause noted |
| 4 | **SBOM** | ☐ | Machine-readable (CycloneDX / SPDX) covering all dependencies |
| 5 | **Signed artifact** | ☐ | Signature + the exact verification command a consumer runs |
| 6 | **CI pipeline** | ☐ | Security gate (Week 15 style) that **fails closed** on HIGH/CRITICAL; link to a run |

### B) 10-min demo + 5-min Q&A structure

| Time | Segment | Content |
|------|---------|---------|
| 0:00–1:30 | Context | App purpose, threat model, trust boundaries |
| 1:30–4:30 | **Attack** | Live exploit of your headline vuln (or recorded fallback) |
| 4:30–6:30 | **Root cause** | Why it was possible; CWE/OWASP mapping |
| 6:30–9:00 | **Fix + verify** | Show the patch, re-run the attack to prove it's blocked |
| 9:00–10:00 | Supply chain | SBOM, signed artifact, and CI gate catching a regression |
| 10:00–15:00 | **Q&A** | Cross-team questions + instructor |

### C) Peer-review rubric (score the team you review, 1–5 each)

| Criterion | 1 (weak) → 5 (strong) |
|-----------|------------------------|
| Threat model completeness | Missing boundaries → thorough, ranked, realistic |
| Vulnerability mapped to CWE/OWASP | Vague → precise id + accurate severity |
| Exploit clarity | Hand-wavy → clear, reproducible PoC |
| Remediation quality | Superficial → root-cause fix, re-tested |
| SBOM + signing | Absent → complete + verifiable |
| Pipeline / fail-closed | None → gate fails closed on HIGH/CRITICAL |
| Demo & Q&A | Unclear → confident, handles tough questions |

> Practice CTF: a short scrimmage mixing web, API, supply-chain, and LLM challenges from Weeks 1–15. Record flags captured and which week's technique each used — this previews the Week 19 final.

---

## Part 4 — Reflection (Lessons Learned)

1. **Lessons learned.** What surprised your team most while threat-modeling and fixing your own app?
2. **What you'd harden next.** Given more time, which control would you add first (e.g., least-privilege IAM, image hardening, output handling, fail-closed paths), and why?
3. **CTF takeaway.** Which practice-CTF category was hardest for your team, and what will you drill before Week 19?

---

## Grading rubric (100)

| Component | Points | What earns full marks |
|-----------|:------:|-----------------------|
| Threat model | 15 | Complete DFD, trust boundaries, ranked risks (STRIDE) |
| Exploitation | 20 | Working PoC of a real vuln, clearly demoed |
| Remediation | 20 | Root-cause fix with before/after + re-test proving it's closed |
| SBOM & signing | 15 | Complete SBOM + verifiable signed artifact |
| CI pipeline | 15 | Security gate fails closed on HIGH/CRITICAL; run linked |
| Demo & Q&A | 15 | Clear 10-min demo, handles 5-min Q&A; CWE/OWASP mapping throughout |

---

## Evidence & Integrity (required)

- **Identity proof:** every screenshot/diagram must show a terminal running `printf '%s | %s | ' "$(whoami)" '<YOUR-STUDENT-ID>'; date '+%F %T %Z'` **in the
  same image as the evidence**. When the evidence is a browser page, a DevTools panel or a
  rendered response, put that terminal **beside the browser and capture the whole screen** — a
  cropped window carries nothing that identifies you, and the lab's own output is
  byte-identical for the whole cohort *by design*, so the stamp is the only thing that makes
  the shot yours. Generic or borrowed evidence is not accepted.
- **Personalized flag (if this lab issues one):** ____________________
  *Flags are unique per student — submitting another student's flag is a violation. See [SUBMISSION.md](../../SUBMISSION.md).*
- **Explain in your own words** *(graded on your reasoning, not copied text):*
  1. What did you do, and **why did the vulnerability work**?
  2. **Why does your fix actually stop it** — and what could still break it?

---

## 🤖 Audit the AI (required)

AI is a power tool you must **distrust** — you are graded on your *critique*, not the AI's answer.

1. Ask an AI assistant to exploit **or** fix this week's vulnerability. Paste its full answer.
2. **Find what's wrong or risky** in it — insecure code, a subtly incomplete fix, a hallucinated API/function/CVE, a missed edge case, or wrong reasoning. Quote the exact line(s).
3. Produce the **correct, verified** version yourself and explain in 2–3 sentences why the AI's output was insufficient.

> Disclose your AI use in the Part 1 table. This task counts toward your **Defense + Reflection** score.

---

## 🧠 Comprehension & Prompt (required)

**A. Explain in Plain English (EiPE).** In 2–3 sentences, in your own words, describe what this week's vulnerable code/endpoint actually *does* and *why it is exploitable* — explain the mechanism, don't dump jargon.

**B. Prompt Problem.** Write a **single prompt** that makes an AI produce a *correct, secure* fix for one finding. Run it: does the exploit now fail? If not, refine the prompt and try again. Submit the **final prompt + the verified result**.
*Graded on the prompt's precision and your verification — this trains problem decomposition and AI literacy (Denny et al. 2024).*
