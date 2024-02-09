from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    UPDATE = 12
    NEWS = 13
    SPECIAL = 14
    EVENTS = 28


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
    def posttime_as_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.posttime)

    def to_dict(self) -> dict:
        return asdict(self)

    def is_update(self) -> bool:
        return EventType(self.event_type) == EventType.UPDATE

    def is_news(self) -> bool:
        return EventType(self.event_type) == EventType.NEWS

    def is_special(self) -> bool:
        return EventType(self.event_type) == EventType.SPECIAL

    def is_event(self) -> bool:
        return EventType(self.event_type) == EventType.EVENTS

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.to_dict() == other.to_dict()
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
