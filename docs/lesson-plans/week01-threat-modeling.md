# Lesson Plan — Week 1: Security Mindset & Threat Modeling

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 1 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week01-threat-modeling` |
| **Slides** | `slides/week01.md` |
| **Standards** | OWASP 2025 **A06 Insecure Design** · CWE-501 (Trust Boundary Violation) |
| **CLOs addressed** | **CLO1** model · **CLO6** ethics & evidence (course specification §6, Week 1 row: "1, 6"). The worksheet's recurring *Audit the AI* and *EiPE + Prompt Problem* parts additionally carry **CLO5** per specification §4. |

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — Define the CIA triad and give one concrete failure example for each of the three properties.
- K2 — Explain what a *trust boundary* is, why data crossing one deserves extra scrutiny, and what "attack surface" means — naming two things that increase it in a web app.
- K3 — Map each STRIDE letter to its threat and to the security property it violates.
- K4 — State what "Secure by Design" (CISA) means and how it differs from bolting security on after release; locate a weakness in the OWASP Top 10, MITRE CWE and ATT&CK landscape.

**Skills (P)** — this week is *modelling only*; the worksheet's ethics note is explicit that students **analyse design, they do not attack the app**.
- P1 — Draw a data-flow diagram of the sample app: the external entity (web client), the process (Flask app), the data stores (`notes.db` SQLite and the `uploads/` store), the flows for `/notes`, `/upload` and `/files/<name>`, with the Internet→app trust boundary marked as a dashed line.
- P2 — Complete a per-element S/T/R/I/D/E grid grounded in the actual code of `sample-app/app.py`.
- P3 — Play the "Elevation of Privilege" deck against their own DFD and record every threat they can tie to a real element or flow.
- P4 — Write attacker personas and abuse cases, and convert threats into testable security requirements phrased as acceptance criteria ("the system must … so that …").
- P5 — Rank the top 5 threats by likelihood × impact, propose one concrete mitigation each, and sketch the secure design for the riskiest flow (`secure_filename`, store outside web root, allow-list extensions).

**Attitude (A)**
- A1 — Work within [ETHICS.md](../../ETHICS.md), which every student signs an acknowledgment of in Week 1; run the sample app only on their own VM/localhost.
- A2 — Submit evidence that is identifiably their own — every screenshot or diagram carries their `whoami` / login email / student ID and a timestamp — and be able to reproduce it live on request.
- A3 — Treat an AI-generated security answer as something to critique and verify, not to trust.

## 2. Key ideas (the through-line)

Security is not a feature you add — it is a property you design for. Defenders must close every
hole; an attacker needs one. The consequence is a method rather than a checklist of bugs: draw the
system as data flowing between components, mark every place data crosses from one privilege level
to another, and interrogate each of those crossings with a fixed vocabulary (STRIDE) so nothing is
forgotten. That is what makes this week's flaws *design* flaws — OWASP A06 Insecure Design,
CWE-501 Trust Boundary Violation — and design flaws are cheapest to fix before the code that
carries them exists. Everything the rest of the term exploits, this week names in advance.

## 3. Prior knowledge and preparation

- **Students, before class:** per the lab README, environment setup **is Lab 0** and is done
  *before class* — install Docker Desktop plus Burp Suite Community or OWASP ZAP (a Linux VM is an
  optional fallback), and verify with `docker run hello-world` and `git --version`. Also the
  one-time Week 1 setup in [SUBMISSION.md](../../SUBMISSION.md): create a GitHub account, **fork**
  the course repo, `git clone` the fork, join the Google Classroom.
- **⚠️ Unresolved conflict the instructor must settle before the day.** Three repo sources
  disagree about where Lab 0 sits. `labs/week01-threat-modeling/README.md` (the most recently
  updated) says "**Before class** — Set up your environment … This *is* **Lab 0**"; `AGENDA.md`'s
  per-week table footnote says "*W1 lab includes Lab 0 environment setup (~45 min) — onboarding
  block is longer"; `slides/week01.md` places Lab 0 "~ start of lab". Worksheet 1's Task 0 budgets
  5 minutes. Which reading is used on the day: ⬚ — and it changes the lab plan by ~40 minutes, so
  decide it before the session, not during it.
- **Instructor, before class:** pull `python:3.12-slim` ahead of the session (`docker compose build`
  or `docker compose up --build` once in the lab folder — `docker compose pull` is a no-op here
  since `docker-compose.yml`'s only service has a `build:` key and no `image:` key, verified);
  obtain the "Elevation of Privilege" deck in printed or virtual form (link in
  [readings.md](../../readings.md)); have the ETHICS.md acknowledgment ready to sign; confirm host
  port 8080 is free (see §8).
- **Lab prerequisites (worksheet Part 3):** "Docker + Docker Compose in your VM; a drawing tool
  (draw.io / paper + photo); the Elevation of Privilege deck (print or virtual)."
- **Prerequisite concept:** what an HTTP endpoint is, and enough Python to read a 43-line Flask file.

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | `quizzes/weekly/week01.md`; no prior teaching week to recap, so the slot carries course framing (break then defend, per-student flags, live scoreboard, weekly *Audit the AI*) and the Week 1 one-time business — see the note below the table | Individual quiz; course-framing slides ("How this course works") |
| 0:10–0:55 | Core concepts | What "secure" means — Confidentiality / Integrity / Availability, one concrete example each; attacker vs. defender asymmetry (defenders must close every hole, attackers need one) and misuse cases vs. use cases; trust boundary = where data crosses between components of different privilege; attack surface = every input an attacker can reach (HTTP params, headers, cookies, file uploads, APIs, env vars, dependencies) | Lecture, board diagram `browser \| (boundary) \| server \| (boundary) \| database`; class exercises from the deck's own notes: classify a named breach against C/I/A; "pick the classroom projector login — how would you abuse this?" (take 3 answers); list the inputs of a login page |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Vulnerability deep-dive + real cases | The worked example the whole method hangs on — the `/upload` endpoint: `Browser --(file)--> [Flask app] --save f.filename--> uploads/`, served back by `/files/<name>`; it crosses the Internet→app boundary and the app trusts *both* the file bytes and the attacker-controlled filename. Then the STRIDE table (letter → threat → property violated) and the full STRIDE pass on that one element: S no auth, T overwrite another user's file, R no logs, I `../` filename, D no size limit, E upload and then request an executable file. Close with the landscape they will cite all term: OWASP Top 10 (2025), OWASP LLM Top 10 (2025), MITRE CWE, MITRE ATT&CK. **Real-world design-flaw breach used as the case: ⬚** — the repo names none; Worksheet 1 Part 4 Q2 requires each student to bring one, so pick a case you are willing to be held to. | Lecture + board walk-through; let the class call out each STRIDE line before revealing it ("6 threats from ONE endpoint — now imagine the whole app") |
| 1:35–1:55 | Defences / secure coding | Secure by Design (CISA): safety is the vendor's job, on by default; shift from "patch later" to designing out the bug class; the industry and government push toward memory-safe languages (revisited in Week 11); why some bugs are design flaws rather than coding slips → **A06 Insecure Design**; the cost gap between fixing at design time and fixing in production. Then the course's AI policy slide (AI is allowed and must be disclosed; it hallucinates APIs/CVEs and writes insecure code; you are graded on understanding — live re-demos, per-student flags, weekly *Audit the AI*) and the three key takeaways. | Lecture with design-time vs production cost contrast |
| 1:55–2:00 | Brief the game | "Elevation of Privilege" — Microsoft's free STRIDE card deck, played against the sample app's DFD; each valid threat tied to a real element or flow scores a point; outcome is a team-built STRIDE model | Instruction |

> **Note — the Week 1 quiz slot.** AGENDA.md mandates a ~10-minute retrieval quiz at the start of
> every teaching week (6 questions: 5 MCQ + 1 short answer, individual, lowest 1–2 dropped across
> the term), and `quizzes/weekly/week01.md` exists. But Week 1 has no prior teaching week to
> retrieve from, and `quizzes/README.md` states that a weekly quiz covers "that week's lecture
> material" — which, at 0:00, has not been taught yet. **How the Week 1 quiz is run is ⬚**: no
> public repo source states a Week-1 convention (diagnostic pre-test, moved to the end of the
> lecture, or otherwise). What the slot does carry unambiguously is the Week 1 one-time business:
> the ETHICS.md acknowledgment — "Every student signs an acknowledgment of this policy in Week 1" —
> and SUBMISSION.md's one-time setup (fork the course repo, clone the fork, join the Google
> Classroom).

**Checks for understanding during lecture**
- During the core-concept block: have the class list the inputs of a login page, then name that list as its attack surface.
- On the STRIDE-applied slide: let students call out threats for `/upload` before each line is revealed — a silent room here means the DFD task will stall.
- At the takeaways: cold-call two students for *"give me one STRIDE threat for a login page."*

## 5. Laboratory — 180 min

Target: `docker compose up --build` in `labs/week01-threat-modeling` → `http://localhost:8080`
(worksheet Part 3, verbatim):

```bash
cd labs/week01-threat-modeling
docker compose up --build           # starts sample-app on http://localhost:8080
curl -s -X POST localhost:8080/notes -H 'Content-Type: application/json' \
     -d '{"owner":"alice","body":"hello"}'   # observe behavior, do not attack
curl -s localhost:8080/notes
```

Source to model: `sample-app/app.py`. Template to fill: `THREAT-MODEL-TEMPLATE.md` — copy it, do
not edit the original. What to submit per task: the threat/element identified + a screenshot (DFD,
table, or running app) + a 2–3 sentence mitigation.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:05 | **Task 0 — Onboarding (5 min)** | `docker compose up`, hit `/notes` and `/files/<name>`, read `sample-app/app.py` | Screenshot of the running app + the JSON response |
| 0:05–0:30 | **Task 1 — Draw the DFD (25 min)** | Identify the external entity (web client), the process (Flask app), the data store (`notes.db` SQLite), the `uploads/` store, and the flows for `/notes`, `/upload`, `/files/<name>`; mark the Internet→app trust boundary with a dashed line | DFD image embedded in their copy of the template |
| 0:30–1:00 | **Task 2 — STRIDE the elements (30 min)** | Fill the S/T/R/I/D/E grid per element, grounded in real code: `/notes` accepts a client-supplied `owner` with no auth (Spoofing); `/upload` saves raw `f.filename` and `/files/<name>` serves it back (Tampering + path-traversal Info disclosure); no logging anywhere (Repudiation) | Completed STRIDE table |
| 1:00–1:20 | **Task 3 — Elevation of Privilege game (20 min)** | Play the EoP deck against their DFD; each card tied to a real element or flow scores a point; record every valid threat | List of carded threats + score |
| 1:20–1:40 | **Task 5 — Abuse cases & attacker personas (20 min)** | Define 2 personas (e.g. a curious logged-in user; an anonymous internet attacker) and write 2 abuse cases each, tied to DFD elements | 4 abuse cases |
| 1:40–2:05 | **Task 6 — Path-traversal deep-dive (25 min)** | Trace `/upload` → `/files/<name>`; explain how `../` in a filename escapes `uploads/`; sketch the secure design (`secure_filename`, store outside web root, allow-list extensions) | The data flow + secure-design note |
| 2:05–2:35 | **Task 7 — Threat-model the project target (30 min)** | Run **NoteVault** (`cd ../../project/starter-app && docker compose up`), draw a quick DFD, list the top 3 STRIDE threats they would investigate | NoteVault DFD + top-3 threats (reused in the [project report](../../project/REPORT-TEMPLATE.md)) |
| 2:35–2:50 | **Task 8 — Security requirements (15 min)** | Write 3 security requirements as acceptance criteria ("the system must … so that …"), each mapped to a threat from Task 2 or 7 | 3 testable security requirements |
| 2:50–3:00 | **Task 4 — Defend / fix it: rank & mitigate (10 min)** | Rank the top 5 threats by likelihood × impact; propose one concrete mitigation each (e.g. auth on `/notes`, `secure_filename()` + allowlist for `/upload`, request logging for Repudiation, size/rate limits for DoS) | Top-5 table with mitigations in their template copy |
| ⬚ | **AI-resilient tasks** | *Audit the AI*, *Explain in Plain English*, *Prompt Problem* | Written answers (AGENDA.md: "start in class, finish as homework") |
| ⬚ | **Micro-demo + submit** | 2–3 rotating students give a 2–3 min walkthrough of their DFD/STRIDE model; everyone submits | Worksheet PDF → Classroom; work pushed → GitHub |

> **Timing note — this week is over-subscribed, and the plan does not hide it.** Worksheet 1's own
> task budgets total exactly 180 minutes (5 + 25 + 30 + 20 + 20 + 25 + 30 + 15 + 10), so the clock
> above reaches 3:00 at the end of Task 4 with nothing left for the closing blocks that
> `AGENDA.md`'s standard template seats at 2:25–2:45 (AI-resilient tasks), 2:45–2:55 (rotating
> micro-demo) and 2:55–3:00 (submit worksheet) — three separate rows in AGENDA.md, merged above into
> two rows ("AI-resilient tasks" and "Micro-demo + submit") for space. AGENDA.md acknowledges
> worksheet/template timing drift in general, but its own closing "⚠️ Note (drift to resolve)" names
> only Weeks 4–6 and 10–12 as *under*-budget (145–150 min of tasks, needing more content to fill the
> 180-min block) — the opposite of Week 1's over-subscription, so that note should not be read as
> already covering this week's case. The one lever the repo actually gives is that the AI-resilient
> tasks "start in class, finish as homework"; the micro-demo has no such lever. **Which task yields
> the time is ⬚** — no repo source states it, and shortening a task below its published budget would
> put the plan out of step with the worksheet the students are holding. Note also that the
> worksheet's own ordering runs 0, 1, 2, 3, 5, 6, 7, 8, 4 — Task 4 (Defend / fix it) genuinely comes
> last in the file, and the table preserves that.

**Formative checkpoints.** Task 0's `/files/<name>` returns **404 until something has been
uploaded** (verified) — a student reporting "the app is broken" here has simply not uploaded a file
yet, and this is a good 30-second teaching moment about the `/upload` → `/files/<name>` pairing they
will model in Task 6. A student still without a DFD at 0:30 should be given the four elements
verbally and made to draw only the flows and the boundary. Before Task 7, the whole room must run
`docker compose down` in the lab folder (§8) or Task 7 will fail to start.

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 1, Parts 1–4 | DFD, STRIDE table, EoP findings, abuse cases, security requirements, top-5 ranking + mitigations, reflection, screenshots | K1–K4, P1–P5, A2 | Part of the 30% worksheet component |
| Weekly quiz (start of lecture) | `quizzes/weekly/week01.md` score | K2–K4 — the item set does **not** examine K1 (CIA), which is evidenced only by Worksheet 1 Part 2 Q1 | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation of their own model | P1–P5, A2 | Pass/flag for follow-up |
| Personalised flag | The worksheet's Evidence & Integrity section reads "Personalized flag **(if this lab issues one)**" | A2 | ⬚ — whether Week 1 issues a flag is not stated in the lab |
| ETHICS.md acknowledgment | Signed acknowledgment (Week 1, per ETHICS.md) | A1 | Compliance gate, not a mark |

The worksheet's own 100-point rubric governs: *Lecture questions (Part 2)* 20 · *Exploitation +
evidence (DFD + STRIDE table + EoP findings + screenshots)* 40 · *Defense (top-5 ranking +
mitigations)* 25 · *Reflection (CWE/OWASP mapping + breach + best mitigation)* 15. Task 7's output
feeds the term project, whose threat model is due in Week 7.

## 7. Materials

- Lab: `labs/week01-threat-modeling/` — `README.md`, `worksheet.md`, `THREAT-MODEL-TEMPLATE.md`, `docker-compose.yml`, `sample-app/app.py`
- Slides: `slides/week01.md`
- Weekly quiz: `quizzes/weekly/week01.md`
- Signature game: Microsoft *Elevation of Privilege* (STRIDE card deck) — https://www.microsoft.com/en-us/download/details.aspx?id=20303
- Reading: OWASP Threat Modeling Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
- Project target for Task 7: `project/starter-app/` (NoteVault) · [project/README.md](../../project/README.md)
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Port 8080 is double-booked by the course's own files.** `labs/week01-threat-modeling/docker-compose.yml` publishes `8080:5000` and `project/starter-app/docker-compose.yml` publishes `8080:8080`. Task 7 tells students to start NoteVault while the Week 1 app is still up, which fails with `Bind for 0.0.0.0:8080 failed: port is already allocated` (reproduced). | Announce before Task 7: `docker compose down` in `labs/week01-threat-modeling` first. A student who wants both up at once must override the published port in one of the two compose files. The same error appears if anything else on the host already holds 8080 — check with `docker ps` before class. |
| **NoteVault is a heavy pull at Task 7.** `project/starter-app/Dockerfile` is `FROM python:3.12` — the full image, not `-slim` — so the whole room downloading it 2 hours into the lab is a stall. | Have students build NoteVault once during the break, or pre-pull `python:3.12` on the lab machines alongside `python:3.12-slim`. |
| **Task 7's command omits `TEAM_ID`.** `project/README.md` specifies `export TEAM_ID=<your-team-name>` before the first build; the worksheet's Task 7 command does not, so the marker seeds as `unassigned` (the compose default). | Expected in Week 1 — teams are not chosen until Week 4 per the project timeline. Tell students the `unassigned` marker is fine now and must be set before the Week 7 threat-model submission. |
| **Docker Desktop is not installed on the day**, because the Lab 0 placement is contradictory across README / AGENDA / slides (§3). | Settle the Lab 0 question before the session. If setup runs in class, the lab table above does not fit — budget it against the worksheet's tasks explicitly rather than silently overrunning. The optional Kali/Ubuntu VM is the documented fallback for hosts that cannot run Docker at all; `labs/toolbox` (itself a Docker image — it needs Docker to build) is a documented fallback only for hosts that can run Docker but lack native clang/libFuzzer/gdb tooling (course-specification.md §10). |
| **The Elevation of Privilege deck is not in the room.** Task 3 has a hard 20-minute slot and the deck is a physical/printed dependency fetched from a Microsoft Download Center page — printing, or classroom network, can fail. | Print the deck the week before; keep a virtual copy per House. Without a deck, Task 3 degrades to a timed STRIDE-category round-robin against the DFD, but say so openly rather than pretending the game ran. |
| **Task 0 looks broken:** `/files/<name>` returns 404 until a file has been uploaded (verified). | Answer once to the whole room; use it to introduce the `/upload` → `/files/<name>` pairing that Task 6 analyses. |
| **A student "tests" the traversal instead of modelling it.** The worksheet's ethics note for this week is *modelling only*. For accuracy if it is demonstrated on the projector: the **write** side is real — an upload sent with `filename=../evil.txt` lands at `/app/evil.txt`, outside `uploads/` (reproduced against the lab image, Flask 3.1.3 / Werkzeug 3.1.8) — but a **read**-side traversal through `/files/<name>` is not reachable (404, including URL-encoded), because Flask's `<name>` converter does not match `/`. Do not promise students a working read-side traversal. | Keep any demonstration instructor-side on the projector; students model, they do not attack. Re-state ETHICS.md rule 1. |
| **A team finishes the DFD and STRIDE grid well before 1:00.** | Extension: STRIDE the `notes.db` data store and the flows *between* elements, not just the endpoints; or start Task 7's NoteVault DFD early (after `docker compose down`). |
| Copied DFDs / STRIDE tables between students | Evidence & Integrity requires `whoami` / login email / student ID and a timestamp in every screenshot and diagram; viva spot-check the pair. |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan), and how the 180-minute over-subscription was resolved: ⬚
- Where Lab 0 actually landed (before class / in class), and what it cost: ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Did the Elevation of Privilege round surface threats the students had missed in Task 2?: ⬚
- Anything to change before this week runs again: ⬚
