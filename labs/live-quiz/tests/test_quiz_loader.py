import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from quiz_loader import parse_topics, load_all_topics

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample-item-bank.md")


def test_parses_two_topics():
    topics = parse_topics(FIXTURE)
    assert set(topics.keys()) == {"Week 1: Threat Modeling", "Week 4: Injection"}


def test_topic_has_correct_question_count():
    topics = parse_topics(FIXTURE)
    assert len(topics["Week 1: Threat Modeling"]) == 2
    assert len(topics["Week 4: Injection"]) == 1


def test_question_shape():
    topics = parse_topics(FIXTURE)
    q = topics["Week 4: Injection"][0]
    assert q["stem"] == "What makes SQL injection possible?"
    assert q["options"] == [
        "Weak passwords",
        "Unparameterized queries with user input",
        "Missing HTTPS",
        "Slow queries",
    ]
    assert q["correct"] == 1  # 0-based index of the "b)" option


def test_correct_index_is_zero_based_for_first_option():
    topics = parse_topics(FIXTURE)
    q = topics["Week 1: Threat Modeling"][1]  # "trust boundary" question, ✓ on b)
    assert q["correct"] == 1


def test_load_all_topics_merges_multiple_files(tmp_path):
    second_file = tmp_path / "extra.md"
    second_file.write_text(
        "## Week 4: Injection\n"
        "2. What is a prepared statement? a) A stored procedure · "
        "b) A query template with bound parameters ✓ · c) A view · d) A trigger\n"
    )
    merged = load_all_topics([FIXTURE, str(second_file)])
    assert len(merged["Week 4: Injection"]) == 2  # 1 from FIXTURE + 1 from second_file


def test_parse_topics_from_text_matches_file(tmp_path):
    import quiz_loader
    md = "## Week 1\n1. Q? a) x ✓ · b) y · c) z · d) w\n"
    p = tmp_path / "s.md"; p.write_text(md, encoding="utf-8")
    assert quiz_loader.parse_topics_from_text(md) == quiz_loader.parse_topics(str(p))


def test_parse_topics_from_text_shape():
    import quiz_loader
    t = quiz_loader.parse_topics_from_text("## T\n1. Q? a) A ✓ · b) B · c) C · d) D\n")
    assert list(t) == ["T"]
    assert t["T"][0]["correct"] == 0 and t["T"][0]["options"][0] == "A"
