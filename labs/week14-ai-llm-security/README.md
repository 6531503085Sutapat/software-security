# Week 14 — Security of AI / LLM-Powered Applications

**OWASP Top 10 for LLM Applications (2025):** LLM01 Prompt Injection · LLM02 Sensitive Info Disclosure · LLM05 Improper Output Handling · LLM06 Excessive Agency · LLM08 Vector/Embedding Weaknesses · LLM10 Unbounded Consumption

## ✅ This week — what to do
1. **Before class** — Docker Desktop working (Week 1 *Lab 0*); skim last week's recap.
2. **Lecture (120 min)** — weekly quiz first (~10 min), then the lecture. Slides: `slides/week14.md`.
3. **Lab (180 min)** — play this week's game, then complete **Worksheet 14** (`worksheet.md`, Parts 1–4, incl. *Audit the AI* + *EiPE/Prompt*). Kickoff: `docker compose up → :6000 (insecure) / :6001 (guarded)`.
4. **Submit** — worksheet PDF → `learn.zcr.ai/submit` · code → GitHub · weekly quiz → `learn.zcr.ai/quiz`. (How: [SUBMISSION.md](../../SUBMISSION.md).)
5. **Project** — apply this week's lesson to your [NoteVault project](../../project/README.md) where it fits.

*Time breakdown: [AGENDA.md](../../AGENDA.md). Grading: see the worksheet rubric.*

## Objectives
- Explain the LLM Top 10 and where AI features add attack surface.
- Perform direct and indirect prompt injection.
- Add guardrails: input/output validation, least-privilege tools, output handling.

## 🧙 Signature game — "Gandalf Challenge"
Leaderboard by level reached.
1. **Direct prompt injection:** override the system prompt to reveal a hidden secret (Gandalf-style levels).
2. **Indirect injection:** plant a malicious instruction in a document the bot ingests (RAG) and trigger it.
3. **Improper output handling:** show model output flowing unsanitized into a downstream action (XSS/command).
4. **Agentic-AI / MCP risks (current, post-Oct 2025):** demo **tool poisoning** and **excessive agency** in an agent with tools (e.g. an MCP server) — a malicious instruction makes the agent call a tool it shouldn't.
5. **Fix (round 2):** input/output guardrails, strict output schemas/validation, **least-privilege tool access**, human-in-the-loop for sensitive tools, and rate/consumption limits; re-test.

## Deliverable
Attack log + mitigations + re-test, including the agent/MCP least-privilege design.

## References
- https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/
- https://gandalf.lakera.ai/
- MITRE ATLAS (AI/agentic attack techniques) — https://atlas.mitre.org/
