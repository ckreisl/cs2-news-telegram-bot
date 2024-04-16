from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from zoneinfo import ZoneInfo


class EventType(Enum):
    UPDATE = 12
    NEWS = 13
    SPECIAL = 14
    EVENTS = 28
    NOT_DEFINED = -1

    @classmethod
    def _missing_(cls, value: object) -> Any:
        return cls.NOT_DEFINED


@dataclass
class Post:
    gid: str
    posterid: str
    headline: str
    posttime: int
    updatetime: int
    body: str
    event_type: int

    @property
    def posttime_as_datetime(self, tz: ZoneInfo = ZoneInfo('UTC')) -> datetime:
        # Do not return a timezone-aware datetime object
        return datetime.fromtimestamp(self.posttime, tz=tz).replace(tzinfo=None)

    def to_dict(self) -> dict:
        return asdict(self)

    def is_update(self) -> bool:
        return EventType(self.event_type) == EventType.UPDATE

    def is_news(self) -> bool:
        return ((EventType(self.event_type) == EventType.NEWS) or  # noqa
                (EventType(self.event_type) == EventType.SPECIAL) or  # noqa
                (EventType(self.event_type) == EventType.EVENTS))

    def is_newer_than(self, other: Post) -> bool:
        if other is None:
            return False
        return self.posttime > other.posttime

    def is_older_eq_than(self, other: Post) -> bool:
        if other is None:
            return False
        return self.posttime <= other.posttime

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.to_dict() == other.to_dict()
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
