from __future__ import annotations

import asyncio

from .cs_external_msg import CounterStrikeExternalMessage
from .cs_news_msg import CounterStrikeNewsMessage
from .cs_update_msg import CounterStrikeUpdateMessage
from .telegram import TelegramMessage
from cs2posts.dto.post import Post


async def create_message(post: Post) -> TelegramMessage:
    # Building a message resolves redirect URLs (blocking HTTP) and runs the
    # bbcode/HTML parsers, so do it in a worker thread to avoid blocking the
    # asyncio event loop.
    return await asyncio.to_thread(build_message, post)


def build_message(post: Post) -> TelegramMessage:
    if post.is_news():
        return CounterStrikeNewsMessage(post)
    if post.is_update():
        return CounterStrikeUpdateMessage(post)
    if post.is_external():
        return CounterStrikeExternalMessage(post)
    raise ValueError(f"Unknown post type {post.title=} {post.url=}")
