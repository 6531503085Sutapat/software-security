# Live Quiz — Self-Hosted Kahoot-Style Game (Design)

**Status:** Approved by user 2026-07-06. Not yet implemented.

## Why

The course already runs weekly retrieval-practice MCQ quizzes as a live, timed, leaderboard game
(the "signature game" pattern used throughout the syllabus). Today that means exporting the
existing MCQ item banks into Kahoot/Quizizz's own import format
(`instructor/quizzes/kahoot/make_kahoot_import.py` → `kahoot-import.xlsx`). That works, but:

- Kahoot's free tier caps out around 40-50 concurrent players — this course runs sections up to
  N≈120, and the MFU replication arm needs remote/hybrid access (not just one room's WiFi).
- Considered self-hosting the existing open-source alternative **ClassQuiz**
  (github.com/mawoka-myblock/ClassQuiz — actively maintained, real-time, native Kahoot-import
  support) instead of building from scratch. User explicitly chose to build our own rather than
  adopt it, to keep the stack consistent with the rest of the course's tooling (Python/Flask
  everywhere; ClassQuiz is FastAPI + python-socketio + SvelteKit, a second language/toolchain to
  maintain) and to avoid depending on someone else's project cadence for a course-critical tool.

## Scope (v1)

- **Individual play only.** House/team scoring is a v2 layer computed after the fact from
  individual results (nickname → House mapping), not built into the game engine itself.
- **Live, host-paced, synchronous** gameplay — matching genuine Kahoot mechanics: the whole room
  sees the same question at the same time, host controls advancing, speed+accuracy scoring,
  live leaderboard after every question. (Considered and rejected: self-paced/async mode — the
  user confirmed the live, synchronized experience is the actual requirement, not just MCQ
  delivery.)
- **Remote/hybrid access required.** Unlike the course's Docker-first labs (localhost only), this
  needs to be reachable by students outside the physical room (MFU's separate site, hybrid
  attendance). Deploys on the **existing CTFd challenge-host** (already has a public IP + TLS
  reverse proxy per `instructor/platform-build/deploy/GO-LIVE-CHECKLIST.md`'s two-host pattern) —
  not a new host/domain.
- Reuses the existing MCQ item banks (`instructor/quizzes/weekly/item-bank.md` +
  `instructor/quizzes/review-quiz-item-bank.md`) as the question source — same parser logic as
  `make_kahoot_import.py` already has, adapted rather than duplicated. Both files are already
  organized under `## <week/topic>` headers (see `make_kahoot_import.py`'s `parse_file()`); the
  host selects which topic(s) to play from a dropdown on the host screen at game-creation time —
  no separate per-game config file to hand-edit.

## Tech stack

**Flask + Flask-SocketIO** (Python), chosen over two alternatives:
- *Node.js + Socket.IO* — rejected: introduces a second language/runtime into a 100%-Python
  course repo.
- *FastAPI + python-socketio + SvelteKit* (mirrors ClassQuiz's own architecture) — rejected:
  proven pattern, but the separate frontend build step adds complexity this small-scale
  (dozens–~200 concurrent players, not thousands) use case doesn't need.

Flask + Flask-SocketIO matches every other lab in this repo (all plain Flask), deploys via
`docker compose up` identically to the rest of the course, and is mature enough for this scale.

## Architecture

```
labs/live-quiz/
├── app.py                # Flask + Flask-SocketIO server
├── quiz_loader.py         # parses item-bank.md -> question sets (adapted from
│                          # instructor/quizzes/kahoot/make_kahoot_import.py's parser)
├── templates/
│   ├── host.html          # instructor/projector view
│   └── player.html        # student view (phone/laptop)
├── static/
│   ├── host.js
│   └── player.js
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

**Roles:**
- **Host** (instructor): starts a game, gets a 6-digit PIN, controls advancing through questions,
  sees per-question results and the running leaderboard.
- **Player** (student): joins via PIN + a pseudonymous nickname (no real names — same PDPA
  posture as the CTFd scoreboard and the existing Kahoot README's note), answers each question as
  it's shown.

**Real-time transport:** Flask-SocketIO room per game (room id = the PIN). Host and all players
in a game share one room; the server is the single source of truth for game state (current
question, per-player scores, timing) — nothing authoritative lives in any client.

## Data flow (per question)

1. Host clicks "Next question" → server broadcasts `question:show` (question text, up to 4
   answers, time limit) to the whole room and records the **server-side** start timestamp (never
   trust a client-reported time, to prevent cheating on timing). Time limit is a fixed 20 seconds
   per question (matches `make_kahoot_import.py`'s existing `TIME_LIMIT` constant, for
   consistency between the two delivery paths) — not read per-item from the markdown source,
   which has no time-limit field today.
2. Player taps an answer → client emits `answer:submit` with the chosen index. Server computes
   elapsed time (`now - question_start`) immediately, scores it (see below), and sends
   per-player instant feedback (correct/wrong + points this round) — nobody else sees this yet.
3. When the time limit elapses OR every currently-connected player has answered (whichever is
   first), server broadcasts `question:results` to everyone: the correct answer, an answer-choice
   distribution (bar chart, Kahoot-style), and the updated leaderboard (top 5 + each player's own
   rank).
4. Host clicks "Next" to repeat, or "Show final leaderboard" after the last question.

## Scoring

```
wrong answer  -> 0 points
correct answer -> 1000 * (1 - (time_taken / time_limit) / 2)
```
Instant correct answers score full marks (1000); a correct answer submitted right at the time
limit scores half (500); wrong is always 0 (no penalty beyond forfeiting the round). 1000 is a
fixed per-question value (matches Kahoot's own convention) — not read from the item bank's own
point-value column, keeping every question worth the same regardless of source.

## Reconnection handling

Players are keyed by **(PIN, nickname)**, not by socket/session id — a dropped connection
(common on classroom WiFi/phone data) that rejoins with the same PIN + nickname resumes the same
score and game position rather than restarting at zero. If the host disconnects, the game simply
pauses (state lives server-side, not in the host's browser) rather than crashing the session for
everyone else.

## Data export

At game end, write a CSV (`nickname, total_score, correct_count, avg_response_time_ms`) into the
git-ignored `instructor/` tree — never tied to real student names in the game itself (same
pseudonymization posture as the rest of the course's research/grading tooling). The instructor
manually joins this against the real roster afterward if it's going into the gradebook or House
points, the same way CTFd scoreboard results are handled today.

## Testing plan

Before first real classroom use: run `docker compose up` locally and simulate one host + several
players (multiple browser tabs), verifying broadcast timing, scoring math, and the
reconnect-resumes-score behavior actually work — matching this project's established discipline
of proving deployment infrastructure via real runs, not just reading the code.

## Explicitly out of scope for v1

- Team/House mode (v2, layered on top of individual results afterward)
- Media/images in questions
- Question authoring UI (questions come from the existing markdown item banks only)
- Any change to the existing Kahoot/Quizizz export path (`make_kahoot_import.py` stays as-is —
  this is a parallel, self-hosted option for when free-tier player caps are the blocker)
