# scoring.py
"""Kahoot-style speed+accuracy scoring: wrong answers always score 0 (no penalty
beyond forfeiting the round); correct answers score between 50% and 100% of
base_points depending on how quickly they were submitted."""


def score_answer(correct, time_taken, time_limit, base_points=1000):
    if not correct:
        return 0
    if time_taken < 0:
        time_taken = 0
    if time_taken > time_limit:
        time_taken = time_limit
    return round(base_points * (1 - (time_taken / time_limit) / 2))
