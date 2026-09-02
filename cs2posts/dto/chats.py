from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import ClassVar

from cs2posts.clock import UTC
from cs2posts.dto.post import PostType

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _as_utc(value: datetime) -> datetime:
    """Normalise to an aware UTC datetime.

    Rows written before the bot used aware datetimes hold naive ISO strings;
    they were always UTC, so attach the zone rather than reject them.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass
class Chat:
    chat_id: int
    chat_id_admin: int = 0
    strikes: int = 0
    is_running: bool = False
    is_banned: bool = False
    is_removed_while_banned: bool = False
    is_news_interested: bool = True
    is_update_interested: bool = True
    is_external_news_interested: bool = True
    last_activity: datetime = field(default=EPOCH)

    # The persisted column backing each interest. Keeping the three columns
    # (rather than one) preserves the existing schema for deployed databases,
    # while the accessors below let callers stay PostType-driven.
    INTEREST_ATTRIBUTE: ClassVar[dict[PostType, str]] = {
        PostType.NEWS: "is_news_interested",
        PostType.UPDATE: "is_update_interested",
        PostType.EXTERNAL: "is_external_news_interested",
    }

    def __post_init__(self) -> None:
        self.last_activity = _as_utc(self.last_activity)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chat:
        data = dict(data)
        last_activity = data.pop("last_activity")
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        return cls(**data, last_activity=last_activity)

    def is_interested_in(self, post_type: PostType) -> bool:
        return bool(getattr(self, self.INTEREST_ATTRIBUTE[post_type]))

    def set_interest(self, post_type: PostType, interested: bool) -> None:
        setattr(self, self.INTEREST_ATTRIBUTE[post_type], interested)

    def toggle_interest(self, post_type: PostType) -> bool:
        interested = not self.is_interested_in(post_type)
        self.set_interest(post_type, interested)
        return interested
