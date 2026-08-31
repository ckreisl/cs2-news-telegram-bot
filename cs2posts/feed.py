from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from cs2posts.dto.post import FeedType
from cs2posts.dto.post import Post
from cs2posts.dto.post import PostType

logger = logging.getLogger(__name__)

# 2023-03-22, the day Counter-Strike 2 was announced. Posts older than this
# belong to CS:GO and are never republished.
CS2_ANNOUNCEMENT_EPOCH = 1679503828

SUPPORTED_FEED_TYPES = (FeedType.INTERN, FeedType.EXTERN)


def _newsitems(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    appnews = payload.get("appnews")
    if not isinstance(appnews, dict):
        return
    newsitems = appnews.get("newsitems")
    if not isinstance(newsitems, list):
        return
    for item in newsitems:
        if isinstance(item, dict):
            yield item


class PostFeed:
    """The posts from one Steam news response, newest first.

    Parsing lives in :meth:`from_api_response` rather than in ``__init__`` so
    that the constructor cannot silently yield an empty feed, and so tests can
    build a feed from ``Post`` objects directly.
    """

    def __init__(self, posts: list[Post]) -> None:
        self._posts = sorted(posts, key=lambda post: post.date, reverse=True)

    @classmethod
    def from_api_response(cls, payload: dict[str, Any] | None) -> PostFeed:
        if not payload:
            return cls([])

        posts = []
        for item in _newsitems(payload):
            feed_type = FeedType(item["feed_type"])
            if feed_type not in SUPPORTED_FEED_TYPES:
                logger.info(
                    "Ignoring feed %s headline=%r url=%s feed_type=%s",
                    item["gid"],
                    item["title"],
                    item["url"],
                    feed_type,
                )
                continue
            posts.append(Post.from_dict(item))

        return cls(posts)

    @property
    def posts(self) -> list[Post]:
        return list(self._posts)

    def of_type(self, post_type: PostType) -> list[Post]:
        """Posts of one kind, newest first, excluding the CS:GO back catalogue."""
        return [
            post
            for post in self._posts
            if post.date >= CS2_ANNOUNCEMENT_EPOCH and post.type is post_type
        ]

    def latest(self, post_type: PostType | None = None) -> Post | None:
        """The newest post, optionally of one kind.

        Replaces the eight ``latest_*``/``oldest_*`` properties this class
        used to expose, one per post type.
        """
        candidates = self._posts if post_type is None else self.of_type(post_type)
        return candidates[0] if candidates else None

    def is_empty(self) -> bool:
        return not self._posts

    def __len__(self) -> int:
        return len(self._posts)

    def __iter__(self) -> Iterator[Post]:
        return iter(self._posts)
