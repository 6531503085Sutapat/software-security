# Week 7 — Mock CTF (Midterm dry-run)

**Covers:** Weeks 1–6 · **Format:** same as the Week 9 midterm practical · **Ungraded** (participation).
**Time:** ~150 min · individual or pairs · Sandbox targets only (ethics policy applies).

> This is practice — **hints are included** and solutions point back to the labs. No real
> exam flags here. Goal: get comfortable with the format so Week 9 has no surprises.

![A revision map of weeks 1 to 6: each week's core idea and OWASP/CWE tag, arranged so untrusted input crosses a trust boundary and the week's control sits at the crossing](img/revision-map.svg)

**Targets:** `labs/week03-cryptography`, `labs/week04-injection`, `labs/week05-xss-client-side`,
`labs/week06-authn-authz` (`docker compose up` in each).

| # | Challenge | Topic | Hint | Self-check |
|---|-----------|-------|------|-----------|
| 1 | Log in as another user without their password | SQLi (W4) | the username field isn't parameterized | `solution_app.py` |
| 2 | Run a command on the server | cmd injection (W4) | `host` is passed to a shell | `solution_app.py` |
| 3 | Pop `alert(1)` that another user would trigger | stored XSS (W5) | the comment body is rendered raw | `fixed_app.py` (CSP) |
| 4 | Read an order that isn't yours | IDOR (W6) | change the id; no ownership check | `attack.md` |
| 5 | Become admin with a crafted token | weak JWT (W6) | `alg:none` / weak secret `"secret"` | `attack.md` |
| 6 | Recover a password from its hash | crypto (W3) | unsalted MD5 + a wordlist | `solution_skeleton.py` |

**For each:** note your payload/command + a one-line fix. Compare with the linked solution.

## Warm-up (concepts)
- Draw a 3-element STRIDE table for any one target above.
- Name the CWE for each challenge you solved.

> Then take the **[cumulative review quiz (Quiz 1)](../../quizzes/quiz1.md)** this week,
> and review weak spots before the Week 8/9 midterm.
