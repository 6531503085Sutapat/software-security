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

![A thin foundation band (Weeks 1-6, lighter weight) plus a wide emphasis band (Weeks 10-15, most of the exam weight: BOLA/mass-assignment/rate-limits, memory safety, SLSA/SBOM/Cosign, cloud IAM, prompt injection, DevSecOps gates) — Week 16 capstone isn't examinable. Section A (30, modern-stack concepts) and B (20, spot-the-vuln) test recall; C (30, applied design, no payload required) and D (20, pipeline/incident design) test design reasoning — 50/50. Unlike Week 8's midterm, which devoted 30 points to writing an actual SQL injection payload, Week 18 requires zero points of payload-writing: the shift is from writing exploits to designing fixes.](img/exam-blueprint-final.svg)

<!-- BOLA/API is the one people under-revise — it's 20 of 100 points across three sections, not a single "spot the vuln" line. The recall-vs-design 50/50 split and the explicit contrast with Week 8 (no payloads here) are the two framing points worth saying out loud. Show briefly; exam day — don't teach. -->

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
