# quiz_loader.py
"""Parse the course's existing MCQ item banks (instructor/quizzes/weekly/item-bank.md,
instructor/quizzes/review-quiz-item-bank.md) into {topic: [question, ...]}.

Same source format and parsing rules as instructor/quizzes/kahoot/make_kahoot_import.py's
parse_file() -- a "## <topic>" header line, then question lines shaped
"N. <stem> a) opt · b) opt ✓ · c) opt · d) opt", options separated
by " · " and the correct one marked with "✓". Output shape differs from the Kahoot
exporter in three ways: (1) 0-based `correct` index, not 1-based; (2) grouped by topic, not a
flat row list, since the game picks one topic per session rather than importing everything at
once; (3) topic keys are the raw "## <heading>" text with NO source-file tag prefix (the Kahoot
exporter prefixes with "weekly:"/"review:" specifically to keep the two files' topics from
colliding in one flat list -- this loader intentionally drops that prefix). If
weekly/item-bank.md and review-quiz-item-bank.md ever use an identical heading, their questions
would merge into one topic; verified harmless against the files as of 2026-07 (no heading
collisions) -- revisit only if that changes.
"""
import re

_bold = re.compile(r"\*\*(.+?)\*\*")
_optsplit = re.compile(r"\s+·\s+")
_optlead = re.compile(r"^[a-d]\)\s*", re.I)


def _clean(s):
    return _bold.sub(r"\1", s).strip()


def parse_topics(path):
    with open(path, encoding="utf-8") as f:
        return parse_topics_from_text(f.read())


def parse_topics_from_text(text):
    topics = {}
    topic = "?"
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        h = re.match(r"^##\s+(.*)", line)
        if h:
            topic = h.group(1).strip()
            continue
        if not re.match(r"^\d+\.\s", line) or "✓" not in line:
            continue
        m = re.search(r"\ba\)\s", line)
        if not m:
            continue
        stem = re.sub(r"^\d+\.\s*", "", line[: m.start()]).strip().rstrip("·").strip()
        opts, correct = [], None
        for piece in _optsplit.split(line[m.start() :]):
            piece = _optlead.sub("", piece).strip()
            if "✓" in piece:
                correct = len(opts)  # 0-based
                piece = piece.replace("✓", "").strip()
            opts.append(_clean(piece))
        opts = [o for o in opts if o]
        if correct is None or len(opts) < 2:
            continue
        topics.setdefault(topic, []).append(
            {"stem": _clean(stem), "options": opts[:4], "correct": correct}
        )
    return topics


def load_all_topics(paths):
    merged = {}
    for path in paths:
        for topic, questions in parse_topics(path).items():
            merged.setdefault(topic, []).extend(questions)
    return merged
