"""Load the local bank and draw one question per difficulty tier (rotated by seed)."""
from __future__ import annotations

import json
import random
import time
from dataclasses import replace
from pathlib import Path
from typing import Optional

from .models import Question

TIERS = range(1, 8)  # 1..7


def _shuffle_options(q: Question, rng: random.Random) -> Question:
    """Return a copy with options shuffled and correct_index remapped, so the
    correct answer is not always in the same slot. The bank authors every
    question with the answer first; this spreads it across A/B/C/D."""
    order = list(range(len(q.options)))
    rng.shuffle(order)
    return replace(
        q,
        options=[q.options[i] for i in order],
        correct_index=order.index(q.correct_index),
    )


def load_bank(path: str | Path) -> list[Question]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Question.from_dict(q) for q in data["questions"]]


def seed_for(contestant_id: str, timestamp: Optional[float] = None, counter: int = 0) -> int:
    """Seed on contestant id + timestamp + counter so no two rounds collide."""
    if timestamp is None:
        timestamp = time.time()
    return hash((contestant_id, round(timestamp, 6), counter)) & 0x7FFFFFFF


def draw_round(bank: list[Question], seed, contestant_id: Optional[str] = None) -> list[Question]:
    """One question per tier (1..7), ascending difficulty. Deterministic per seed."""
    if contestant_id is not None:
        seed = hash((seed, contestant_id)) & 0x7FFFFFFF
    rng = random.Random(seed)
    drawn: list[Question] = []
    for tier in TIERS:
        pool = [q for q in bank if q.difficulty == tier]
        if not pool:
            raise ValueError(f"Question bank has no question for difficulty tier {tier}")
        drawn.append(rng.choice(pool))
    # Shuffle after all picks so the id-selection stream (and rotation) is
    # unchanged; only the option order within each question varies.
    return [_shuffle_options(q, rng) for q in drawn]
