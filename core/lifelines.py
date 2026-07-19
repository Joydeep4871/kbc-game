"""Lifeline logic. Only 50-50 computes; phone/expert are pause-only flags."""
from __future__ import annotations

import random

from .models import Question

FIFTY_FIFTY = "50-50"
PHONE_A_FRIEND = "phone"
EXPERT_ADVICE = "expert"
ALL_LIFELINES = (FIFTY_FIFTY, PHONE_A_FRIEND, EXPERT_ADVICE)


def fifty_fifty(question: Question, rng: random.Random) -> list[int]:
    """Return the indices to hide: two wrong options, leaving correct + one decoy."""
    wrong = [i for i in range(len(question.options)) if i != question.correct_index]
    keep_decoy = rng.choice(wrong)
    removed = [i for i in wrong if i != keep_decoy]
    # For the four-option bank this is always exactly two removals.
    return sorted(removed[:2])
