# Week 17 — Mock CTF (Final dry-run)

**Covers:** whole term, emphasis Weeks 10–16 · **Format:** same as the Week 19 final CTF · **Ungraded** (participation).
**Time:** ~165 min · teams · Sandbox targets only (ethics policy applies).

> Practice run with **hints**; solutions point back to the labs. No real exam flags.

![Final revision map for weeks 10 to 16: three spine boxes state that a control must sit at a boundary (W10), be on by default (W11) and fail closed (W15), over a table giving each week's core flaw, OWASP or CWE tag, and the first-half week it builds on.](img/revision-map-final.svg)

**Targets:** `labs/week10-api-security`, `labs/week11-memory-safety-exploitation`,
`labs/week12-supply-chain`, `labs/week13-cloud-container`, `labs/week14-ai-llm-security`
(+ a callback to the web half).

| # | Challenge | Topic | Hint | Self-check |
|---|-----------|-------|------|-----------|
| 1 | Read another user's orders via the API | BOLA (W10) | id in the URL, no authz | `solution_api.py` |
| 2 | Create a user you shouldn't be able to | mass assignment (W10) | smuggle `is_admin` in the body | `solution_api.py` |
| 3 | Reach `win()` in the binary | stack overflow (W11) | offset 72 → overwrite RA; `objdump` for `&win` | `exploit_skeleton.py` |
| 4 | Make the binary crash with a fuzzer | fuzzing (W11) | `clang -fsanitize=address,fuzzer fuzz_harness.c` | `safe.rs` (the fix) |
| 5 | Find the vulnerable dependency / unsigned image | supply chain (W12) | `trivy fs` / `cosign verify` | `sign.sh`, `sca_scan.sh` |
| 6 | Spot the IAM/secret/root misconfig | cloud (W13) | `trivy config`; read `Dockerfile.insecure` | `harden.md` |
| 7 | Make the chatbot leak its secret | prompt injection (W14) | override the system instruction | `guarded_chatbot.py` |
| 8 | Callback: any one web bug from W4–6 | web | reuse a midterm technique | week04–06 solutions |

**For each:** payload/command + one-line mitigation; compare with the linked solution.

## Warm-up (concepts)
- For any 2 challenges, give the OWASP 2025 / API / LLM id + CWE.
- One sentence: which control would have prevented it in CI?

> Review weak spots, then the Week 18 written + Week 19 capstone CTF.
