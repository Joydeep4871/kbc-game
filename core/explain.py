"""Explanation card payload shown after every reveal. Never skipped."""
from __future__ import annotations

from .models import Question


def explanation_card(question: Question) -> dict:
    return {
        "correct_option": question.options[question.correct_index],
        "why": question.explanation,
        "code": question.code,
        "library": question.library,
    }
