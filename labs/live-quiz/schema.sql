-- schema.sql — live-quiz platform tables. Applied idempotently at startup (db.init_db).
CREATE TABLE IF NOT EXISTS teachers (
  id            INTEGER PRIMARY KEY,
  username      TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS question_sets (
  id          INTEGER PRIMARY KEY,
  -- Which course this belongs to. A STRING, not a foreign key: courses are
  -- configured in the content registry ($COURSES / the curriculum monorepo),
  -- not stored here, so a `courses` table would be a second source of truth.
  -- Validated at the write boundary by course_scope.check().
  course_slug  TEXT,
  teacher_id  INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  source_md   TEXT NOT NULL,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sets_teacher ON question_sets(teacher_id);
