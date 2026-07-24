---
marp: true
theme: default
paginate: true
header: "Software Security · Week 14"
---

# Week 14
## Security of AI / LLM-Powered Applications
Software Security · Nutthakorn Chalaemwongwan

<!-- Hook: it's 2026 — your students will all ship AI features. Show that a single sentence can make an AI assistant ignore its rules and leak a secret. No exploit code, just text. ~2 min. -->

---

## Today

- Where AI features add attack surface
- OWASP **LLM Top 10 (2025)**
- Prompt injection (direct + indirect)
- Agentic-AI / MCP risks
- 🎮 Game: **Gandalf Challenge**

<!-- Roadmap, 1 min. Big idea: prompt injection IS injection (W4) — untrusted data interpreted as instructions. Everything they learned applies. Lab = beat Gandalf, then add guardrails. -->

---

## Why a whole week on AI

- LLMs now sit inside real products & agents
- New, fast-moving attack surface
- OWASP LLM Top 10 + MITRE ATLAS

<!-- Justify the week: this is the most current, fastest-moving area in the course. Note the field changes monthly — what they learn is the THINKING, not a fixed list. OWASP LLM Top 10 + MITRE ATLAS are the references. ~3 min. -->

---

## OWASP LLM Top 10 (2025)

| | | |
|---|---|---|
| LLM01 Prompt Injection | LLM02 Sensitive Info Disclosure | LLM03 Supply Chain |
| LLM04 Data/Model Poisoning | LLM05 Improper Output Handling | LLM06 Excessive Agency |
| **LLM07 System Prompt Leakage** | LLM08 Vector/Embedding | LLM09 Misinformation |
| LLM10 Unbounded Consumption | | |

> **New in 2025:** LLM07 System Prompt Leakage · LLM08 promoted (RAG everywhere) · LLM10 replaces "DoS" with runaway *cost*.

<!-- Don't read all 10 — highlight the 2025 changes. LLM07 (system-prompt leakage) is new because devs hid secrets in prompts. LLM10 reframed as runaway COST (an agent loop can run up a huge bill). ~4 min. -->

---

## Prompt injection

> Untrusted text overrides the system's instructions — injection, again.

- **Direct:** user tells the bot to ignore its rules
- **Indirect:** malicious instructions hidden in a fetched doc / web page (RAG)

<!-- The core concept — say "this is W4 injection in a new interpreter (the LLM)." Direct = the Gandalf game. Indirect is the scary one: the payload rides in a document/email/web page the model reads, so the victim never typed it. ~6 min. -->

---

## Improper output handling

- Model output flows unsanitized into HTML/SQL/shell
- → XSS / injection downstream
- Treat LLM output as **untrusted input**

<!-- Crucial and overlooked: the LLM's OUTPUT is attacker-influenced data. If you drop it into innerHTML you get XSS (W5); into a query, SQLi (W4). The rule from W5 returns: encode for the context, validate before use. ~4 min. -->

---

## Real-world incidents

- **Bing Chat "Sydney" (2023):** a typed *"ignore previous instructions"* leaked the hidden system prompt — **direct** injection
- **EchoLeak (2025):** *zero-click* **indirect** injection in M365 Copilot → data exfil (CVE-2025-32711)
- **Agentic tool-abuse:** injected web/email content makes a tool-using agent take real actions (send mail, move funds, run code) — it trusts the text as instructions
- **Résumé injection:** hidden white text inflated an AI screening score

> Injection needs no exploit code — just text the model trusts.

<!-- EchoLeak is the headline: zero-click — the victim just receives an email Copilot later reads, and data exfiltrates. No link clicked. Résumé injection makes it relatable (white-on-white text gaming an AI screener). ~5 min. -->

---

## Agentic-AI / MCP risks (2025+)

- Agents call tools (e.g. via **MCP**) → real-world actions
- **Tool poisoning**, **excessive agency**, RCE via tools
- MITRE ATLAS added agent techniques (Oct 2025)
- Research: **43%** of public MCP servers had command-injection flaws

<!-- The frontier — and where THEY will build. The moment an LLM can call tools, injection becomes real-world ACTIONS (send money, run code). The 43% MCP stat lands: the ecosystem is young and insecure. ~5 min. -->

---

## Real MCP/agent incidents (2025)

- **Supabase × Cursor:** privileged agent read a support ticket with injected SQL → leaked integration tokens (privileged access + untrusted input + exfil channel)
- **Invariant Labs:** a malicious trivia MCP server's *tool description* hijacked a trusted WhatsApp MCP → exfiltrated chats
- **MCPoison (CVE-2025-54136):** approved-then-swapped MCP config in Cursor → silent RCE on every session

> The danger pattern: **privilege + untrusted input + an outbound channel.**

<!-- Drive the pattern home — it's the unifying lesson: an exploit needs privilege + untrusted input + a way out. Break any one leg and the attack fails (that's what the defenses do). The tool-DESCRIPTION attack surprises everyone. ~5 min. -->

---

## Defenses

- Input/output **guardrails** + content filtering
- Strict output **schemas/validation**; encode before downstream use
- **Least-privilege tool access** + human-in-the-loop for sensitive actions
- Rate/consumption limits; isolate untrusted content in RAG

<!-- The payoff — map each defense to a leg of the pattern: least-privilege tools cut PRIVILEGE; isolating RAG content cuts UNTRUSTED INPUT; egress limits + human approval cut the OUTBOUND CHANNEL. No single guardrail is enough; layer them. ~5 min. -->

---

## 🧙 Game — Gandalf Challenge

1. Beat Gandalf levels via **direct + indirect prompt injection** → exfiltrate the secret (leaderboard by level)
2. Demo **tool poisoning / excessive agency** on an agent with tools
3. **Round 2:** add guardrails + least-privilege tools, re-test

<!-- Gandalf (Lakera) is genuinely fun and free — students compete to climb levels. Round 2 (build guardrails + least-privilege tools) is graded. Q6 of the quiz asks for the injection that captured the flag + why the guardrail failed. ~3 min. -->

---

## Deliverable

> 📋 **Worksheet 14** — `labs/week14-ai-llm-security/worksheet.md` (Part 3) · **kickoff:** `docker compose up` → :6000 (insecure) / :6001 (guarded)

- Attack log (which injection beat which level)
- Mitigations + re-test results
- Least-privilege agent/MCP tool design
- **+ Audit the AI / EiPE / Prompt Problem** (see worksheet)

<!-- The least-privilege tool design is the thinking deliverable. Especially fitting this week: the Audit-the-AI task critiques an AI's own (insecure) answer. -->

---

## Key takeaways

- Prompt injection = injection; LLM output = untrusted
- Constrain agency: least-privilege tools, human approval
- The field moves monthly — track OWASP LLM + ATLAS

<!-- Recap. Cold-call: "the agent read a malicious email and wired money — which leg of privilege+input+channel would you cut, and how?" ~2 min. -->

---

# Questions?
Next week: DevSecOps — putting it together

<!-- Cliffhanger: "Next week we wire the whole course into one CI/CD pipeline — Red vs Blue: sneak a vuln past the gate, or block it." -->
