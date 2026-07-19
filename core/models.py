"""Data models for the game. Pure dataclasses, no behavior beyond parsing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Question:
    id: str
    library: str
    difficulty: int
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    code: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "Question":
        return cls(
            id=d["id"],
            library=d["library"],
            difficulty=int(d["difficulty"]),
            question=d["question"],
            options=list(d["options"]),
            correct_index=int(d["correct_index"]),
            explanation=d["explanation"],
            code=d.get("code"),
        )


@dataclass
class GameState:
    """Mutable run state. The engine owns the transitions; this just holds them."""
    round: list[Question]
    current_rung: int = 1            # 1..7
    banked_rung: int = 0             # highest rung answered correctly (0 = none)
    selected_index: Optional[int] = None
    locked: bool = False             # "Lock kiya jaye" confirmed
    revealed: bool = False
    last_correct: Optional[bool] = None
    removed_options: list[int] = field(default_factory=list)  # hidden by 50-50
    used_lifelines: set[str] = field(default_factory=set)
    consulting: Optional[str] = None  # "phone" | "expert" while panel open
    status: str = "running"          # "running" | "won" | "lost"
    final_rung: int = 0              # designation rung awarded at end

    @property
    def current_question(self) -> Question:
        return self.round[self.current_rung - 1]
