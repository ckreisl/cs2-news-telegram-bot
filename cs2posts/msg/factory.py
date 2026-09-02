from __future__ import annotations

import asyncio
from collections.abc import Callable

from cs2posts.dto.post import Post
from cs2posts.dto.post import PostType
from cs2posts.exceptions import UnsupportedPostError
from .cs_external_msg import CounterStrikeExternalMessage
from .cs_news_msg import CounterStrikeNewsMessage
from .cs_update_msg import CounterStrikeUpdateMessage
from .sendable import Sendable

MESSAGE_BY_POST_TYPE: dict[PostType, Callable[[Post], Sendable]] = {
    PostType.NEWS: CounterStrikeNewsMessage,
    PostType.UPDATE: CounterStrikeUpdateMessage,
    PostType.EXTERNAL: CounterStrikeExternalMessage,
}


def build_message(post: Post) -> Sendable:
    try:
        message_class = MESSAGE_BY_POST_TYPE[post.type]
    except KeyError as exc:  # pragma: no cover - PostType is exhaustive
        raise UnsupportedPostError(
            f"No message renderer for {post.type} ({post.title!r})"
        ) from exc
    return message_class(post)


async def create_message(post: Post) -> Sendable:
    """Render ``post`` off the event loop.

    Building a message resolves redirect URLs (blocking HTTP) and runs the
    bbcode/HTML parsers, so it runs in a worker thread.
    """
    return await asyncio.to_thread(build_message, post)
