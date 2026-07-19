"""Countdown timer with an injectable clock so pause/resume math is testable.

duration=None means untimed (rungs 4-7). remaining() returns None when untimed.
"""
from __future__ import annotations

import time
from typing import Callable, Optional


class Timer:
    def __init__(self, duration: Optional[float], now: Callable[[], float] = time.monotonic):
        self.duration = duration
        self._now = now
        self._accumulated = 0.0        # seconds elapsed while running, frozen at pauses
        self._run_start: Optional[float] = None
        self._stopped = False

    def start(self, delay: float = 0.0) -> None:
        """Begin the countdown. delay defers the actual start (e.g. while the
        question fades in); remaining() holds at full duration until then."""
        self._accumulated = 0.0
        self._run_start = self._now() + delay
        self._stopped = False

    @property
    def running(self) -> bool:
        return self._run_start is not None and not self._stopped

    def elapsed(self) -> float:
        e = self._accumulated
        if self.running:
            # max() so a pending start delay does not count as negative elapsed.
            e += max(0.0, self._now() - self._run_start)
        return e

    def pause(self) -> None:
        if self.running:
            self._accumulated += max(0.0, self._now() - self._run_start)
            self._run_start = None

    def delay_remaining(self) -> float:
        """Seconds until a delayed start actually begins ticking (0 if started)."""
        if self._run_start is None or self._stopped:
            return 0.0
        return max(0.0, self._run_start - self._now())

    def resume(self) -> None:
        if not self._stopped and self._run_start is None:
            self._run_start = self._now()

    def force_stop(self) -> None:
        self.pause()
        self._stopped = True

    def remaining(self) -> Optional[float]:
        if self.duration is None:
            return None
        return max(0.0, self.duration - self.elapsed())

    def is_expired(self) -> bool:
        r = self.remaining()
        return r is not None and r <= 0.0
