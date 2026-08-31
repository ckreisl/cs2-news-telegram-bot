from __future__ import annotations

from datetime import UTC
from datetime import datetime
from typing import Protocol

UTC = UTC


class Clock(Protocol):
    """The current time, as a dependency.

    Injecting the clock keeps time-dependent behaviour (spam windows, ban
    timeouts) testable without patching private methods or freezing globals.
    """

    def now(self) -> datetime: ...


class SystemClock:
    """The real wall clock, in UTC."""

    def now(self) -> datetime:
        return datetime.now(tz=UTC)


class FrozenClock:
    """A clock that only moves when a test moves it."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self._now += timedelta(seconds=seconds)
