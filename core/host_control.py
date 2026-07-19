"""Thin host-override facade over the engine and its timer."""
from __future__ import annotations

from .game_engine import GameEngine


class HostControl:
    def __init__(self, engine: GameEngine):
        self.engine = engine

    def start_round(self) -> None:
        self.engine.start_round()

    def pause_timer(self) -> None:
        if self.engine.timer:
            self.engine.timer.pause()

    def resume_timer(self) -> None:
        if self.engine.timer:
            self.engine.timer.resume()

    def reveal(self) -> None:
        self.engine.reveal()

    def force_correct(self) -> None:
        self.engine.force_correct()

    def force_wrong(self) -> None:
        self.engine.force_wrong()

    def show_explanation(self) -> dict:
        return self.engine.explanation()

    def next_question(self) -> None:
        self.engine.advance()
