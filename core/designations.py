"""Rung to HR designation mapping and the single safe-haven floor at rung 5."""

DESIGNATIONS = {
    1: "HR Intern",
    2: "HR Assistant",
    3: "HR Generalist",
    4: "HR Business Partner",
    5: "HR Manager",       # safe haven floor
    6: "HR Director",
    7: "CHRO",
}

SAFE_HAVEN_RUNG = 5
TIMED_RUNGS = (1, 2, 3)
TIMER_SECONDS = 60


def title(rung: int) -> str:
    return DESIGNATIONS.get(rung, "No designation")


def apply_safe_haven(banked_rung: int) -> int:
    """Award rung. Once the safe haven is cleared, cannot fall below it."""
    if banked_rung >= SAFE_HAVEN_RUNG:
        return max(banked_rung, SAFE_HAVEN_RUNG)
    return banked_rung


def is_timed(rung: int) -> bool:
    return rung in TIMED_RUNGS
