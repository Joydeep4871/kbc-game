"""Framework-agnostic view-model builders. Any adapter renders these dicts.

Keeps presentation logic out of the core engine and out of Streamlit, so the
Streamlit adapter and any future adapter share one source of layout truth.
"""
from __future__ import annotations

from core import designations
from core.game_engine import GameEngine
from core.lifelines import ALL_LIFELINES, FIFTY_FIFTY, PHONE_A_FRIEND, EXPERT_ADVICE
from core.models import GameState

LETTERS = ("A", "B", "C", "D")
LIFELINE_LABELS = {
    FIFTY_FIFTY: "50-50",
    PHONE_A_FRIEND: "Phone a Friend",
    EXPERT_ADVICE: "Expert Advice",
}


def ladder_rows(state: GameState) -> list[dict]:
    """Top rung (7) first for a top-down ladder render."""
    rows = []
    for rung in range(7, 0, -1):
        if rung == state.current_rung and state.status == "running":
            row_state = "current"
        elif rung <= state.banked_rung:
            row_state = "done"
        else:
            row_state = "future"
        rows.append({
            "rung": rung,
            "title": designations.title(rung),
            "state": row_state,
            "safe_haven": False,
        })
    return rows


def answer_boxes(state: GameState) -> list[dict]:
    q = state.current_question
    boxes = []
    for i, text in enumerate(q.options):
        if state.revealed and i == q.correct_index:
            box_state = "correct"
        elif state.revealed and i == state.selected_index:
            box_state = "wrong"
        elif i == state.selected_index:
            box_state = "selected"
        else:
            box_state = "default"
        boxes.append({
            "index": i,
            "letter": LETTERS[i],
            "text": text,
            "hidden": i in state.removed_options,
            "box_state": box_state,
        })
    return boxes


def timer_payload(engine: GameEngine) -> dict:
    remaining = engine.timer.remaining() if engine.timer else None
    return {
        "timed": remaining is not None,
        "remaining": remaining,
        "running": bool(engine.timer and engine.timer.running),
    }


def lifeline_states(state: GameState) -> list[dict]:
    return [
        {"name": name, "label": LIFELINE_LABELS[name], "used": name in state.used_lifelines}
        for name in ALL_LIFELINES
    ]
