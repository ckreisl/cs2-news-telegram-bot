from __future__ import annotations

from typing import Any

from telegram.constants import ParseMode

from cs2posts.msg.constants import TELEGRAM_MAX_MESSAGE_LENGTH
from cs2posts.msg.sendable import send_in_sequence


def split_text(message: str, limit: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> list[str]:
    """Split ``message`` into chunks Telegram will accept, preferring line breaks."""
    if len(message) <= limit:
        return [message]

    chunks: list[str] = []
    chunk = ""

    for line in message.split("\n"):
        candidate = f"{chunk}{line}\n"
        if len(candidate) <= limit:
            chunk = candidate
            continue

        if chunk:
            chunks.append(chunk)

        # A single line can itself exceed the limit; hard-split it so we
        # never hand Telegram an over-long message that it would reject.
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]

        chunk = f"{line}\n"

    if chunk:
        chunks.append(chunk)

    return chunks


class TelegramMessage:
    """A plain-text message, split into Telegram-sized chunks."""

    def __init__(self, message: str) -> None:
        self._message = message
        self._messages = split_text(message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def messages(self) -> list[str]:
        return self._messages

    async def send(self, bot: Any, chat_id: int) -> None:
        async def send_chunk(text: str) -> None:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

        await send_in_sequence(self._messages, send_chunk)
