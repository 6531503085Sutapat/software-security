# Live Quiz — self-hosted Kahoot-style game

Real-time, host-paced, speed+accuracy-scored MCQ game. It's a small multi-teacher platform: each
teacher registers an account (invite-gated), builds and manages their own question sets from
Markdown — same source format as the course's other item banks (a `## <topic>` heading followed
by `N. <stem> a) opt · b) opt ✓ · c) opt · d) opt` question lines) — and starts games from them.
Students still join anonymously by PIN, no account needed on that side. Built to remove
Kahoot/Quizizz's free-tier player caps as a blocker at N≈120 and to work for remote/hybrid access
(MFU); **decided 2026-07-29 as the primary quiz mechanism for this course** (Kahoot/Quizizz kept
as fallback — see "Relationship to the Kahoot/Quizizz export path" below) — see
`docs/superpowers/specs/2026-07-10-live-quiz-platform-design.md` for the full design
rationale (the current multi-teacher platform design; the earlier `2026-07-06-live-quiz-design.md`
is the superseded pre-pivot single-classroom draft).

The interface is a KOSEN·KMITL-branded, projector-first host screen and a phone-first player
screen: a live lobby that fills as students join, a ticking countdown, big answer tiles coded by
**colour + shape + text** (so they read for colour-blind students and from the back of the hall),
a live answer-distribution bar chart with the correct answer revealed, a running leaderboard, and
a podium finish. It respects `prefers-reduced-motion` and targets WCAG-AA contrast.

## Run it

```
export INVITE_CODE=letmein   # anyone who has this code can register a teacher account
cd labs/live-quiz && docker compose up --build
```

- Register: open `http://localhost:5050/register`, enter the invite code plus a username and
  password. Registration is closed (the form rejects everyone) until `INVITE_CODE` is set to
  something non-empty — the server also logs a startup warning if it's unset.
- Build a set: after registering you land in `http://localhost:5050/console`. Paste or upload a
  Markdown question set there (same `## <topic>` / `N. <stem> a) ... ✓` format as the course's
  other item banks), give it a title, and save it.
- Host a game: from the console, start a game from one of your own sets — this is what issues the
  6-digit PIN. `/host` itself is login-gated and just redirects you back to the console; it is no
  longer an open "pick a topic, Create game" page anyone can reach.
- Players: open `http://localhost:5050/`, enter the PIN + a pseudonymous nickname (not a real
  name — same PDPA posture as the CTFd scoreboard).

To run it **without Docker** for local dev (e.g. macOS AirPlay squats on port 5000):

```
pip install -r requirements.txt
DB_PATH=./dev.db INVITE_CODE=letmein SECRET_KEY=dev PORT=5057 python app.py
# then open http://localhost:5057/register
```

`DB_PATH` points SQLite at a local file (created on first run) instead of the container's `/data`
volume; `INVITE_CODE` opens registration for this run; `PORT` picks a free port.

## Deploying for real classroom/remote use

This needs to be reachable outside `localhost` for remote/hybrid students (unlike this course's
other Docker-first labs). Deploy on the existing CTFd challenge-host (already has a public IP +
TLS reverse proxy) rather than standing up new infrastructure — see
`instructor/platform-build/deploy/GO-LIVE-CHECKLIST.md` for that host's setup. Set a real
`SECRET_KEY` via the environment (do not use the `docker-compose.yml` default in production).

## Running as a shared platform (multiple teachers)

This is no longer a single-classroom tool with one shared host URL — it's meant to run once per
deployment and serve several teachers, each with their own login and question sets:

1. Set a strong `SECRET_KEY` and an `INVITE_CODE` via the environment before bringing the
   container up (do not use the `docker-compose.yml` defaults in production).
2. Share the invite code, out-of-band, with the teachers who should get accounts.
3. Each teacher registers once at `/register`, signs in at `/login`, and builds their own
   question sets in `/console` (paste or upload Markdown, same format as before).
4. Each teacher starts games from their own sets in the console; a game's results CSV
   (`/host/<pin>/export`) can only be pulled by the teacher who created that game.
5. Students still join anonymously at `/` by PIN — no account needed on that side.

**Back up the `live-quiz-data` named volume.** It's the only place teacher accounts and question
sets persist; losing it means every teacher has to re-register and re-paste their sets. Set
`COOKIE_SECURE=1` once the deployment is actually served over TLS — session cookies otherwise flow
over plain HTTP, which is fine for local dev but not for a public-IP host.

## Accessibility & resilience notes

- **Answers never rely on colour alone** — every option carries a distinct shape (triangle /
  diamond / circle / square), a text label, and an A/B/C/D key. All motion is disabled under
  `prefers-reduced-motion`.
- **Reconnect is seamless.** Players are keyed by `(PIN, nickname)`, so a dropped phone that
  rejoins resumes its score (the score shown is the server's, not a client guess). If a question is
  live when they rejoin, the server re-sends it and the client keeps any answer already locked in,
  rather than wiping it or stranding them on a blank screen.
- **A closed tab no longer skews the room.** A socket disconnect marks that player away, so they
  stop counting toward the projector's "answered" tally and the connected-player count. Every round
  is bounded by the 20-second timer and ends early once the still-connected players have all
  answered. (A disconnect is deliberately *not* treated as an instant "everyone answered" — a brief
  wifi blip of the last un-answered player must not rob them of the round.)
- **Answers are rejected once the round is revealed**, and nicknames are length-capped and
  control-char-stripped server-side, so neither a late tap nor a bypassed client `maxlength` can
  score or corrupt the export.

## Scoring

Wrong answers always score 0. Correct answers score `1000 * (1 - (time_taken/20) / 2)` — full
marks for an instant answer, half marks for one submitted right at the 20-second limit.

## Data handling

Player nicknames are pseudonymous by design — never map them to a real student roster inside
this tool. Results export as a CSV (`nickname, total_score, correct_count, avg_response_time_ms`)
that the instructor manually joins against the real roster afterward, same as CTFd's flow.

## Graded weekly quiz (`/assess`) — replaces Google Forms

**A different mode from the live game, not an extension of it.** The game is
synchronous, anonymous and in-memory; this is asynchronous, identified, persisted,
and its scores become part of someone's grade. They share a process and a
database; they deliberately do not share an identity model.

Decided 2026-07-29 alongside bringing Classroom and the Master Gradebook Sheet
onto our own platform — see the override box in
`instructor/FULL-PLATFORM-DESIGN.md` §4.5.

**Teacher:** `/assess` → publish from a question set → issue codes → mark short
answers → export.
**Student:** `/quiz` → enter the code from their slip → one question per page → done.

### Proctoring: settings became invariants

`instructor/quizzes/weekly/README.md` lists the Form settings that made copying
hard. Every one of them is now enforced server-side, which is a stronger
position, not an equivalent one:

| Google Form setting | Here |
|---|---|
| shuffle question order | per-student permutation, frozen at attempt start |
| shuffle option order | same — and answers are stored in **canonical** index space, so grading never depends on what the student saw |
| one question per page | the cursor lives on the server |
| disable "back" | the cursor is **advance-only** — not a browser hint a student can defeat |
| 1 response per account | `UNIQUE(assessment_id, student_id)` + a one-time code burned on redemption |
| collect email | the roster's `student_id` **is** the identity — the same handle as CTFd, WireGuard and the gradebook |
| release scores later | `assessments.released` |

**The one real trade: we own the access path instead of Google.** That is the
point of the exercise.

### Why a one-time code and not a student password

A student password would be a **fifth** credential to distribute, reset and own —
on top of the CTFd account, the WireGuard `.conf`, and the institutional Google
account. And per `quizzes/weekly/README.md` §"Make copying hard" item 1, the real
control is *"in class, timed, devices away"* — so what's needed is **attribution,
not remote authentication**. A code that dies on redemption needs no store and no
reset path, and makes one-attempt a `UNIQUE` constraint rather than a session check.

Re-issuing is idempotent: adding a late enrolment does not invalidate the sheets
already printed for everyone else.

### Two things that would silently corrupt a term

- **Questions are frozen at publish.** The teacher's question set is a living
  document; an assessment is a snapshot of it. Without this, editing the item bank
  while a quiz is open rewrites questions under students who are mid-attempt.
- **A student who never sat it exports as blank, not 0.** "Didn't sit it" and "sat
  it and scored nothing" are different facts and only the teacher can decide which
  applies. `results.csv` also carries `fully_graded` — a partially-marked quiz has
  a real earned total that is **not** a final mark.

### Exports

| Endpoint | Feeds |
|---|---|
| `results.csv` | `instructor/gradebook/` — `percent` is 0–100, per `GRADEBOOK.md` |
| `q6.csv` | `instructor/quizzes/weekly/verify_q6.py`, so Q6 keeps being checked against each student's own CTFd capture rather than becoming a second unverified path |
| `codes.csv` | the print-and-cut sheet — **per-student, never a shared list** |

### Verified end-to-end

Beyond 48 unit + route tests, a real run against a live server using the course's
**actual** `instructor/quizzes/weekly/item-bank.md`: published a 5-MCQ + Q6 quiz,
issued 3 codes, walked 2 students through over real HTTP (each saw a **different
question order and different option permutations**), left the 3rd deliberately
absent, marked one Q6 3/3 and the other 0/3, and fed the resulting `results.csv`
straight into `gradebook.compute()` → `FINAL 74.45 B` / `72.70 B`, with the absent
student correctly refused as "nothing to enter". Re-entering a burned code was
refused.

## Worksheet submission + rubric grading (`/work`, `/submit`) — replaces Classroom

**Teacher:** `/work` → set an assignment (rubric defaults to the worksheets' own
20/40/25/15 = 100) → issue codes → mark → export.
**Student:** `/submit` → code from their slip → upload, replace, add the required
AI-disclosure note, read feedback once released.

### The download endpoint is the security-critical route

Everything a student uploads is attacker-controlled bytes, and the teacher who
reads it is signed in with the session that can change every mark. So uploads are
**never rendered inline**: `Content-Type: application/octet-stream` (never the
uploaded type, never guessed from the extension), `Content-Disposition:
attachment`, `nosniff`, and `Content-Security-Policy: sandbox; default-src 'none'`.

Verified for real by uploading
`<svg …><script>alert(document.cookie)</script></svg>` and fetching it **as the
teacher**: served as an opaque download with the script still inert bytes. Another
student and an anonymous request both get **404**, not 403 — a probe learns nothing.

### A student never names a file on disk

`store_file` generates the on-disk name from `secrets.token_hex`; the student's
filename is stored for display only. Traversal, collision and extension-confusion
are impossible by construction rather than filtered. Proven by uploading
`../../../../etc/passwd` — it landed as a flat 48-hex file alongside the others,
and shows in the UI as `passwd`.

### Backups: the trap that would only surface during a restore

Submissions are **files on a volume**, so the SQLite dump contains none of them.
Restoring the database alone gives you submission rows pointing at files that no
longer exist — a restore that looks successful and has lost every student's work.
`backup-ctfd-db.sh` therefore tars the upload directory in the same run, keeps
those archives **180 days** (not 14 — a mark can be disputed long after), and its
restore instructions say to restore both or neither. Round-trip verified:
3 files archived, restored, bytes identical.

### Not a zero

A student who never handed in exports as blank, never `0`. **Late is shown, not
deducted** — SUBMISSION.md's −10%/day is the teacher's call, applied once,
deliberately. An unmarked rubric row is `NULL`, so `fully_graded=0` travels with
the row and a partial mark can't be imported as a final one.

## Relationship to the Kahoot/Quizizz export path

**DECIDED 2026-07-29: this app is the PRIMARY quiz mechanism**, not Kahoot/Quizizz — their
free tier caps at ~40-50 players/game, which forces an N≈120 cohort to be split and re-run
per section; this app has no such cap. `instructor/quizzes/kahoot/make_kahoot_import.py`
(exports to real Kahoot/Quizizz) still exists and still works as a **fallback** for when this
deployment itself is down.

## Known limitations (not blocking for classroom use)

`/host`, `/console`, and `/host/<pin>/export` all require a teacher login now (see "Running as a
shared platform" above), and export is further scoped so only the teacher who created a given game
can download its results CSV. This used to be a real gap — noted here since an earlier version of
this doc flagged it — but it's resolved as of this build.

- **Nicknames aren't unique.** Two students who pick the same nickname share one score row (and one
  reconnect slot). Harmless for casual play; if it matters for grading, ask students to use their
  pseudonymous student code. A future fix would reject or auto-suffix a duplicate at join time.

Resolved since the first build (kept here as a record): CSV export now neutralizes spreadsheet
formula-injection prefixes; answers are rejected once a round is revealed (no post-timeout scoring);
reconnecting mid-question re-shows the question and keeps the score server-authoritative; the
countdown steps rather than sweeps under `prefers-reduced-motion`; brand-orange chrome uses the
deep shade so white text on it clears WCAG-AA; and host/console/export access — previously
unauthenticated, trusting only PIN secrecy — now requires a teacher login, with exports further
scoped to the creating teacher.
