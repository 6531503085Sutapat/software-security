# Live Quiz — self-hosted Kahoot-style game

Real-time, host-paced, speed+accuracy-scored MCQ game, reusing the course's existing item banks
(`instructor/quizzes/weekly/item-bank.md` + `instructor/quizzes/review-quiz-item-bank.md`).
Built to remove Kahoot/Quizizz's free-tier player caps as a blocker at N≈120 and to work for
remote/hybrid access (MFU) — see `docs/superpowers/specs/2026-07-06-live-quiz-design.md` for the
full design rationale.

The interface is a KOSEN·KMITL-branded, projector-first host screen and a phone-first player
screen: a live lobby that fills as students join, a ticking countdown, big answer tiles coded by
**colour + shape + text** (so they read for colour-blind students and from the back of the hall),
a live answer-distribution bar chart with the correct answer revealed, a running leaderboard, and
a podium finish. It respects `prefers-reduced-motion` and targets WCAG-AA contrast.

## Run it

```
cd labs/live-quiz && docker compose up --build
```

- Host: open `http://localhost:5050/host`, pick a topic, "Create game" for a PIN.
- Players: open `http://localhost:5050/`, enter the PIN + a pseudonymous nickname (not a real
  name — same PDPA posture as the CTFd scoreboard).

To run it **without Docker** for local dev (e.g. macOS AirPlay squats on port 5000), point it at
any item-bank markdown and pick a free port:

```
pip install -r requirements.txt
ITEM_BANK_PATHS=/abs/path/to/item-bank.md PORT=5057 python app.py
# then open http://localhost:5057/host
```

`ITEM_BANK_PATHS` is an `os.pathsep`-separated list; unset, it falls back to the container mount
points. If no bank files are found the server logs a warning at startup and the host screen shows
an explicit "no item banks" message instead of a blank dropdown.

## Deploying for real classroom/remote use

This needs to be reachable outside `localhost` for remote/hybrid students (unlike this course's
other Docker-first labs). Deploy on the existing CTFd challenge-host (already has a public IP +
TLS reverse proxy) rather than standing up new infrastructure — see
`instructor/platform-build/deploy/GO-LIVE-CHECKLIST.md` for that host's setup. Set a real
`SECRET_KEY` via the environment (do not use the `docker-compose.yml` default in production).

## Accessibility & resilience notes

- **Answers never rely on colour alone** — every option carries a distinct shape (triangle /
  diamond / circle / square), a text label, and an A/B/C/D key. All motion is disabled under
  `prefers-reduced-motion`.
- **Reconnect is seamless.** Players are keyed by `(PIN, nickname)`, so a dropped phone that
  rejoins resumes its score; if a question is live when they rejoin, the server re-sends it so they
  can still answer (rather than staring at a blank screen until the next question).
- **A closed tab no longer stalls the round.** A socket disconnect marks that player away, so the
  "everyone answered → reveal early" path still fires for the players who are still connected
  instead of waiting out the full 20s timer.

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

- **A truly last-instant answer can miss the round's on-screen tally.** The client disables the
  answer tiles the moment you tap and again at the reveal, so the normal ways to answer "late" are
  closed. The remaining edge is an answer that lands in the same instant the 20-second timeout
  reveals the results: it's still scored correctly server-side and shows up in the next round's
  leaderboard, but won't retroactively edit the distribution already painted for that round. Narrow
  and self-healing; doesn't affect end-of-game totals.
- **CSV export (`/host/<pin>/export`) writes nicknames unescaped.** This is a CSV/spreadsheet
  formula-injection consideration (a nickname starting with `=`, `+`, `-`, or `@` could execute as
  a formula if the CSV is opened directly in Excel/Sheets without import sanitization) — separate
  from the innerHTML/XSS class of bug already handled in the client. Not fixed in this build; if the
  exported CSV is ever opened directly (rather than parsed programmatically), treat nickname cells
  as untrusted and don't trust formula results from them.
- **Getting the item banks onto the deploy host still needs a documented step.** The app now fails
  loudly when no banks are found (startup warning + an on-screen "no item banks" message) and lets
  you point `ITEM_BANK_PATHS` anywhere, so it no longer degrades silently. What's still undocumented
  is *how* `instructor/quizzes/*` should be synced onto the CTFd challenge-host for a real remote
  session — decide that (a bind-mount, a copy step, or an `ITEM_BANK_PATHS` pointing at a synced
  location) before go-live.
- **Host endpoints (`/host`, `/host/create`, `host_next`, `/host/<pin>/export`) have no
  authentication.** Anyone who reaches the host URL, or who knows/guesses a game's 6-digit PIN,
  can advance someone else's game or download its results CSV. This mirrors Kahoot's own
  PIN-based trust model and is low-stakes for pseudonymous classroom play, but is worth noting
  since this deploys on a public-IP host for remote/hybrid access rather than staying on
  localhost. Not fixed in this build.
