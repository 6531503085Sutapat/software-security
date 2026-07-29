-- schema_assess.sql — the graded weekly-quiz tables, applied idempotently at
-- startup alongside schema.sql.
--
-- This is a DIFFERENT MODE from the live Kahoot-style game, not an extension of
-- it. The game is synchronous, anonymous and in-memory; this is asynchronous,
-- identified, persisted, and its numbers end up in someone's grade. Sharing a
-- database with the game is fine; sharing its identity model is not.
--
-- Replaces the Google Form path described in
-- instructor/quizzes/weekly/README.md. Every proctoring control that README
-- lists as a *Form setting* is a server-side invariant here — see the notes on
-- `attempts` below.

-- Roster an assessment can be assigned to. `student_id` is the SAME handle used
-- everywhere else — the CTFd username, the WireGuard peer name, the gradebook
-- row key (see instructor/roster/). Not a new identity; a reference to the
-- existing one.
CREATE TABLE IF NOT EXISTS students (
  id          INTEGER PRIMARY KEY,
  teacher_id  INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
  student_id  TEXT NOT NULL,
  name        TEXT NOT NULL DEFAULT '',
  email       TEXT NOT NULL DEFAULT '',
  created_at  TEXT NOT NULL,
  UNIQUE (teacher_id, student_id)
);

CREATE TABLE IF NOT EXISTS assessments (
  id                INTEGER PRIMARY KEY,
  teacher_id        INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
  title             TEXT NOT NULL,
  variant           TEXT NOT NULL DEFAULT 'A',   -- parallel A/B forms
  shuffle_questions INTEGER NOT NULL DEFAULT 1,
  shuffle_options   INTEGER NOT NULL DEFAULT 1,
  time_limit_sec    INTEGER,                     -- NULL = untimed
  opens_at          TEXT,                        -- ISO-8601 UTC; NULL = no window
  closes_at         TEXT,
  released          INTEGER NOT NULL DEFAULT 0,  -- scores visible to students
  created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assess_teacher ON assessments(teacher_id);

-- FROZEN AT PUBLISH. The teacher's question set is a living document; an
-- assessment is a snapshot of it. Without this, editing the item bank while a
-- quiz is open silently rewrites questions under students who are mid-attempt,
-- and re-grades submitted attempts against text they never saw.
CREATE TABLE IF NOT EXISTS assessment_questions (
  id            INTEGER PRIMARY KEY,
  assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  position      INTEGER NOT NULL,          -- canonical order, pre-shuffle
  kind          TEXT NOT NULL,             -- 'mcq' | 'short'
  stem          TEXT NOT NULL,
  options_json  TEXT NOT NULL DEFAULT '[]',
  correct       INTEGER,                   -- 0-based, canonical; NULL for 'short'
  points        REAL NOT NULL DEFAULT 1.0,
  UNIQUE (assessment_id, position)
);

-- One-time access code per (assessment, student). Generated at publish, handed
-- out on paper with the quiz (the real proctoring control is that students are
-- in the room — quizzes/weekly/README.md §"Make copying hard" item 1), redeemed
-- once, burned.
--
-- Deliberately NOT a student password: that would be a fifth credential to
-- distribute, reset and own, on top of the CTFd account, the WireGuard .conf and
-- the institutional Google account. A code that dies on redemption needs no
-- store and no reset path, and makes "one attempt" a UNIQUE constraint rather
-- than a session check.
CREATE TABLE IF NOT EXISTS attempt_codes (
  code          TEXT PRIMARY KEY,
  assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  student_id    TEXT NOT NULL,
  issued_at     TEXT NOT NULL,
  redeemed_at   TEXT,
  UNIQUE (assessment_id, student_id)
);

CREATE TABLE IF NOT EXISTS attempts (
  id            INTEGER PRIMARY KEY,
  assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  student_id    TEXT NOT NULL,
  code          TEXT NOT NULL REFERENCES attempt_codes(code),
  -- Per-student permutations, frozen when the attempt starts. Frozen rather
  -- than recomputed because a reshuffle on refresh would leak information (a
  -- second ordering of the same options) and would break advance-only.
  order_json    TEXT NOT NULL,   -- [question position, ...] in this student's order
  options_json  TEXT NOT NULL,   -- {position: [canonical option index, ...]}
  -- Advance-only. This is the "disable back" control, enforced on the server
  -- instead of in the browser — a Form setting a student can defeat with the
  -- back button becomes an invariant a student cannot address.
  cursor        INTEGER NOT NULL DEFAULT 0,
  started_at    TEXT NOT NULL,   -- the time limit is measured from here, server-side
  submitted_at  TEXT,
  UNIQUE (assessment_id, student_id)   -- one attempt per student, structurally
);
CREATE INDEX IF NOT EXISTS idx_attempts_assessment ON attempts(assessment_id);

CREATE TABLE IF NOT EXISTS answers (
  id            INTEGER PRIMARY KEY,
  attempt_id    INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
  question_id   INTEGER NOT NULL REFERENCES assessment_questions(id),
  -- CANONICAL option index, never the shuffled one the student saw. Grading
  -- must not depend on the permutation.
  choice        INTEGER,
  text          TEXT,            -- short answer (Q6)
  auto_points   REAL,            -- MCQ, graded on submit
  manual_points REAL,            -- short answer, graded by the teacher later
  graded_at     TEXT,
  UNIQUE (attempt_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_answers_attempt ON answers(attempt_id);
