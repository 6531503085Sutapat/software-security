# Live Quiz Platform — Multi-Teacher Accounts + Question-Set Console (Design)

**Status:** Approved by user 2026-07-10 (verbal). Not yet implemented.

## Why

`labs/live-quiz/` today is a **single-classroom** tool: it reads two fixed item-bank files
mounted at container start (`ITEM_BANK_PATHS`), and *anyone* who reaches `/host` can create a
game or download any game's results — there is no authentication (a documented known limitation).
That is fine for one instructor on their own machine, but the user wants other teachers to **use
the platform to run their own quizzes with their own questions**, without the instructor editing
files on the server for them.

This design turns it into a **small multi-teacher platform**: a teacher registers (gated by an
invite code), logs in, manages their own question sets through a web console, and starts games
from them. Students are unchanged — they still join anonymously by PIN + nickname.

Explicitly NOT in scope (keep it a teacher tool, not an enterprise SaaS): org/team hierarchies,
billing, email verification/password reset flows, per-question media, a question-authoring WYSIWYG
(teachers paste/upload the same simple markdown the parser already reads), or analytics dashboards
beyond the existing per-game CSV export.

## Decisions locked with the user

1. **Registration = invite code.** The deployment owner sets one `INVITE_CODE` (env). A teacher
   self-registers with username + password + that code. No open signup (would invite abuse on a
   public host); no per-account manual provisioning by the owner (too much admin for a colleague
   group). Rotating the code cuts off new signups without touching existing accounts.
2. **DB-backed question sets fully replace the file-mount model.** The old
   `ITEM_BANK_PATHS`/volume-mount path is removed as the game source; question sets now live in the
   database, owned per teacher. A one-time optional import (`IMPORT_ITEM_BANKS`, off by default)
   can seed the *first* registered teacher's account from mounted files, so the instructor's
   existing banks aren't lost — but steady state is DB-only.

## Architecture

Still one Flask + Flask-SocketIO app, one container. Added: a SQLite database (one file on a
persistent volume) and an auth/session layer. The Socket.IO game engine (`game.py`, `scoring.py`,
the in-memory `GAMES` dict, the whole live round loop) is **unchanged** — a game is still created
from a list of questions; the only change is *where that list comes from* (a DB question set the
logged-in teacher owns, instead of a mounted file + topic dropdown).

```
labs/live-quiz/
├── app.py            # + auth routes, console routes, login-required guards on host/*
├── auth.py           # NEW: register/login/logout, password hashing, session helpers, login_required
├── db.py             # NEW: SQLite connection + schema init + query helpers (teachers, question_sets)
├── quiz_loader.py    # unchanged parser — now called on a set's stored markdown, not a file path
├── game.py, scoring.py  # unchanged
├── templates/
│   ├── login.html, register.html   # NEW
│   ├── console.html                # NEW: list/create/edit/delete my sets + Start game
│   ├── host.html, player.html      # host.html loses the file-topic dropdown (set chosen in console)
├── static/           # + console.js, reuse existing style.css (KOSEN·KMITL brand)
├── schema.sql        # NEW: table definitions
└── docker-compose.yml  # + a named volume for the SQLite file; INVITE_CODE/SECRET_KEY env
```

### Data model (SQLite)

```sql
CREATE TABLE teachers (
  id            INTEGER PRIMARY KEY,
  username      TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,        -- bcrypt
  created_at    TEXT NOT NULL
);
CREATE TABLE question_sets (
  id          INTEGER PRIMARY KEY,
  teacher_id  INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  source_md   TEXT NOT NULL,          -- raw markdown; the parser's input, source of truth
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
```

Parsed questions are derived on demand from `source_md` via the existing `quiz_loader`, not stored
separately — one source of truth, and editing a set is just editing its markdown. A set may
contain multiple `## topic` headings; when starting a game the teacher picks which topic (same
dropdown the host page has today, now populated from the chosen set instead of mounted files).

### Auth

- **Passwords:** bcrypt (`bcrypt` lib) — a security course's own tool must model this correctly.
- **Sessions:** Flask signed-cookie session storing `teacher_id`; cookie flags `HttpOnly`,
  `SameSite=Lax`, and `Secure` when served over TLS (behind the reverse proxy). `SECRET_KEY` stays
  the existing env (already there), now load-bearing for auth, so a weak default must warn loudly.
- **CSRF:** all state-changing teacher forms (register, login, create/edit/delete set, create game)
  carry a per-session CSRF token verified server-side. (The student socket flow is unaffected —
  it's not cookie-authenticated.)
- **`login_required` guard** on every `/console*`, `/host`, `/host/create`, `/host/<pin>/export`.
  This closes the old "host endpoints unauthenticated" known limitation as a side effect. Ownership
  is re-checked on every set/game action (no IDOR: a teacher can only touch sets where
  `teacher_id == session.teacher_id`, and export only games they created).

### Data flow — creating and running a game

1. Teacher logs in → `/console` lists their sets.
2. Create/edit a set: paste markdown or upload a `.md` file → server parses with `quiz_loader`,
   shows a **preview** (topics found, question count per topic, any un-parseable lines flagged) →
   save to `question_sets`.
3. "Start game" on a set → pick a topic → `POST /host/create` (login-required, ownership-checked)
   builds a `GameSession` from that set+topic's parsed questions exactly as today → PIN issued.
4. From here the live game is **identical to the current app**: students join `/` by PIN, the
   host drives it, scoring/reveal/leaderboard/CSV export all unchanged. The game is still
   in-memory and ephemeral; only the *definition* (the question set) is persisted.

### Error handling

- Empty/invalid `INVITE_CODE` on register → clear form error, no account created.
- Duplicate username → clear form error (unique constraint).
- Markdown that parses to **zero** questions → refuse to save with a message (don't let a teacher
  start an empty game).
- Upload size cap + `.md`/text only (reject binary/huge files) — defense on the upload path.
- Missing DB file / first boot → schema auto-initialized from `schema.sql`.
- Weak `SECRET_KEY` or missing `INVITE_CODE` → loud startup warning (same pattern as the existing
  missing-item-bank warning).

### Testing plan

TDD per component, extending the existing 40-test suite:
- `db.py`: schema init idempotent; teacher/set CRUD; cascade delete; per-teacher isolation query.
- `auth.py`: bcrypt round-trip; register rejects bad invite code / duplicate username; login
  rejects wrong password; `login_required` redirects anonymous → login.
- Route tests (Flask test client): `/console` requires login; a teacher cannot read/edit/delete
  another teacher's set (IDOR probe returns 403/404, not the data); `/host/create` requires login
  and an owned set; CSRF token required on POSTs.
- Set-from-markdown → game: a saved set's parsed questions produce a runnable `GameSession`
  (reuses the existing socket round-trip test, sourced from a DB set instead of a file).
- Keep all existing game-engine tests green (they don't touch auth/DB).
- Real browser smoke run (like the redesign): register → login → create set (paste + upload +
  preview) → start game → a student joins and plays → CSV export → logout.

## Deployment changes

- `docker-compose.yml`: add a **named volume** for the SQLite file (so accounts/sets survive
  restarts — unlike the ephemeral games), and require `SECRET_KEY` + `INVITE_CODE` env. Drop the
  two item-bank bind-mounts (replaced by the DB), keep an optional `IMPORT_ITEM_BANKS` mount for
  the one-time seed.
- README: new "Running as a shared platform" section — set `INVITE_CODE`, share it with teachers,
  each registers once; back up the SQLite volume; still behind the CTFd host's TLS proxy for
  remote/hybrid use. The public-IP + auth combination means the old "host has no auth" caveat is
  now resolved and should be removed from Known limitations.

## Migration / backward-compat

The app changes from "starts a game from mounted files" to "requires a login + a question set."
There is no student-facing breakage (join flow identical). For an existing single-classroom user,
the one-time `IMPORT_ITEM_BANKS` seed reproduces their old banks as the first teacher's sets, so
nothing is lost. This is a deliberate, documented one-way move to the account model, not a dual
mode kept forever (dual modes = permanent complexity for little gain).
