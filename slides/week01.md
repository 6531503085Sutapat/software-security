---
marp: true
theme: default
paginate: true
header: "Software Security · Week 1"
---

# Week 1
## Security Mindset & Threat Modeling
Software Security · Nutthakorn Chalaemwongwan

<!-- Welcome the class. One line: "By the end of today you'll be able to look at any system and ask the right 'what could go wrong' questions — and write them down in a way engineers can act on." Set the tone: this course is hands-on; we break things in a sandbox to learn to defend them. ~2 min. -->

---

## Today

- What "secure" means (CIA)
- Attacker vs. defender mindset
- Trust boundaries & attack surface
- STRIDE + the OWASP/MITRE landscape
- **Secure by Design**
- 🎲 Game: **Elevation of Privilege** · Lab 0 setup

<!-- Roadmap slide — 1 min. Tell them the lecture is ~2 h, then a 3 h lab where they threat-model a real app, play the card game, AND implement one real fix (this grew from a propose-only exercise to a build-and-prove one — see Lab 1 slide). Ask: "Who has heard the word 'threat model' before?" gauge the room. -->

---

## How this course works

- Every week: **lecture concept → hands-on game/lab**
- You'll *break* sandbox targets **and** *defend* your own code
- Per-student flags · live scoreboard · weekly "Audit the AI"
- Ethics first: attack only provided targets (see `ETHICS.md`)

<!-- Set expectations + ethics (legally important). Emphasize: every flag is unique to you; copying is traceable; you may be asked to explain your work live. Say plainly: "Attacking systems you don't own is a crime — everything here is in a sandbox you're authorized to attack." Have them read/sign the ethics acknowledgment this week. ~2 min. -->

---

## What does "secure" mean?

- **Confidentiality** — only the right people can read data
- **Integrity** — data/code can't be tampered with undetected
- **Availability** — the system is there when needed

> Security is not a feature you add — it's a property you design for.

<!-- Core model. Give one concrete example each: C — your medical records; I — your bank balance not silently changed; A — the hospital system up during an emergency. Ask the class to classify a breach you name (e.g., "ransomware encrypts files" → hits A and often C). Stress the tagline; it recurs all term. ~6 min. -->

---

## Attacker vs. defender mindset

- Defenders must close **every** hole
- Attackers need **one**
- Think in **abuse cases**, not just use cases
- "What can go wrong here?" at every boundary

<!-- The asymmetry is the whole reason security is hard. Contrast a "use case" (user logs in) with an "abuse case" (attacker logs in as someone else) — say "abuse case," not "misuse case," to match the worksheet's term (Task 4: 2 personas × 2 abuse cases, graded). Exercise: pick the classroom projector login and ask "how would you abuse this?" Get 3 answers. ~5 min. -->

---

## Trust boundaries & attack surface

- **Trust boundary:** where data crosses between components of different privilege
- **Attack surface:** every input an attacker can reach
  - HTTP params, headers, cookies, file uploads, APIs, env vars, dependencies

<!-- Define both precisely — these terms drive the whole DFD/STRIDE method. Draw on the board: browser | (boundary) | server | (boundary) | database. Anything crossing a boundary is where you scrutinize. Ask the class to list inputs of a login page → that's its attack surface. ~6 min. -->

---

## Worked example: the `/upload` endpoint

```text
Browser  --(file)-->  [Flask app]  --save f.filename-->  uploads/
                            |                               ^
                       /files/<name>  --------serves back---
```

- Crosses the **Internet → app** trust boundary
- Inputs: the file **bytes** *and* the **filename** (attacker-controlled)
- `../../escaped.txt` as a filename → the app saves it there — **arbitrary-file-write**, unauthenticated, anywhere the process can reach (not "overwrite a same-name file" — write to a path you chose)
- `/files/<name>` (the *read* path) is comparatively well-defended — Werkzeug's `safe_join` blocks the same trick

<!-- This is the "make it concrete" moment — walk the data flow on the board. Ask: "what does the app trust here?" (it trusts the filename, unsanitized, on save). Verified live: /upload writes outside uploads/ with no auth; /files/<name> refuses every traversal encoding tried. Get the direction right — it's a WRITE bug, not a read bug — the rest of today's STRIDE pass depends on this. ~7 min. -->

---

## STRIDE

| Letter | Threat | Property violated |
|---|---|---|
| **S** | Spoofing | Authentication |
| **T** | Tampering | Integrity |
| **R** | Repudiation | Non-repudiation |
| **I** | Information disclosure | Confidentiality |
| **D** | Denial of service | Availability |
| **E** | Elevation of privilege | Authorization |

<!-- STRIDE is a checklist so you don't forget a category. Go letter by letter, 1 example each, ideally tied to /upload: T = swap a file; I = read another user's upload; D = upload a 10 GB file; E = upload a .php and execute it. Tell them: apply STRIDE to every element of the DFD. ~8 min. -->

---

## STRIDE applied to `/upload`

- **S** — no auth: anyone can upload as "anyone"
- **T** — `../` filename **writes** outside `uploads/` — arbitrary-file-write, not just an overwrite
- **R** — no logs → can't prove who uploaded the malware
- **I** — the *read* path (`/files/<name>`) is comparatively well-defended (Werkzeug blocks traversal there) — this element's real risk is on the write side, not this letter
- **D** — no size limit → fill the disk
- **E** — upload `shell.php`, then request it → code execution

<!-- Pay-off slide: the full STRIDE pass on one element. Let the class call out threats before revealing each line. Verified by running the real sample-app: the traversal bug is a WRITE primitive (Tampering), and the naive "I = read outside the folder" claim does NOT reproduce against /files/<name> — Werkzeug's safe_join blocks it. Don't let this STRIDE pass repeat that error. End with: "5-6 threats from ONE endpoint — now imagine the whole app." ~6 min. -->

---

## The landscape you'll use all term

- **OWASP Top 10 (2025)** — most critical web risks
- **OWASP LLM Top 10 (2025)** — AI app risks
- **MITRE CWE** — catalogue of weaknesses (this week's finding maps to **CWE-501**, Trust Boundary Violation)
- **MITRE ATT&CK** — adversary tactics & techniques

<!-- Orient them to the references we'll cite weekly. OWASP = what to prevent; CWE = the precise weakness id; ATT&CK = how real adversaries operate. Name CWE-501 explicitly here — the worksheet's Reflection Q1 asks them to map their /upload finding to a CWE, and this is the answer the course has already committed to (fixed 2026-07-25, after CWE-1059 turned out to be MITRE-prohibited for vulnerability mapping). They'll map every finding to a CWE/OWASP id all term. ~3 min. -->

---

## Secure by Design

- **CISA "Secure by Design":** safety is the vendor's job, on by default
- Shift from "patch later" to **design out the bug class**
- Industry & government push toward **memory-safe languages** (more in Wk 11)
- Some bugs are **design flaws**, not coding slips → **A06: Insecure Design**
- Today's lab makes you *do* this: after you fix `/upload`, you'll argue whether your fix closes the **class** of bug or just this one **instance**

<!-- Tie the mindset to the current policy moment (CISA, memory-safety roadmaps). Key idea: threat modeling catches design flaws *before* code exists — cheapest place to fix. This slide's own thesis is Task 8's actual grading question — make the connection explicit, don't leave it implicit. Contrast cost of fixing at design vs in production (orders of magnitude). ~4 min. -->

---

## 🎲 Game — Elevation of Privilege

- Microsoft's free **STRIDE card deck**
- Play cards against the sample app's data-flow diagram
- Each valid threat tied to a real element = a point
- Outcome: a team-built STRIDE model

<!-- Explain the game before the lab: it gamifies the STRIDE pass we just did. Each suit = a STRIDE category; you play a card by naming a concrete threat on the DFD. Make it competitive (leaderboard). It lowers the barrier for students who freeze on a blank page. ~3 min. -->

---

## Lab 0 — Environment setup (once)

1. **Docker Desktop** (Win/macOS/Linux) — runs every lab target
2. Browser + proxy: Burp Suite Community **or** OWASP ZAP
3. **Toolbox container** (for W11 + recon): `docker build -t softsec-toolbox labs/toolbox`
4. *Optional fallback:* a Kali/Ubuntu VM if your host can't run Docker
5. Verify: `docker run hello-world`, `git --version`

<!-- Logistics — get everyone's environment working today; setup pain derails later weeks. Have TAs circulate. Tell them to fork the course repo now. This is graded only on "it runs." ~ start of lab. -->

---

## Lab 1 — Threat-model a sample app

> 📋 **Worksheet 1** — `labs/week01-threat-modeling/worksheet.md` (Part 3) · **kickoff:** `docker compose up` → http://localhost:8080

1. Run the app; draw a **DFD**; apply **STRIDE** to each element
2. Abuse cases: 2 personas × 2 abuse cases
3. Deep-dive the `/upload` path-traversal finding
4. **Systems-level pass:** assume one element is owned — what does it reach? Chain two low findings into one system-level claim
5. Turn threats into testable **security requirements** ("the system must … so that …")
6. **NoteVault (term project):** DFD + top-3 threats — this kicks off your project
7. Rank top 5 risks (likelihood × impact)
8. **Defend: implement one real mitigation** — diff, before/after evidence, and argue whether your fix closes the bug **class** or just this **instance**

<!-- This grew from a 4-step propose-only exercise into an 8-part build-and-prove lab (task numbering in the worksheet is 0-8, with a 3b for the systems-level pass) — don't teach the old 4-step version. Two things are new and graded, cite them explicitly: the systems-level pass (step 4, research-grounded — STRIDE-only modeling makes people miss system-level threats) and the implemented-and-evidenced defense (step 8 — this is where "Secure by Design" 4 slides ago stops being theory). Point them to THREAT-MODEL-TEMPLATE.md. Step 6 kicks off the term project. -->

---

## Using AI in this course

- AI is allowed — and you must **disclose** how you used it
- But AI **hallucinates** APIs/CVEs and writes **insecure code**
- You're graded on understanding, not the answer:
  - random **live re-demos** — explain it or score zero
  - your **flags are unique** to you — copying is traceable
  - every lab has an **"Audit the AI"** task: find what its answer gets wrong
- Use AI to **learn faster** — never to **skip the thinking**

<!-- Address AI head-on, week 1. Frame it as a professional skill: future engineers use AI but must verify it. The Audit-the-AI task turns its weakness into the lesson. Be explicit about the integrity controls so expectations are set early. ~4 min. -->

---

## Key takeaways

- Design for security; don't bolt it on
- Attackers need one gap — model the whole surface
- STRIDE + DFD = a repeatable way to find design flaws

<!-- Recap in 3 lines. Cold-call 2 students: "give me one STRIDE threat for a login page." Confirm they can do the lab. ~2 min. -->

---

# Questions?
Next week: Secure SDLC, tooling & fuzzing

<!-- Cliffhanger: "Next week we automate finding these bugs — and race to triage them. Get your VM working before then." Take questions; remind about the ethics acknowledgment + Lab 0. -->
