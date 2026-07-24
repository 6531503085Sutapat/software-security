# Live Quiz — self-hosted Kahoot-style game

Real-time, host-paced, speed+accuracy-scored MCQ game. It's a small multi-teacher platform: each
teacher registers an account (invite-gated), builds and manages their own question sets from
Markdown — same source format as the course's other item banks (a `## <topic>` heading followed
by `N. <stem> a) opt · b) opt ✓ · c) opt · d) opt` question lines) — and starts games from them.
Students still join anonymously by PIN, no account needed on that side. Built to remove
Kahoot/Quizizz's free-tier player caps as a blocker at N≈120 and to work for remote/hybrid access
(MFU) — see `docs/superpowers/specs/2026-07-10-live-quiz-platform-design.md` for the full design
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

## Relationship to the Kahoot/Quizizz export path

`instructor/quizzes/kahoot/make_kahoot_import.py` (exports to real Kahoot/Quizizz) still exists
and still works — this is a parallel option for when Kahoot's free-tier player cap (~40-50) is
the actual blocker, not a replacement.

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
