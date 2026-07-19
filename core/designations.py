"""Rung to HR designation mapping.

Linear progression only. The earlier "safe haven" floor at rung 5 has been
removed per the revised brief: a wrong answer ends the run at the highest rung
the contestant actually banked, with no floor.
"""

DESIGNATIONS = {
    1: "HR Intern",
    2: "HR Assistant",
    3: "HR Generalist",
    4: "HR Business Partner",
    5: "HR Manager",
    6: "HR Director",
    7: "CHRO",
}

TIMED_RUNGS = (1, 2, 3)
TIMER_SECONDS = 60


def title(rung: int) -> str:
    return DESIGNATIONS.get(rung, "No designation")


def is_timed(rung: int) -> bool:
    return rung in TIMED_RUNGS
