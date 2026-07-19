"""Pytest coverage for the required core behaviors. No UI, no real wall clock."""
from pathlib import Path

import pytest

from core import designations, lifelines
from core.game_engine import GameEngine
from core.question_bank import draw_round, load_bank

BANK_PATH = Path(__file__).resolve().parents[1] / "data" / "question_bank.json"


@pytest.fixture
def bank():
    return load_bank(BANK_PATH)


class FakeClock:
    """Manually advanced clock for deterministic timer math."""
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def tick(self, seconds):
        self.t += seconds


def _round(bank, seed=1):
    return draw_round(bank, seed)


# 1. Engine round progression -------------------------------------------------
def test_round_progression_to_chro(bank):
    eng = GameEngine(_round(bank), seed=0)
    eng.start_round()
    for rung in range(1, 8):
        assert eng.state.current_rung == rung
        q = eng.state.current_question
        eng.select(q.correct_index)
        eng.lock()
        eng.reveal()
        assert eng.state.last_correct is True
        assert eng.state.banked_rung == rung
        eng.advance()
    assert eng.state.status == "won"
    assert eng.final_designation() == "CHRO"


# 2. 50-50 removes exactly two wrong options ----------------------------------
def test_fifty_fifty_removes_two_wrong(bank):
    eng = GameEngine(_round(bank), seed=0)
    eng.start_round()
    q = eng.state.current_question
    eng.apply_lifeline(lifelines.FIFTY_FIFTY)
    removed = eng.state.removed_options
    assert len(removed) == 2
    assert q.correct_index not in removed
    remaining = [i for i in range(len(q.options)) if i not in removed]
    assert len(remaining) == 2
    assert q.correct_index in remaining
    assert lifelines.FIFTY_FIFTY in eng.state.used_lifelines


# 3. Safe-haven floor at rung 5 -----------------------------------------------
def test_safe_haven_floor_holds(bank):
    # Clear rungs 1..5, then fail rung 6 -> keep HR Manager (rung 5).
    eng = GameEngine(_round(bank), seed=0)
    eng.start_round()
    for _ in range(5):
        eng.select(eng.state.current_question.correct_index)
        eng.reveal()
        eng.advance()
    assert eng.state.current_rung == 6
    eng.force_wrong()
    assert eng.state.status == "lost"
    assert eng.state.final_rung == 5
    assert eng.final_designation() == "HR Manager"


def test_below_safe_haven_no_floor(bank):
    # Fail rung 3 with only rungs 1-2 banked -> HR Assistant, no floor applied.
    eng = GameEngine(_round(bank), seed=0)
    eng.start_round()
    for _ in range(2):
        eng.select(eng.state.current_question.correct_index)
        eng.reveal()
        eng.advance()
    eng.force_wrong()
    assert eng.state.final_rung == 2
    assert eng.final_designation() == "HR Assistant"


# 4. Timer pause/resume math --------------------------------------------------
def test_timer_pause_resume_math(bank):
    from core.timer import Timer
    clock = FakeClock()
    t = Timer(60, now=clock)
    t.start()
    clock.tick(10)
    assert t.remaining() == pytest.approx(50)
    t.pause()
    clock.tick(100)              # time passes while paused, no drain
    assert t.remaining() == pytest.approx(50)
    t.resume()
    clock.tick(20)
    assert t.remaining() == pytest.approx(30)
    clock.tick(40)              # runs past zero, floors at 0
    assert t.remaining() == 0
    assert t.is_expired()


def test_timed_rungs_only_first_three(bank):
    clock = FakeClock()
    eng = GameEngine(_round(bank), seed=0, now=clock)
    eng.start_round()
    assert eng.timer.remaining() == pytest.approx(60)   # rung 1 timed
    eng.select(eng.state.current_question.correct_index)
    eng.reveal(); eng.advance()  # rung 2
    eng.select(eng.state.current_question.correct_index)
    eng.reveal(); eng.advance()  # rung 3
    eng.select(eng.state.current_question.correct_index)
    eng.reveal(); eng.advance()  # rung 4
    assert eng.state.current_rung == 4
    assert eng.timer.remaining() is None                 # rung 4 untimed


# 5. Rotation uniqueness ------------------------------------------------------
def test_rotation_two_seeds_differ(bank):
    r1 = [q.id for q in draw_round(bank, seed=1)]
    r2 = [q.id for q in draw_round(bank, seed=2)]
    assert r1 != r2
    # Same seed is deterministic.
    assert r1 == [q.id for q in draw_round(bank, seed=1)]


def test_round_is_one_per_ascending_tier(bank):
    r = draw_round(bank, seed=7)
    assert [q.difficulty for q in r] == [1, 2, 3, 4, 5, 6, 7]
