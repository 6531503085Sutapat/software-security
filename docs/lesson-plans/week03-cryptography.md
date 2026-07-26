# Lesson Plan — Week 3: Cryptography Used Correctly (and Misused)

| | |
|---|---|
| **Course** | Software Security (⬚ course code) |
| **Week / date** | 3 · ⬚ |
| **Contact time** | 300 min = 120 lecture + 180 laboratory |
| **Lab folder** | `labs/week03-cryptography` |
| **Slides** | `slides/week03.md` |
| **Standards** | OWASP 2025 **A04 Cryptographic Failures** · CWE-327 (broken/risky crypto algorithm — MD5, AES-ECB) · CWE-916 (weak password hashing — unsalted/fast) · CWE-330 (insufficiently random values — predictable token) · CWE-798 (hard-coded credentials — hardcoded key) |
| **CLOs addressed** | **CLO2** exploit · **CLO3** remediate · **CLO5** evaluate & communicate · **CLO6** evidence & ethics |

> The course-specification schedule row for Week 3 names **CLO2, CLO3**; CLO5 and CLO6 enter through the worksheet's *Audit the AI* and *Evidence & Integrity* sections, which every teaching week carries.

---

## 1. Session objectives

By the end of this week a student can:

**Knowledge (K)**
- K1 — Distinguish hashing, encryption and encoding, and name one job each is the wrong tool for.
- K2 — Explain why a fast hash (MD5/SHA-1) is unfit for password storage, and what a vetted KDF (bcrypt/argon2) provides instead.
- K3 — State what a salt defends against and why it must be unique per password; and why AES-ECB leaks structure while an authenticated mode (AES-GCM) adds integrity.

**Skills (P)**
- P1 — Recover passwords from unsalted MD5 hashes with a wordlist (`hashcat -m 0` or the `john --format=raw-md5` equivalent), and explain why unsalted MD5 falls so fast.
- P2 — Demonstrate the ECB structure leak: identical 16-byte plaintext blocks produce identical ciphertext blocks.
- P3 — Show that a 6-digit `random` reset token is brute-forceable, and identify the hardcoded key as a key-management flaw.
- P4 — Migrate password storage to argon2id with a rehash-on-login path, and perform an AES-GCM round-trip that fails the tag check on a tampered byte.
- P5 — Run the fixed skeleton and map each fix to the CWE it closes.

**Attitude (A)**
- A1 — Crack only the hashes provided in `hashes.txt`, on their own machine; wordlists and recovered values stay inside the lab (see the worksheet ethics note and [ETHICS.md](../../ETHICS.md)).
- A2 — Submit identity-stamped evidence that is their own work, and be able to reproduce it live on request.
- A3 — Treat AI-generated cryptographic code as something to be verified, not trusted.

## 2. Key ideas (the through-line)

Cryptography here rarely fails because the maths is broken — it fails because a sound primitive is used
for the wrong job or in the wrong mode. A fast hash stands in for a slow password KDF; a cipher mode
(ECB) preserves the very structure it was meant to hide; a key is pasted into source; a token comes
from a non-cryptographic RNG. The fix is never a cleverer tweak of the broken pattern — it is choosing
the vetted construction for the task (a KDF for passwords, an AEAD for data, a CSPRNG for tokens) and
keeping keys out of the code.

## 3. Prior knowledge and preparation

- **Students, before class:** Docker Desktop running (Week 1 Lab 0); skim the Week 2 recap. Install
  `hashcat` **or** `john` on the host and obtain the `rockyou.txt` wordlist — the lab image ships
  neither, and Tasks 1 and 6 need them.
- **Instructor, before class:** pull the lab image ahead of the session (`docker compose pull` in the
  lab folder) — a room of students pulling `python:3.12-slim` at once is the most common way to lose
  time; have the offline fallback ready (see §8). Confirm a working `hashcat`/`john` + `rockyou.txt` is
  available in the room, and that outbound TCP 443 to `example.com` works for Task 9 (or stage a saved
  cert).
- **Prerequisite concept:** what a hash is versus a cipher, and basic command-line use.

## 4. Lecture — 120 min

| Time | Block | Content | Method |
|---|---|---|---|
| 0:00–0:10 | Weekly quiz + recap | ~10-min retrieval quiz on Week 2 (secure SDLC, tooling & fuzzing); today's agenda | Individual quiz, lowest 1–2 dropped |
| 0:10–0:55 | Core concept | Hashing vs. encryption vs. encoding — what each is for and the job each is wrong for; why fast hashes fail for passwords and what a KDF (bcrypt/argon2id) adds; salts (why they are not secret, why unique per password); live-crack a single MD5 on the projector | Lecture + live coding on the projector |
| 0:55–1:05 | Break | | |
| 1:05–1:35 | Deep dive + real cases | The classic misuses: unsalted/fast MD5 (CWE-916/327), the AES-ECB structure leak (CWE-327), hardcoded keys (CWE-798), non-CSPRNG tokens (CWE-330); a short TLS-in-context aside; two brief real breaches (large password-database leaks on fast/unsalted hashes; hardcoded-credential disclosures in shipped software) | Lecture + short discussion: "what would have stopped this?" |
| 1:35–1:55 | Defences | argon2id with automatic per-password salting and a rehash-on-login migration path; AES-GCM authenticated encryption (random 12-byte nonce + auth tag); keys from env/secrets manager, never in source; the `secrets` CSPRNG for tokens; map each defence to the CWE it closes | Lecture with before/after code comparisons |
| 1:55–2:00 | Brief the game | "Capture the Hash" speedrun — crack the hashes fastest, then flip to the defender side and rebuild the service with a KDF + authenticated encryption | Instruction |

**Checks for understanding during lecture**
- After the core concept: cold-call *"is this hashing, encryption, or encoding — and what is it the wrong tool for?"*
- Before the break: one-minute paper — *"why is a salt not a secret, and why must it be unique per password?"*

## 5. Laboratory — 180 min

Target: `docker compose up` in `labs/week03-cryptography` installs `pycryptodome` + `argon2-cffi` on
`python:3.12-slim`, then runs `vulnerable_crypto.py` (the misuses) and `solution_skeleton.py` (the fix).
Locally: `pip install pycryptodome argon2-cffi` then `python vulnerable_crypto.py`. Targets:
`vulnerable_crypto.py`, `hashes.txt` (four unsalted MD5s), `solution_skeleton.py`. This week publishes
no web port — the target is a script, not a server.

| Time | Task | Student does | Evidence produced |
|---|---|---|---|
| 0:00–0:05 | **Task 0 — Onboarding (5 min)** | Run `python vulnerable_crypto.py`; note the md5 digest, the identical ECB ciphertext blocks, and the short token | Screenshot of the program output |
| 0:05–0:35 | **Task 1 — Capture the Hash (30 min)** | Strip the comment lines from `hashes.txt`, then run `hashcat -m 0 hashes.txt rockyou.txt` (or the `john --format=raw-md5` equivalent); recover all four plaintexts | Screenshot of cracked results (mask any real-looking value) + one line on why unsalted MD5 fell (CWE-916/327) |
| 0:35–0:55 | **Task 2 — ECB structure leak (20 min)** | Call `encrypt_ecb(b"A"*16 + b"A"*16)` from `vulnerable_crypto.py`; show the two 16-byte ciphertext blocks are identical | Hex output highlighting the repeated block + how it leaks structure (CWE-327) |
| 0:55–1:10 | **Task 3 — Predictable token (15 min)** | Call `reset_token()` repeatedly; argue why a 6-digit `random` token (10^6 space, non-CSPRNG) is brute-forceable | Sample tokens + a one-line attack estimate (CWE-330) |
| 1:10–1:15 | **Task 4 — Hardcoded key (5 min)** | Find `HARDCODED_KEY` in `vulnerable_crypto.py`; explain why shipping a key in source is a flaw | The line + a 2-sentence mitigation (CWE-798) |
| 1:15–1:40 | **Task 6 — Crack the project target's hashes (25 min)** | **NoteVault** stores unsalted MD5 hashes; obtain them (via the app's `/admin` once reachable, or from its `seed()` in `project/starter-app/app.py`) and crack them with `hashcat -m 0` | Recovered password(s) + the CWE; record for the [project report](../../project/REPORT-TEMPLATE.md) |
| 1:40–2:05 | **Task 7 — Password storage migration (25 min)** | Write `store_password`/`verify_password` with **argon2id**, plus a **rehash-on-login** path that upgrades a legacy MD5 record to argon2id at next login | The code + a short note on why migration matters |
| 2:05–2:25 | **Task 8 — Authenticated encryption round-trip (20 min)** | Encrypt+decrypt a message with **AES-GCM** using a random 12-byte nonce and a key from an env var; then flip one ciphertext byte and show decryption **fails** (tag check) | Round-trip output + the tampered-fails proof |
| 2:25–2:40 | **Task 9 — TLS in practice (15 min)** | Run `openssl s_client -connect example.com:443 </dev/null 2>/dev/null \| tee /tmp/tls.txt \| openssl x509 -noout -issuer -subject -dates`, then `grep -E 'Protocol\|New,' /tmp/tls.txt` for the negotiated version (the version line is printed by `s_client`, not `x509`, so the plain pipe would discard it) | Cert summary (issuer, validity, TLS version) + one line on what TLS protects that hashing/at-rest encryption does not |
| 2:40–3:00 | **Task 5 — Defend / fix it (20 min)** | Run `python solution_skeleton.py`; confirm `store_password`/`verify_password` use argon2id (auto-salted), `encrypt_gcm` uses a random 12-byte nonce + auth tag with a key from `ENC_KEY_HEX` env, and `reset_token` uses `secrets`; map each fix to the CWE it closes | Before/after table (misuse → fix → CWE closed) + screenshot of the fixed script running |
| carry-over | **AI-resilient tasks** | *Audit the AI* (critique an AI-written exploit/fix), *Explain-in-Plain-English*, *Prompt Problem* | Written answers (start in class only if ahead of budget; otherwise homework) |
| carry-over | **Micro-demo + submit** | 2–3 rotating students give a 2–3 min "show your exploit/fix"; everyone submits | Worksheet PDF → Classroom; fixed code → GitHub |

**Timing note — this block is over-subscribed.** Worksheet Part-3 tasks (0, 1, 2, 3, 4, 6, 7, 8, 9, 5)
sum to **180 min exactly**, so they fill the entire lab. The standard *AI-resilient* and
*micro-demo/submit* blocks therefore have no dedicated slot this week: run them in class only if the
room is ahead of budget; otherwise the AI-resilient tasks start in class and finish as homework (as
[AGENDA.md](../../AGENDA.md)'s standard lab template already specifies for this block), and the final minutes of Task 5's slot
double as the submit-and-wrap window. The rotating micro-demo can roll to the next week or be sampled
by viva if time runs out.

**Formative checkpoints.** The worksheet numbers its tasks in file order — 0, 1, 2, 3, 4, then **6, 7,
8, 9, and Task 5 (Defend) last**. Follow that sequence; the out-of-order numbering is intentional
(break, apply to the project, build the fixes, then run the skeleton). A student stuck on Task 1 after
15 minutes has almost always not stripped the comment lines from `hashes.txt` or is missing
`rockyou.txt` — check both before anything else. Tasks 7 and 8 are the load-bearing "build the fix"
tasks; a student behind at 2:05 should jump to Task 5 (run the skeleton) so they still land the defend
evidence, and return to 7/8 afterwards.

## 6. Assessment for this week

| Instrument | Evidence | Outcome | Weight |
|---|---|---|---|
| Worksheet 3, Parts 1–4 | Cracked hashes, ECB/token/key proof, argon2id + GCM code, before/after CWE mapping, written answers | K1–K3, P1–P5, A2–A3 | Part of the 30% worksheet component |
| Weekly quiz (start of lecture) | Quiz score | Recall of Week 2 (SDLC, tooling & fuzzing) | Part of the 10% quiz/participation component |
| Viva spot-check / micro-demo | Live reproduction and explanation | P1–P5, A2 | Pass/flag for follow-up |
| Identity-stamped evidence (per-student flag if this lab issues one) | `whoami`/login email/student ID + timestamp on every screenshot | A2 | Integrity control, not a mark |

Grading detail is in the worksheet's own rubric (Part 2 = 20, exploitation + evidence = 40, defence =
25, reflection = 15). Partial credit is available where a student explains the mechanism correctly but
could not land the exploit.

## 7. Materials

- Lab: `labs/week03-cryptography/` — `vulnerable_crypto.py`, `solution_skeleton.py`, `hashes.txt`, `docker-compose.yml`, `worksheet.md`, `README.md`
- Slides: `slides/week03.md`
- Project target for Task 6: `project/starter-app/` (NoteVault) — see the [project README](../../project/README.md) and [REPORT-TEMPLATE](../../project/REPORT-TEMPLATE.md)
- Host tooling students supply: `hashcat` or `john`, and the `rockyou.txt` wordlist
- References: OWASP Password Storage Cheat Sheet; OWASP Cryptographic Storage Cheat Sheet
- Submission channels: [SUBMISSION.md](../../SUBMISSION.md) · Rules of engagement: [ETHICS.md](../../ETHICS.md)

## 8. Risks and contingencies

| Risk | Mitigation |
|---|---|
| Slow/failed `python:3.12-slim` pull in class | Pre-pull before the session; keep a USB copy of the image (`docker save`/`docker load`) |
| Student runs `python vulnerable_crypto.py` on the host and hits `ModuleNotFoundError: No module named 'Crypto'` | Use `docker compose up` (installs `pycryptodome` + `argon2-cffi`), or `pip install pycryptodome argon2-cffi` first; this also covers `argon2` for Tasks 5/7 |
| Students arrive without `hashcat`/`john` or `rockyou.txt` | The compose image ships neither and `labs/toolbox` does not carry them, so Tasks 1 and 6 (55 min combined) stall; require the install in the pre-class prep, and pair a stuck student with a House member who has the wordlist |
| `hashcat` may not find a usable GPU backend on some laptops (notably Apple Silicon) | Fall back to `john --format=raw-md5`, which the worksheet lists as the equivalent |
| Task 9 needs outbound TCP 443 to `example.com`; campus egress filtering/proxy blocks it | Stage a saved cert or point `s_client` at an allowed internal host; keep the `tee /tmp/tls.txt` + separate `grep -E 'Protocol\|New,'` two-step exactly as written, since the version line comes from `s_client`, not `x509` |
| Task 6 depends on NoteVault being reachable | If a student cannot yet reach `/admin`, the seeded unsalted MD5 hashes are readable directly from `seed()` in `project/starter-app/app.py` |
| A student finishes the exploit tasks early | Extension: implement the rehash-on-login upgrade end-to-end (legacy MD5 record → argon2id at next login) and write a test that proves a tampered AES-GCM byte still fails the tag check |
| Copy-paste of a classmate's cracked value or code | Identity-stamped evidence (and the per-student flag if issued) makes submissions attributable; viva spot-check the pair |

## 9. Post-teaching reflection

*Complete after the session — this also feeds the course's engagement data.*

- Attendance / completion: ⬚
- Time actually taken per task (vs. plan): ⬚
- Where the class got stuck, and what unblocked them: ⬚
- Misconception that showed up in the *Explain-in-Plain-English* answers: ⬚
- Quality of the *Audit the AI* critiques (did students catch the planted flaw?): ⬚
- Anything to change before this week runs again: ⬚
