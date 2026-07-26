# Lesson Plan — Week 9: Midterm — Hands-on CTF Practical

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 9 · ⬚ |
| **Contact time** | 150 min — a single practical-exam block. No lecture, no lab (`AGENDA.md`, *Week 9 — Midterm CTF practical (150 min)*) |
| **Lab folder** | `labs/week09-midterm-practical` — holds `README.md` and `ctf.md` (the student paper); it ships no target of its own |
| **Slides** | `slides/week09.md` — proctor deck, not a teaching deck |
| **Covers** | Weeks 1–6 (`labs/week09-midterm-practical/README.md`). The seven challenges themselves draw on Weeks 3–6; threat modelling and CWE/OWASP mapping (W1–W2 material) are examined in the Week 8 written paper |
| **Targets** | `labs/week03-cryptography` · `labs/week04-injection` · `labs/week05-xss-client-side` · `labs/week06-authn-authz` (`ctf.md`, *Targets*) |
| **Standards** | The ids the source weeks' READMEs attach: **A04** Cryptographic Failures · CWE-327, CWE-916, CWE-330 (W3) · **A05** Injection · CWE-89, CWE-78 (W4) · **A05** Injection · CWE-79, CWE-352 (W5) · **A01** Broken Access Control, **A07** Authentication Failures · CWE-639, CWE-287 (W6) |
| **CLOs addressed** | **CLO2** exploit · **CLO3** remediate · **CLO6** evidence & ethics (course specification §6, row 9) |

---

## 1. Session objectives

This is an assessment, not a teaching session. What the sitting is designed to evidence:

**Knowledge (K)**
- K1 — For each challenge solved, state in one line the control that would have prevented it (`ctf.md` requires a **mitigation** column per challenge).
- K2 — Recognise which vulnerability class a target's behaviour belongs to *without* task scaffolding: unlike the weekly worksheets, `ctf.md` states only the goal of each challenge.

**Skills (P)**
- P1 — Log in as `admin` without the password, and read a file via the `host` parameter, on the injection target (challenges 1–2, W4).
- P2 — Fire `alert(document.domain)` stored for another user (challenge 3, W5).
- P3 — Read another user's order object, and become admin with a forged JWT (challenges 4–5, W6).
- P4 — Recover a password from a weak hash, and recover the plaintext structure from the ECB oracle (challenges 6–7, W3).
- P5 — Record, per challenge, the **flag/proof**, the **payload or command**, and a **one-line mitigation** — the three columns of `ctf.md`'s submission table.

**Attitude (A)**
- A1 — Attack only the supplied sandbox targets, under [ETHICS.md](../../ETHICS.md) (`ctf.md`, *Rules*).
- A2 — Work individually — no collaboration (`ctf.md`, *Rules*).
- A3 — Submit evidence that is identifiably their own and that they can reproduce on request ([SUBMISSION.md](../../SUBMISSION.md), *Academic Integrity*).

## 2. What is assessed

Seven challenges, 100 points, 150 minutes, individual (`ctf.md`). They are **not** independently
hosted: only four targets carry the seven challenges (`ctf.md`, *Targets*) — `week04-injection`
carries challenges 1–2 (30 pts), `week06-authn-authz` carries 4–5 (30 pts), and
`week03-cryptography` carries 6–7 (25 pts); only `week05-xss-client-side` (challenge 3, 15 pts) is
single-challenge. A target that will not start therefore costs a student every challenge it hosts,
not one.

| # | Title (as printed in `ctf.md`) | Topic | Source week | Pts |
|---|---|---|---|---:|
| 1 | **Boolean Bypass** — log in as `admin` without the password | SQLi | W4 | 15 |
| 2 | **Shell Out** — read a file via the `host` parameter | Command injection | W4 | 15 |
| 3 | **Pop the Alert** — fire `alert(document.domain)` stored for another user | Stored XSS | W5 | 15 |
| 4 | **Not Your Order** — read another user's order object | IDOR | W6 | 15 |
| 5 | **Forge Ahead** — become admin with a forged JWT | Broken JWT | W6 | 15 |
| 6 | **Crack It** — recover a password from a weak hash | Crypto | W3 | 15 |
| 7 | **Penguin** — recover the plaintext structure from the ECB oracle | Crypto | W3 | 10 |

The READMEs attach OWASP/CWE ids at **week** level (header table above), not per challenge;
challenge-level attribution is left to the marking key.

**CLO coverage.** Challenges 1–7 evidence **CLO2**. The per-challenge mitigation line is the
**CLO3** evidence available in a 150-minute practical — there is no defend-and-re-test task here, as
there is in a teaching week. Per-student flags and identity-stamped evidence carry **CLO6**.

## 3. Preparation and infrastructure readiness

### 3.1 What this sitting actually runs on

- **Student machines, local Docker.** The course delivery model is "all lab targets run locally in
  Docker" on the student's own machine, no cloud account for the core labs (course specification
  §1, §10). The exploitation itself therefore does not depend on the campus network.
- **Who starts the targets.** `ctf.md` says "Targets (**started by the instructor**)". Decide which
  of the two planting models in `instructor/anti-cheating.md` §A you are running **before** the day,
  because the two are not interchangeable:
  1. *Local build (the playbook's recommendation)* — each student runs `docker compose up` in their
     own copy, and compose reads **their** `.env`, so the flag is derived from their student ID.
  2. *Instructor-seeded* — you host the targets and insert each student's flag row/secret before
     their session. A single shared instance started by the instructor issues **one** flag per
     challenge to everyone, and per-student attribution is lost unless model 2 is actually done.
- **CTFd is the scoreboard, not the grade.** `instructor/CTFd-SETUP.md` is explicit: CTFd flags in
  `ctfd/challenges.yml` are shared/static and CTFd is the engagement layer; graded integrity uses
  the per-student flags from `seed_flags.py`. If the board is up, **freeze it** for the exam window
  (CTFd → Settings → Freeze time, `CTFd-SETUP.md` §4).
- **The spawnable platform is not in play.** `instructor/platform-build/` (CTFd skin + per-student
  spawnable challenges) is verified on local Docker only; its `deploy/` is recorded as "scripts
  valid; **not yet run on real hosts**", and `instructor/PLATFORM-ROADMAP.md` defers go-live. Do not
  plan this sitting around it.
- **Submission of record.** Flags + payload + mitigation via the CTF Form / Classroom
  ([SUBMISSION.md](../../SUBMISSION.md), *Exams*). `ctf.md`'s own submission table is the paper form
  of the same three columns.

### 3.2 Per-student flag seeding

```bash
export FLAG_SALT='<this cohort's salt — never published>'   # instructor/anti-cheating.md §A
python3 instructor/seed_flags.py gen students.txt -o flags.csv     # authoritative table
python3 instructor/seed_flags.py env <STUDENT_ID> > .env           # in the lab folder that uses it
python3 instructor/seed_flags.py verify 'FLAG{...}' students.txt   # who was this issued to?
```

Two dependencies that fail *before* anything is generated: `instructor/seed_flags.py` is a shim that
forwards `FLAG_SALT` to `SWSEC_FLAG_SALT` and requires the sibling `KOSEN69 - curriculum` monorepo —
without it, it exits with `ERROR: curriculum monorepo not found at …`.

**Which challenges are actually env-seeded** (verified against the files, not assumed):

| Target | Compose passes | App reads it |
|---|---|---|
| `labs/week04-injection` | `FLAG_SQLI`, `FLAG_CMDI` | `vulnerable_app.py:10–11`, via `os.environ.get(...)` with an in-file fallback |
| `labs/week06-authn-authz` | `FLAG_IDOR`, `FLAG_JWT` | `vulnerable_app.py:11–12`, same pattern |
| `labs/week05-xss-client-side` | *no `environment:` block* | no `FLAG`/`os.environ` reference in `vulnerable_app.py` |
| `labs/week03-cryptography` | *no `environment:` block* | no `FLAG`/`os.environ` reference in `vulnerable_crypto.py` |

`seed_flags.py env` does issue `FLAG_XSS`, `FLAG_CRACK` and `FLAG_ECB`, but nothing in the W3/W5 labs
consumes them as they currently stand. **Challenges 3, 6 and 7 are therefore not per-student by
construction** — plant them by the procedure in the marking key, or plan their attribution around
identity-stamped evidence and the viva (§6).

**Pre-flight, in each of the two seeded folders:** `docker compose config` must show a *value* for
each `FLAG_*`. With no `.env` present it renders them as `FLAG_SQLI: null` (checked), the variable
never reaches the container, and the app serves the placeholder committed in `vulnerable_app.py` —
the `…_demo` values. A `_demo` flag arriving on a submission sheet means **seeding failed**, not
that the student cheated.

### 3.3 Room, network, machines

- Room / seating / invigilator count: ⬚ (not recorded in this repository).
- Students work on their own machines; "phones away; one device" (`instructor/anti-cheating.md` §C).
- Network is needed for image and `pip` fetches at target start-up and for the submission Form — not
  for solving. Get the targets **up before the clock starts** (§4).
- The deck's own instruction: "Confirm everyone's VM/Docker works in the first 5 min"
  (`slides/week09.md`, speaker note).

### 3.4 Test the day before

- [ ] **Planting model chosen and recorded** (§3.1). Model 1: every student has their own `.env` in
      their own copy before the day. Model 2: per-student rows/secrets seeded into the instance you
      host. Tick every box below and still arrive with one shared instance and no seeding, and the
      per-student flags are decorative.
- [ ] `docker pull python:3.12-slim` — the base image all four targets use.
- [ ] Bring each target up **once, one at a time**: the three web targets answer on
      `http://localhost:8080`; `labs/week03-cryptography` publishes no port and runs its compose
      command (`pycryptodome`, `argon2-cffi`, then `vulnerable_crypto.py`), with `hashes.txt` in the
      folder.
- [ ] `docker compose config` in `labs/week04-injection` and `labs/week06-authn-authz` shows real
      `FLAG_*` values, not `null` (§3.2).
- [ ] `python3 instructor/seed_flags.py verify '<one issued flag>' students.txt` resolves to the
      right student, **using the same salt** that `gen` ran with.
- [ ] Optional, if the CTFd catalog is in use: `python3 instructor/check_flag_keys.py` exits 0
      (flag-key vocabulary in sync — `instructor/platform-build/README.md`, *Guardrails*).
- [ ] CTFd scoreboard frozen for the window; submission Form open/close times set, with the Form
      settings from `instructor/anti-cheating.md` §C (restrict to the cohort's accounts, collect
      email, one response, auto-close).
- [ ] Tell students to arrive with a cracker for challenge 6 — `hashcat` or `john` plus the wordlist
      named in `labs/week03-cryptography/worksheet.md`'s prerequisites. **No course container ships
      one:** the crypto compose installs only `pycryptodome` and `argon2-cffi`, and `labs/toolbox`
      carries clang, gdb, `nmap` and `sqlmap` — not a password cracker.
- [ ] The Week 7 mock CTF has been run — `labs/week07-review-midterm-prep/mock-ctf.md` states
      "Format: same as the Week 9 midterm practical", ungraded, hints included. `README.md` tells
      students to warm up on it.

## 4. Run of show — the 150-minute block

Timings are `AGENDA.md`'s (*Week 9 — Midterm CTF practical*): `0:00–0:10 rules + target check ·
0:10–2:30 solve challenges · submit flags`.

| Time | Block | Instructor does | Students do |
|---|---|---|---|
| 0:00–0:10 | **Briefing + target check** | Run `slides/week09.md`: format (timed, sandbox, each solved challenge = a flag = points), the 150 minutes, that **flags are per-student and copying is traceable**, the four challenge areas, and the rules (sandbox targets only, no collaboration, submit flag + method + mitigation). Confirm Docker is working across the room | Stand the targets up; report anything that will not start **now**, not at 1:00 |
| 0:10–2:30 | **Competition window** | Invigilate; answer only environment questions, not challenge questions; watch for the `_demo` tell (§3.2) | Solve challenges 1–7 in any order; fill the three columns per challenge as they go |
| 2:30 | **Submission cutoff** | Close the Form / collect the paper tables; the deck's closing slide is "Submit your flags" | Submit flags + payload/command + one-line mitigation |

**Port note to give in the briefing.** The three web targets all publish host port **8080** — they
cannot run at the same time. Students must bring one down before bringing the next up, or override
the published port (§9).

The 150-minute block contains **no debrief slot** — see §7.

## 5. Scoring — how points become marks

| Step | Rule | Source |
|---|---|---|
| Per challenge | Flag/proof + payload/command + one-line mitigation = full points | Points: `ctf.md` (challenge table, 6 × 15 + 1 × 10 = 100); scoring rule: `instructor/exams/week09-midterm-practical-ctf-answers.md` (*Scoring*) |
| No flag | Partial credit for documented progress | `ctf.md`; `labs/week09-midterm-practical/README.md` |
| Paper total | 100 pts | `ctf.md` |
| Into the gradebook | **Midterm % = average** of the W8 written and the W9 CTF | `instructor/GRADEBOOK.md` |
| Into the final mark | Midterm block = **20%**, individual — so this sitting carries half of it | `syllabus.md` §6; course specification §4 |

**Individual vs team.** Week 9 is individual end to end (`ctf.md`: *Individual*, "no
collaboration"). There is **no** team component: the Houses / CTFd leaderboard is explicitly
non-graded engagement (`syllabus.md`, *Teams & Houses*; course specification §7), and the team CTF
is Week 19. Nothing on the scoreboard should be transcribed into the gradebook.

**Make-up sittings.** The instructor exam set holds a parallel **Form B for the written papers only**
(`instructor/exams/` — W8 and W18); there is no Form B for the practical. What the deck points at
for rotation is the CTF pool in `instructor/exams/item-bank.md` ("W9 — Midterm CTF extras", covers
W1–6). Absence / make-up / late policy for an exam sitting: ⬚ (institutional).

## 6. Academic-integrity controls actually used

| Control | How it is operated | What it catches |
|---|---|---|
| **Per-student flags** | `seed_flags.py gen` before the day; `verify '<flag>' students.txt` at marking | A flag submitted by one student but *issued* to another — a violation for **both** parties ([SUBMISSION.md](../../SUBMISSION.md)) |
| **Identity-stamped evidence** | Screenshots must carry the student's terminal `whoami` / login email / student ID **and** a timestamp | Borrowed or generic screenshots (`instructor/anti-cheating.md` §B) |
| **Method note per challenge** | The payload/command + mitigation columns of `ctf.md` | A flag held without the mechanism; also the basis for partial credit |
| **Viva / re-demo spot-check** | Pick 2–3 students to reproduce or explain their own submission | Work the student cannot account for (`anti-cheating.md` §D; course specification §7) |
| **Scoreboard freeze** | CTFd → Settings → Freeze time for the window | Progress leaking between students mid-sitting (`CTFd-SETUP.md` §4) |
| **Dynamic scoring + first blood** | Already configured per challenge on CTFd | Reduces the incentive to pool answers (`anti-cheating.md` §C) |
| **Rotation each cohort** | New `FLAG_SALT`, new data seeds, at least one target changed per topic | Last year's flag dump (`anti-cheating.md` §E) |

**Known limits, so they are covered deliberately rather than assumed away:**

- Challenges **3, 6 and 7** are not env-seeded per student (§3.2). Their attribution rests on
  identity-stamped evidence, the method note, and the viva — weight the spot-check towards them.
- A `…_demo` flag is a **seeding failure**, not cheating (§3.2). Check `docker compose config`
  before accusing anyone.
- `verify` only resolves flags generated with the **same salt**; a salt mismatch looks like an
  unattributable flag.
- Red flags to carry into marking (`anti-cheating.md` §F): identical screenshots across students,
  a flag `verify` attributes elsewhere, prose that does not match the student's own data seed.
- If copying is found: `ETHICS.md` + the conduct process; keep the `verify` output as evidence
  (`anti-cheating.md` §G).

## 7. After the sitting — debrief and how results feed the final mark

- **Debrief.** `AGENDA.md` allocates no debrief inside the 150 minutes. The only adjacent slot the
  timetable offers is the Week 10 lecture's opening block, `0:00–0:10 weekly quiz + recap`
  (`AGENDA.md`, standard teaching-week template); date ⬚. The deck's own close is: collect
  submissions, grade with the answer key + `seed_flags.py verify` for copied flags, preview Week 10
  (APIs) (`slides/week09.md`).
- **Marking.** Key: `instructor/exams/week09-midterm-practical-ctf-answers.md` (git-ignored — never
  copy any of it into this repository's public files).
- **Into the mark.** Enter the score under *Midterm*; the sheet recomputes **Midterm % = average**
  of W8 and W9 (`instructor/GRADEBOOK.md`), and the Classroom import maps
  `grade ÷ maxPoints × 100`. Midterm is 20% of the final mark (`syllabus.md` §6).
- **Into next time.** A challenge nobody solved, or everybody solved, is an item-bank note for the
  W19 pool (`instructor/exams/item-bank.md`).

## 8. Materials

- Paper + brief: `labs/week09-midterm-practical/ctf.md`, `labs/week09-midterm-practical/README.md`
- Proctor deck: `slides/week09.md`
- Targets: `labs/week03-cryptography/`, `labs/week04-injection/`, `labs/week05-xss-client-side/`,
  `labs/week06-authn-authz/` (`docker compose up` in each)
- Dry run students should have done: `labs/week07-review-midterm-prep/mock-ctf.md`
- Instructor-only (git-ignored): `instructor/seed_flags.py`, `instructor/anti-cheating.md`,
  `instructor/CTFd-SETUP.md`, `instructor/GRADEBOOK.md`,
  `instructor/exams/week09-midterm-practical-ctf-answers.md`, `instructor/exams/item-bank.md`
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement:
  [ETHICS.md](../../ETHICS.md)

## 9. Risks and contingencies

| Risk | Mitigation |
|---|---|
| **Port 8080 collision between targets.** `labs/week04-injection`, `labs/week05-xss-client-side` and `labs/week06-authn-authz` all publish `8080:5000`; the second `docker compose up` fails to bind | Brief it at 0:00–0:10: `docker compose down` one before starting the next, or override the **left** side of the ports mapping. The app listens on 5000 *inside* the container, so do not republish 5000 — macOS AirPlay squats 5000, not 8080 |
| **Missing `.env` → no per-student flag.** Compose renders `FLAG_SQLI: null` and the app falls back to the `…_demo` placeholder committed in `vulnerable_app.py` | `docker compose config` in `labs/week04-injection` and `labs/week06-authn-authz` the day before; treat any `_demo` flag on a sheet as a seeding failure |
| **`seed_flags.py` cannot find the curriculum monorepo** — the shim `sys.exit`s with `ERROR: curriculum monorepo not found` and generates nothing | Run `gen` the **day before**, not on the morning; the sibling `KOSEN69 - curriculum` directory must be present |
| **Salt mismatch** between `gen` and `verify` (flags are an HMAC of student ID + challenge keyed by the salt) — attribution silently returns nothing | Record the cohort's `FLAG_SALT` with the `flags.csv` it produced; export the same value before `verify` |
| **PyPI reachability at start-up.** Every target `pip install`s at container start (`flask`; `flask pyjwt`; `pycryptodome argon2-cffi`) — a whole room starting at once needs the network | Pre-pull `python:3.12-slim`; keep a USB `docker save`/`docker load` copy; use the 0:00–0:10 target check to surface failures before the clock matters |
| **Challenge 6 needs a host-side cracker.** No course container ships `hashcat`/`john`; `labs/toolbox` has clang, gdb, `nmap`, `sqlmap` only | Prerequisite announced with the Week 7 mock CTF; verify at the target check. A student without one can still earn documented-progress credit |
| **Burp on its default listener.** The Week 6 worksheet's optional Burp step points the browser proxy at `127.0.0.1:8080` — the same port the targets publish | Burp is optional for this sitting; move either Burp's listener or the target's published port |
| **CTFd unavailable, or never deployed for this cohort** | The board is engagement only; the submission of record is the CTF Form / Classroom ([SUBMISSION.md](../../SUBMISSION.md)), and `ctf.md`'s submission table works on paper |
| **A single instructor-hosted instance issues one shared flag per challenge** (`ctf.md` says targets are "started by the instructor") | Settle the planting model before the day (`anti-cheating.md` §A); if you host, seed per-student rows/secrets, otherwise attribution for challenges 1, 2, 4, 5 is lost too |
| **A student's Docker will not run at all** | No spare-machine provision is recorded in this repository — decide and record it: ⬚ |

**If it fails mid-session — decision order**

1. **Network drops.** Solving is local and the targets are already up; keep going. Hold submissions
   and collect `ctf.md`'s table on paper at 2:30, transcribe afterwards.
2. **One target dies for one student.** They lose every challenge that target hosts (§2) — up to 30
   pts (week04 or week06) or 25 pts (week03), 15 pts if it's week05 — not the whole paper. Note it
   against their sheet for partial credit.
3. **The Form / CTFd dies.** The paper table becomes the record; nothing else changes.
4. **Widespread failure to start targets inside the first 10 minutes.** That is exactly what the
   `0:00–0:10` target check exists to expose. The repository defines no fallback adjustment to the
   150-minute window — the decision and its justification are the instructor's, and must be
   recorded: ⬚.

## 10. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Challenge with the lowest solve rate, and what that says about the week it came from: ⬚
- Integrity flags raised by `seed_flags.py verify`, and how each resolved: ⬚
- Anything to change before this week runs again: ⬚
