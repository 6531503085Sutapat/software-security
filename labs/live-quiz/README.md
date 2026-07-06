# Live Quiz — self-hosted Kahoot-style game

Real-time, host-paced, speed+accuracy-scored MCQ game, reusing the course's existing item banks
(`instructor/quizzes/weekly/item-bank.md` + `instructor/quizzes/review-quiz-item-bank.md`).
Built to remove Kahoot/Quizizz's free-tier player caps as a blocker at N≈120 and to work for
remote/hybrid access (MFU) — see `docs/superpowers/specs/2026-07-06-live-quiz-design.md` for the
full design rationale.

## Run it

```
cd labs/live-quiz && docker compose up --build
```

- Host: open `http://localhost:5050/host`, pick a topic, "Create game" for a PIN.
- Players: open `http://localhost:5050/`, enter the PIN + a pseudonymous nickname (not a real
  name — same PDPA posture as the CTFd scoreboard).

## Deploying for real classroom/remote use

This needs to be reachable outside `localhost` for remote/hybrid students (unlike this course's
other Docker-first labs). Deploy on the existing CTFd challenge-host (already has a public IP +
TLS reverse proxy) rather than standing up new infrastructure — see
`instructor/platform-build/deploy/GO-LIVE-CHECKLIST.md` for that host's setup. Set a real
`SECRET_KEY` via the environment (do not use the `docker-compose.yml` default in production).

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

## Known limitations (found during build/verification, not blocking)

- **Late answers after a round's results are revealed don't retroactively update that round's
  already-shown leaderboard/distribution**, though the points ARE correctly credited server-side
  and appear in every subsequent round's leaderboard (verified: a late-answering player's score
  was folded correctly into the very next question's broadcast). Only matters if a player answers
  after the 20s timeout or after everyone else has already answered; narrow window, self-heals by
  the next round. Worth a future fix (e.g., disable answer buttons client-side once results are
  shown, or have the server reject/flag post-reveal submissions) but doesn't affect end-of-game
  correctness.
- **CSV export (`/host/<pin>/export`) writes nicknames unescaped.** This is a CSV/spreadsheet
  formula-injection consideration (a nickname starting with `=`, `+`, `-`, or `@` could execute as
  a formula if the CSV is opened directly in Excel/Sheets without import sanitization) — separate
  from the innerHTML/XSS class of bug already fixed in `host.js`/`player.js`. Not fixed in this
  build; if the exported CSV is ever opened directly (rather than parsed programmatically), treat
  nickname cells as untrusted and don't trust formula results from them.
- **Production deployment layout is not yet fully specified.** This lab's `docker-compose.yml`
  bind-mounts the real item-bank files via a path relative to the repo root
  (`../../instructor/quizzes/...`), which assumes the repo (with `instructor/` populated) is
  checked out on the CTFd challenge-host with that same relative layout. No existing deploy doc
  (`instructor/platform-build/deploy/GO-LIVE-CHECKLIST.md` and siblings) currently specifies how
  `instructor/quizzes/*` gets synced onto that host, and if the layout assumption is wrong, the
  app currently degrades silently (empty topic dropdown, no error) rather than failing loudly.
  Resolve this — and consider adding a startup warning when the item-bank paths are missing —
  before relying on this in a real class session.
- **Reconnecting mid-question doesn't re-show the in-progress question.** `GameSession.join()`
  correctly resumes a rejoining player's score, but the server never re-emits `question:show` to
  them on rejoin — if a player drops and reconnects while a question is active, their screen stays
  blank (or shows the previous question) until the host advances to the next one, so they can't
  answer the round they reconnected into. Only affects players who disconnect mid-question, not
  general reconnection. Fix: have `on_player_join` also emit the current question state (from
  `game.current_question()`) when one is active.
- **Host endpoints (`/host`, `/host/create`, `host_next`, `/host/<pin>/export`) have no
  authentication.** Anyone who reaches the host URL, or who knows/guesses a game's 6-digit PIN,
  can advance someone else's game or download its results CSV. This mirrors Kahoot's own
  PIN-based trust model and is low-stakes for pseudonymous classroom play, but is worth noting
  since this deploys on a public-IP host for remote/hybrid access rather than staying on
  localhost. Not fixed in this build.
