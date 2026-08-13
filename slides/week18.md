---
marp: true
theme: default
paginate: true
header: "Software Security · Week 18 · Final"
---

# Week 18
## Final — Written Exam
Cumulative · emphasis on Weeks 10–15

<!-- Proctor deck. Week 16 is the capstone studio — no new examinable content, don't imply it's in scope. Before start: confirm exam version (rotate from exams/item-bank.md final pool), time, open/closed-note, integrity (no AI/phones). Keep talk minimal once the clock runs. -->

---

## Format

- Duration: **150 minutes** · 100 pts
- Cumulative, emphasis Weeks 10–15 (Week 16 capstone is not separately examined)
- 4 sections: A Modern-stack concepts (30) · B Spot the Vuln (20) · **C Applied (30)** · D Design & DevSecOps (20)

<!-- State the section split exactly as printed. All 15 graded items map into the Weeks 10–15 block — this is closer to cumulative-in-name-only than a 60/40 split, say so if asked. -->

---

## What's assessed

- **API security / BOLA** — object-level authorization across A/B/C (20 pts total, not a single bullet's worth)
- Supply-chain integrity (SLSA / SBOM / Cosign)
- Cloud & container misconfiguration (concrete examples, not IAM-specific)
- LLM & agentic threat modeling
- DevSecOps gate design
- Memory-safety mitigations & Secure-by-Design tradeoffs

<!-- BOLA/API is the one people under-revise — it's 20 of 100 points across three sections, not a single "spot the vuln" line. Show briefly; exam day — don't teach. -->

---

## Tips

- Reason about design, not just single bugs
- Always name the mitigation + where it belongs in the pipeline
- Map every finding to **OWASP 2025 / API Security Top 10 / LLM Top 10 / CWE**

<!-- Key score-saver for the final: it rewards DESIGN reasoning (where the fix belongs), not just bug-spotting — and don't drop "API" from the mapping list, BOLA is graded. Say once, then start. -->

---

# Good luck
Week 19: capstone CTF tournament + project demos

<!-- Close: remind W19 = team CTF + graded demos; bring runnable project + SBOM/signed artifact/pipeline. Grade with exams/week18-…-answers.md. -->
