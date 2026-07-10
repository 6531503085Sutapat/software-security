# game.py
"""In-memory game state for one live-quiz session. No database: a game is short-lived
(one class period) and this project's expected scale (dozens-to-~200 concurrent players)
doesn't need persistence beyond the end-of-game CSV export (see export_results)."""
import random
import string
import time

from scoring import score_answer

TIME_LIMIT = 20  # seconds per question; matches make_kahoot_import.py's TIME_LIMIT constant


def generate_pin():
    return "".join(random.choices(string.digits, k=6))


class Player:
    def __init__(self, nickname):
        self.nickname = nickname
        self.score = 0
        self.correct_count = 0
        self.response_times_ms = []
        self.connected = True


class GameSession:
    def __init__(self, pin, questions, time_limit=TIME_LIMIT):
        self.pin = pin
        self.questions = questions
        self.time_limit = time_limit
        self.current_index = -1
        self.players = {}
        self.question_start_time = None
        self.answers_this_round = {}
        self.finished = False

    def join(self, nickname):
        if nickname not in self.players:
            self.players[nickname] = Player(nickname)
        else:
            self.players[nickname].connected = True
        return self.players[nickname]

    def disconnect(self, nickname):
        if nickname in self.players:
            self.players[nickname].connected = False

    def current_question(self):
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def next_question(self):
        self.current_index += 1
        self.answers_this_round = {}
        self.question_start_time = time.time()
        self._revealed_this_round = False
        if self.current_index >= len(self.questions):
            self.finished = True
            return None
        return self.current_question()

    def submit_answer(self, nickname, choice_index):
        if nickname not in self.players:
            raise ValueError(f"unknown player: {nickname}")
        if nickname in self.answers_this_round:
            return None
        q = self.current_question()
        if q is None:
            raise ValueError("no active question")
        time_taken = time.time() - self.question_start_time
        correct = choice_index == q["correct"]
        points = score_answer(correct, time_taken, self.time_limit)
        self.answers_this_round[nickname] = (choice_index, time_taken)
        player = self.players[nickname]
        player.score += points
        if correct:
            player.correct_count += 1
        player.response_times_ms.append(time_taken * 1000)
        return {"correct": correct, "points": points}

    def all_answered(self):
        connected = [n for n, p in self.players.items() if p.connected]
        return len(connected) > 0 and all(n in self.answers_this_round for n in connected)

    def answer_distribution(self):
        q = self.current_question()
        counts = [0] * len(q["options"])
        for choice_index, _ in self.answers_this_round.values():
            if 0 <= choice_index < len(counts):
                counts[choice_index] += 1
        return counts

    def leaderboard(self, top_n=5):
        ranked = sorted(self.players.values(), key=lambda p: -p.score)
        return [{"nickname": p.nickname, "score": p.score} for p in ranked[:top_n]]

    def rank_of(self, nickname):
        ranked = sorted(self.players.values(), key=lambda p: -p.score)
        for i, p in enumerate(ranked):
            if p.nickname == nickname:
                return i + 1
        return None

    def export_results(self):
        rows = []
        for p in self.players.values():
            avg_ms = sum(p.response_times_ms) / len(p.response_times_ms) if p.response_times_ms else 0
            rows.append(
                {
                    "nickname": _csv_safe(p.nickname),
                    "total_score": p.score,
                    "correct_count": p.correct_count,
                    "avg_response_time_ms": round(avg_ms),
                }
            )
        return rows


def _csv_safe(value):
    """Neutralize spreadsheet formula injection (CWE-1236): a nickname starting with =, +, -, @
    (or a control prefix) would run as a formula when the exported CSV is opened directly in
    Excel/Sheets. Prefixing a single quote makes the cell render as literal text."""
    if value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value
