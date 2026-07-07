# tests/test_scoring.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scoring import score_answer


def test_wrong_answer_scores_zero():
    assert score_answer(correct=False, time_taken=0.1, time_limit=20) == 0


def test_wrong_answer_scores_zero_even_if_instant():
    assert score_answer(correct=False, time_taken=0, time_limit=20) == 0


def test_instant_correct_answer_scores_full_points():
    assert score_answer(correct=True, time_taken=0, time_limit=20) == 1000


def test_correct_answer_at_time_limit_scores_half_points():
    assert score_answer(correct=True, time_taken=20, time_limit=20) == 500


def test_correct_answer_halfway_through_scores_three_quarters():
    # time_taken = time_limit/2 -> 1 - (0.5/2) = 0.75 -> 750
    assert score_answer(correct=True, time_taken=10, time_limit=20) == 750


def test_time_taken_beyond_limit_is_clamped_to_half_points():
    # a late/out-of-order submission should never score below the time-limit floor
    assert score_answer(correct=True, time_taken=999, time_limit=20) == 500


def test_negative_time_taken_is_clamped_to_full_points():
    # defensive clamp in case of clock skew
    assert score_answer(correct=True, time_taken=-1, time_limit=20) == 1000


def test_custom_base_points():
    assert score_answer(correct=True, time_taken=0, time_limit=20, base_points=500) == 500
