-- schema_submit.sql — worksheet submission + rubric grading.
-- Replaces Google Classroom's collect-and-grade role. Applied idempotently at
-- startup alongside schema.sql and schema_assess.sql.
--
-- IDENTITY: the same one-time-code model as the graded quiz. No student password
-- anywhere on this platform — that would be a fifth credential to distribute,
-- reset and own. Unlike a quiz, a submission code stays usable until the
-- deadline (a student must be able to come back and replace a bad upload), and
-- read-only afterwards so they can still read their feedback.
--
-- FILES LIVE ON DISK, NOT IN THIS DATABASE. Decided rather than drifted into:
-- worksheet PDFs with embedded screenshots run to megabytes, and at N≈120 × 13
-- worksheets that would make the nightly SQLite dump enormous and slow enough to
-- start failing quietly. The cost of that choice is that `backup-ctfd-db.sh`
-- must tar the upload directory — files on a Docker volume are NOT in the
-- database backup, and nothing would tell you they were missing until a restore.
-- That edit ships with this schema, not after it.

CREATE TABLE IF NOT EXISTS assignments (
  id           INTEGER PRIMARY KEY,
  -- Which course this belongs to. A STRING, not a foreign key: courses are
  -- configured in the content registry ($COURSES / the curriculum monorepo),
  -- not stored here, so a `courses` table would be a second source of truth.
  -- Validated at the write boundary by course_scope.check().
  course_slug  TEXT,
  teacher_id   INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
  title        TEXT NOT NULL,
  -- Optional link to a week in the content plane (/learn/<week_slug>), so the
  -- brief and the worksheet it refers to are one click apart.
  week_slug    TEXT,
  instructions TEXT NOT NULL DEFAULT '',
  due_at       TEXT,                      -- ISO-8601 UTC; NULL = no deadline
  -- The real rubric, from the worksheets themselves:
  --   Lecture questions 20 / Exploitation+evidence 40 / Defense 25 / Reflection 15
  -- Stored per-assignment rather than hard-coded because W16 (capstone) and the
  -- project use different splits.
  rubric_json  TEXT NOT NULL,
  released     INTEGER NOT NULL DEFAULT 0, -- marks + feedback visible to students
  created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assign_teacher ON assignments(teacher_id);

CREATE TABLE IF NOT EXISTS submit_codes (
  code          TEXT PRIMARY KEY,
  assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
  student_id    TEXT NOT NULL,
  issued_at     TEXT NOT NULL,
  UNIQUE (assignment_id, student_id)
);

CREATE TABLE IF NOT EXISTS submissions (
  id            INTEGER PRIMARY KEY,
  assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
  student_id    TEXT NOT NULL,
  created_at    TEXT NOT NULL,
  -- Set on the FIRST upload and updated on each replacement. Lateness is
  -- computed from this against due_at at grading time, never stored as a flag —
  -- a stored flag goes stale the moment a deadline is extended, which happens.
  submitted_at  TEXT,
  -- The student's own note (AI-tool disclosure lives here — SUBMISSION.md
  -- requires it on every submission).
  note          TEXT NOT NULL DEFAULT '',
  UNIQUE (assignment_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_sub_assignment ON submissions(assignment_id);

CREATE TABLE IF NOT EXISTS submission_files (
  id            INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  -- What the student called it, sanitised for DISPLAY only. Never used to build
  -- a path.
  display_name  TEXT NOT NULL,
  -- What it is called on disk: a random token this application chose. A student
  -- never influences a byte of the filesystem path, so traversal, collision and
  -- extension-confusion are all structurally impossible rather than filtered.
  stored_name   TEXT NOT NULL UNIQUE,
  size_bytes    INTEGER NOT NULL,
  sha256        TEXT NOT NULL,
  uploaded_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_files_submission ON submission_files(submission_id);

CREATE TABLE IF NOT EXISTS rubric_scores (
  id            INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  criterion     TEXT NOT NULL,
  points        REAL,                     -- NULL = not marked yet, NOT zero
  comment       TEXT NOT NULL DEFAULT '',
  graded_at     TEXT,
  UNIQUE (submission_id, criterion)
);
