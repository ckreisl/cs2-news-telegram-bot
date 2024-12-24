from __future__ import annotations

from .cs_external_msg import CounterStrikeExternalMessage
from .cs_news_msg import CounterStrikeNewsMessage
from .cs_update_msg import CounterStrikeUpdateMessage
from .telegram import TelegramMessage
from cs2posts.dto.post import Post


class TelegramMessageFactory:

    @staticmethod
    async def create(post: Post) -> TelegramMessage:
        if post.is_news():
            return CounterStrikeNewsMessage(post)
        if post.is_update():
            return CounterStrikeUpdateMessage(post)
        if post.is_external():
            return CounterStrikeExternalMessage(post)
        raise ValueError(f"Unknown post type {post.title=} {post.url=}")
