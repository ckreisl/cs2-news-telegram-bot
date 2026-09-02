from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from datetime import datetime
from enum import Enum
from typing import Any

from cs2posts.clock import UTC


class PostType(Enum):
    """The three kinds of post the bot distinguishes.

    Every post is exactly one of these (``is_news`` is defined as the
    complement of the other two), so lookups keyed by ``PostType`` are total
    and need no fallback branch.
    """

    NEWS = "news"
    UPDATE = "update"
    EXTERNAL = "external"

    def __str__(self) -> str:
        return self.value


class FeedType(Enum):
    EXTERN = 0
    INTERN = 1
    NOT_DEFINED = -1

    @classmethod
    def _missing_(cls, value: object) -> FeedType:
        return cls.NOT_DEFINED


@dataclass
class Post:
    gid: str
    title: str
    url: str
    is_external_url: bool
    author: str
    contents: str
    feedlabel: str
    date: int
    feedname: str
    feed_type: int
    appid: int
    # can be empty from crawled data
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, json: dict[str, Any]) -> Post:
        # Ignore unknown keys so new fields added by the Steam API do not
        # break construction.
        field_names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in json.items() if k in field_names})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def date_as_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.date, tz=UTC)

    @property
    def date_display(self) -> str:
        """How a post date is rendered in every outgoing message."""
        return self.date_as_datetime.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def feed_type_enum(self) -> FeedType:
        return FeedType(self.feed_type)

    @property
    def type(self) -> PostType:
        if self.is_update():
            return PostType.UPDATE
        if self.is_external():
            return PostType.EXTERNAL
        return PostType.NEWS

    def is_update(self) -> bool:
        return "patchnotes" in self.tags or "Release Notes" in self.title

    def is_external(self) -> bool:
        return self.feed_type_enum is FeedType.EXTERN

    def is_news(self) -> bool:
        return not self.is_update() and not self.is_external()

    def is_newer_than(self, other: Post) -> bool:
        return self.date > other.date
