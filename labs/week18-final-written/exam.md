# Final — Written Exam (Week 18)

**Course:** Software Security (KOSEN69) · **Cumulative**, emphasis on **Weeks 10–15** (Week 16 is the capstone studio — no new examinable content)
**Time:** 150 min · **Total:** 100 pts

**Name:** ____________________  **Student ID:** ____________  **Date:** ________

> Reason about design and the pipeline, not just single bugs. Map findings to OWASP 2025 / API / LLM Top 10 / CWE.

---

![A blueprint diagram showing the Week 18 final exam covers Weeks 1-6 lightly, folds Weeks 7-9 midterm content into scope, weights Weeks 10-15 most heavily across six labeled topic blocks, excludes Week 16's capstone, breaks the 100 points into four sections split evenly between recall/identification and design reasoning, and contrasts this with Week 8's midterm which devoted 30 of 100 points to writing an actual exploit payload versus Week 18's zero.](img/exam-blueprint-final.svg)

## Section A — Modern-stack concepts (30 pts, 5 each)

A1. What is **BOLA** and why is it the #1 API risk? How does it differ from mass assignment?
A2. Explain **memory-safety mitigations** (canary, ASLR, NX, PIE) and why memory-safe languages are the real fix.
A3. Define **SBOM**, **SLSA**, and **artifact signing** — how they work together for supply-chain integrity.
A4. What is **security misconfiguration** (A02)? Give three concrete cloud/container examples.
A5. Explain **direct vs indirect prompt injection** with an example of each.
A6. What does a **CI security gate** check, and what condition should fail the build?

---

## Section B — Spot the Vulnerability (20 pts, 5 each)
*Name it (+ OWASP/CWE) and give the fix.*

B1.
```python
@app.get("/api/users/<id>/orders")
def orders(id): return db.orders_for(id)   # any caller, any id
```
B2.
```dockerfile
FROM ubuntu:latest
ENV AWS_SECRET=AKIA...
USER root
```
B3.
```python
reply = llm(system_prompt + user_input)
return f"<div>{reply}</div>"   # rendered as HTML
```
B4.
```c
char buf[64];
strcpy(buf, argv[1]);   // no bounds check
```

---

## Section C — Applied (30 pts, 10 each)

C1. Design the fix for the BOLA endpoint in B1: show the authorization check and explain deny-by-default.
C2. You ship a container image. Write the **steps + tools** to: scan it, generate an SBOM, sign it, and verify the signature before deploy.
C3. An LLM feature lets users ask questions over uploaded documents (RAG) and can call a "send email" tool. List three risks (with LLM IDs) and a mitigation for each.

---

## Section D — Design & DevSecOps (20 pts, 10 each)

D1. Design a **GitHub Actions security pipeline**: which scanners, what each catches, where SARIF goes, and the gate condition. Why "fail closed"?
D2. Pick one **notable supply-chain incident** (e.g. XZ Utils, SolarWinds, Log4Shell) and explain the attack path and two controls that would have reduced impact.

---

*End of exam. Pair with the Week 19 capstone CTF + project demos.*
