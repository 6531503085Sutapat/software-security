---
marp: true
theme: default
paginate: true
header: "Software Security · Week 6"
---

# Week 6
## Authentication, Sessions & Access Control
Software Security · Nutthakorn Chalaemwongwan

<!-- Hook: change /orders/1 to /2 and read a stranger's data — promise that demo. The #1 web risk in 2025 is Broken Access Control, and it's mostly missing one check. ~2 min. -->

---

## Today

- Authn vs authz
- Session management & JWT pitfalls
- OAuth2 / OIDC at a glance
- IDOR & broken access control
- 🎮 Game: **IDOR Treasure Hunt + JWT Forgery**

<!-- Roadmap, 1 min. This is the last teaching week before review/midterm — flag that. Lab = exploit IDOR + forge a JWT, then implement RBAC + proper verification. -->

---

## Recap — Week 5

- XSS steals sessions → today we manage them
- Client-side trust is limited — enforce on the server

<!-- 1-min bridge. XSS could steal a session token; today: what IS that token, and how do we stop theft + misuse? Theme of the week: enforce on the server, every request. -->

---

## Authn vs Authz

- **Authentication** — *who are you?* (login, MFA)
- **Authorization** — *what are you allowed to do?*
- Most breaches today are **authz** failures
- Maps to **A01 Broken Access Control**, **A07 Authentication Failures**

<!-- The distinction students most often blur — make them repeat it. Authn = identity; authz = permission. A01 is #1 in OWASP 2025 precisely because authz checks get forgotten. Ask for an example of each failing. ~5 min. -->

---

## Sessions

- Server issues a session token after login
- Stored in cookie (`HttpOnly`, `Secure`, `SameSite`)
- Risks: fixation, predictable IDs, no expiry, no logout invalidation

<!-- Connect cookie flags to W5: HttpOnly stops XSS theft, SameSite stops CSRF, Secure forces HTTPS. Explain session fixation briefly (attacker sets the id before login). ~5 min. -->

---

## JWT pitfalls

```text
header.payload.signature
```

- `alg: none` accepted → forge any token
- Weak/guessable HMAC secret → re-sign
- Not checking `exp` / `aud` / signature at all
- Sensitive data in payload (it's only base64!)

<!-- Decode a JWT live (jwt.io) to show the payload is just base64 — NOT encrypted. The `alg:none` attack is the JWT Forgery game: server trusts the header's claimed algorithm. Emphasize: never put secrets in the payload. ~7 min. -->

---

## OAuth2 / OIDC (high level)

- Delegated access via tokens — don't share passwords
- OIDC adds identity (ID token) on top of OAuth2
- Common bugs: open redirect, missing state, token leakage

<!-- Keep high-level (full OAuth is its own course). Key idea: "Login with Google" = delegation, you never give the app your Google password. The `state` parameter prevents CSRF on the callback. ~4 min. -->

---

## IDOR & broken access control

```text
GET /api/orders/1   → your order
GET /api/orders/2   → someone else's  😱
```

- Object reference with no ownership check
- Vertical (become admin) vs horizontal (other users)

<!-- The worked example — this is the IDOR Treasure Hunt. The server authenticated you but never checked the object BELONGS to you. Horizontal = peer data; vertical = privilege escalation. ~6 min. -->

---

## Access control models

- **MAC** — Mandatory: system-enforced labels (military)
- **DAC** — Discretionary: owner grants access (file perms)
- **RBAC** — Role-Based: permissions via roles
- **RuBAC** — Rule-Based: conditions (time of day, IP)

> Best practices: separation of duties · least privilege · implicit deny

<!-- Quick taxonomy; RBAC is what they'll implement in the lab. Stress the three best-practice principles — especially implicit deny (default to no access). ~4 min. -->

---

## Exercise — RBAC

| Role | Permissions |
|---|---|
| Developer | Read/write Git, JIRA, run unit tests |
| QA Engineer | Read Git, write test reports, JIRA, **deploy to staging** |
| Project Manager | Read Git, JIRA, view dashboard |
| Intern | Read Git, run unit tests |

1. Who may deploy to staging?
2. An intern must create bug entries — which role's perms to add?
3. List all roles that can modify the codebase.

<!-- Run this interactively — give 2 minutes, then poll answers. (1) QA only. (2) add JIRA-write, narrowly (least privilege, not a full role bump). (3) Developer (write Git); discuss whether QA's staging deploy counts. ~6 min. -->

---

## Reading the attack in the logs

Reconstruct the kill chain from Apache logs:

```text
GET /login.php?username=' or 1=1 limit 1; -- a&...   302   ← SQLi admin
POST /upload.php                                     200   ← backdoor
GET /uploads/backdoor.php?cmd=ls%20-l                200   ← RCE
```

- `%20` = space (URL-decode!) · logs let you trace what happened

<!-- Ties W4 (SQLi auth bypass + upload→RCE) into incident response. Walk the three lines as a story: get in → plant webshell → run commands. Teach URL-decoding (%20=space). Defenders read logs; attackers leave them. ~5 min. -->

---

## CWE mapping

- **CWE-639 / CWE-284** — IDOR / improper access control
- **CWE-287** — improper authentication
- **CWE-345 / CWE-347** — insufficient verification / bad signature

<!-- Reference for the worksheet. ~1 min. -->

---

## Defenses

- **Server-side authorization on every request** (deny by default)
- Check ownership, not just authentication
- Strong session tokens + proper expiry/rotation
- Verify JWT signature, `alg`, `exp`, `aud`; keep secrets strong
- RBAC / ABAC enforced centrally
- **Centralize** the check — don't scatter `if role==...` everywhere

<!-- The payoff. #1: authorize EVERY request, deny by default. "Check ownership, not just authentication" is the IDOR fix in one line. Centralize so you can't forget a check on one endpoint. ~6 min. -->

---

## Tool — Burp Suite workflow

| Tool | Use |
|---|---|
| **Proxy** | intercept & modify requests |
| **Repeater** | replay/tweak one request |
| **Intruder** | automate brute-force/fuzz |
| **Decoder/Comparer** | encode payloads / diff responses |

- Set **scope**, intercept, change a value (e.g. `price=1`), forward
- Test auth, sessions, **IDOR**, privilege escalation

<!-- Practical — they'll use Repeater to tweak object ids and Intruder to enumerate. Demo: intercept, change orders/1→2, forward, see another user's data. Set scope first so you don't attack out-of-bounds. ~5 min. -->

---

## 🗺️ Game — IDOR Treasure Hunt + JWT Forgery

1. Tamper object IDs to reach other users' data → each secret = a flag
2. Forge a weak JWT to become **admin**
3. **Round 2:** implement RBAC checks + fix token signing/verification

<!-- Explain before lab. Treasure hunt = enumerate ids for per-student flags. JWT forgery = alg:none or crack a weak secret. Round 2 (fix it) is graded. ~3 min. -->

---

## Lab steps

> 📋 **Worksheet 6** — `labs/week06-authn-authz/worksheet.md` (Part 3) · **kickoff:** `docker compose up` → http://localhost:8080

1. Find IDOR endpoints; enumerate other users' objects
2. Crack/forge a weak JWT (e.g. `alg:none` or weak secret)
3. Add ownership checks + proper JWT verification
4. Re-test: access denied

<!-- Logistics. Step 3-4 (defend + prove denial) graded. Q6 of the quiz asks for the object id they used + the fix + their personal flag. Also the NoteVault project access-control task. -->

---

## Deliverable

- IDOR + JWT findings with impact
- Fixed authorization + token handling
- Proof the forged token / cross-user access now fails
- **+ Audit the AI / EiPE / Prompt Problem** (see worksheet)

<!-- Before/after + proof. AI-resilient tasks count. -->

---

## Key takeaways

- Authenticate once, **authorize every request**
- Never trust client-supplied IDs or tokens blindly
- Deny by default

<!-- Recap. Cold-call: "we authenticated the user — why can they still read another user's order?" (no ownership/authz check). ~2 min. -->

---

# Questions?
Next week: Reflection & review (midterm prep)

<!-- Wrap the teaching block: "Next week we consolidate W1-6 — Jeopardy + a mock CTF in the exact midterm format. Bring your cheat-sheet of CWEs." Remind cumulative review quiz in W7. -->
