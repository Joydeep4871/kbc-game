"""State machine for a single run. No UI, no wall-clock assumptions in logic."""
from __future__ import annotations

import random
import time
from typing import Callable, Optional

from . import designations, lifelines
from .explain import explanation_card
from .models import GameState, Question
from .timer import Timer


class GameEngine:
    def __init__(
        self,
        round_questions: list[Question],
        seed: int = 0,
        now: Callable[[], float] = time.monotonic,
    ):
        if len(round_questions) != 7:
            raise ValueError("A round must have exactly 7 questions")
        self.state = GameState(round=round_questions)
        self._rng = random.Random(seed)
        self._now = now
        self.timer: Optional[Timer] = None

    # --- round flow ---------------------------------------------------------
    def start_round(self) -> None:
        """Present the current question and start its timer if the rung is timed."""
        s = self.state
        s.selected_index = None
        s.locked = False
        s.revealed = False
        s.last_correct = None
        s.removed_options = []
        s.consulting = None
        duration = designations.TIMER_SECONDS if designations.is_timed(s.current_rung) else None
        self.timer = Timer(duration, now=self._now)
        self.timer.start()

    def select(self, index: int) -> None:
        s = self.state
        if s.revealed or s.locked or index in s.removed_options:
            return
        s.selected_index = index
        # Committing an answer stops the clock, like locking in a final answer.
        if self.timer:
            self.timer.pause()

    def lock(self) -> None:
        """Final-answer lock. Freezes the answer and pauses the timer for the reveal beat."""
        if self.state.selected_index is not None and not self.state.revealed:
            self.state.locked = True
            if self.timer:
                self.timer.pause()

    # --- lifelines ----------------------------------------------------------
    def apply_lifeline(self, name: str) -> None:
        s = self.state
        if name in s.used_lifelines or s.revealed:
            return
        if name == lifelines.FIFTY_FIFTY:
            s.removed_options = lifelines.fifty_fifty(s.current_question, self._rng)
            if s.selected_index in s.removed_options:
                s.selected_index = None
        elif name in (lifelines.PHONE_A_FRIEND, lifelines.EXPERT_ADVICE):
            # No computation. Just pause the timer and open the consult panel.
            s.consulting = name
            if self.timer:
                self.timer.pause()
        else:
            raise ValueError(f"Unknown lifeline: {name}")
        s.used_lifelines.add(name)

    def close_consult(self) -> None:
        self.state.consulting = None
        if self.timer:
            self.timer.resume()

    # --- reveal / outcome ---------------------------------------------------
    def reveal(self, forced: Optional[bool] = None) -> None:
        """Resolve the current question. forced overrides the selection (host)."""
        s = self.state
        if s.revealed:
            return
        if self.timer:
            self.timer.force_stop()
        if forced is None:
            correct = s.selected_index == s.current_question.correct_index
        else:
            correct = forced
        s.last_correct = correct
        s.revealed = True
        if correct:
            s.banked_rung = s.current_rung
            if s.current_rung == 7:
                s.status = "won"
                s.final_rung = 7
        else:
            self._end_lost()

    def force_correct(self) -> None:
        self.reveal(forced=True)

    def force_wrong(self) -> None:
        self.reveal(forced=False)

    def timeout(self) -> None:
        """Timed-question timeout: treated as wrong. Host may still force_correct."""
        self.reveal(forced=False)

    def _end_lost(self) -> None:
        s = self.state
        s.status = "lost"
        # Linear: the contestant keeps the highest rung they actually banked.
        # No safe-haven floor, per the revised brief.
        s.final_rung = s.banked_rung

    def advance(self) -> None:
        """Move to the next rung after a correct reveal. No-op if run is over."""
        s = self.state
        if s.status != "running" or not s.revealed or not s.last_correct:
            return
        if s.current_rung >= 7:
            return
        s.current_rung += 1
        self.start_round()

    # --- read helpers -------------------------------------------------------
    def explanation(self) -> dict:
        return explanation_card(self.state.current_question)

    def final_designation(self) -> str:
        return designations.title(self.state.final_rung)
