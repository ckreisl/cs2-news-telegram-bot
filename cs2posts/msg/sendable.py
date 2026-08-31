from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any
from typing import Protocol
from typing import runtime_checkable

from cs2posts.msg.constants import TELEGRAM_SEND_DELAY_SECONDS


@runtime_checkable
class Sendable(Protocol):
    """Something the bot can deliver to a chat.

    This, not ``TelegramMessage``, is what the bot depends on. Keeping the
    contract separate from the chunked-text implementation means a message
    type that renders media does not have to inherit -- and then fail to
    honour -- a text-shaped base class.

    Runtime-checkable so tests can assert conformance directly.
    """

    async def send(self, bot: Any, chat_id: int) -> None: ...


async def send_in_sequence[T](
    items: Sequence[T],
    send: Callable[[T], Awaitable[None]],
    delay: float = TELEGRAM_SEND_DELAY_SECONDS,
) -> None:
    """Send ``items`` in order, pausing between them but not after the last.

    Telegram rate-limits bursts; the pause used to be re-implemented at every
    call site that sends more than one thing.
    """
    last = len(items) - 1
    for index, item in enumerate(items):
        await send(item)
        if index < last:
            await asyncio.sleep(delay)
