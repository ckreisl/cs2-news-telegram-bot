from __future__ import annotations

import asyncio
import functools
import logging

from telegram.constants import ParseMode

from cs2posts.msg.constants import TELEGRAM_MAX_MESSAGE_LENGTH
from cs2posts.msg.constants import TELEGRAM_SEND_DELAY_SECONDS


logger = logging.getLogger(__name__)


def resilient_send(func):
    """Decorator for async send-helper methods.

    Catches any exception, logs it with full traceback, and returns normally
    so that the caller's iteration loop continues with the next block.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            logging.getLogger(func.__module__).exception(
                f"Failed to execute {func.__name__}, skipping block")
    return wrapper


class TelegramMessage:

    def __init__(self, message: str) -> None:
        self.__message = message
        self.__messages = self.split(message)

    @property
    def message(self) -> str:
        return self.__message

    @property
    def messages(self) -> list[str]:
        return self.__messages

    def split(self, message: str) -> list[str]:

        if len(message) < TELEGRAM_MAX_MESSAGE_LENGTH:
            return [message]

        lines = message.split('\n')
        chunks = []
        chunk = ''

        for line in lines:
            if (len(chunk) + len(line)) < TELEGRAM_MAX_MESSAGE_LENGTH:
                chunk += line + "\n"
                continue

            chunks.append(chunk)
            chunk = line + "\n"

        chunks.append(chunk)

        return chunks

    @resilient_send
    async def _send_text_chunk(self, bot, chat_id: int, text: str) -> None:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)

    async def send(self, bot, chat_id: int) -> None:
        """Default implementation: sends each text chunk in ``self.messages``.

        Subclasses that handle richer content (images, carousels, etc.) should
        override this method.
        """
        for i, msg in enumerate(self.messages):
            await self._send_text_chunk(bot, chat_id, msg)
            if i < len(self.messages) - 1:
                await asyncio.sleep(TELEGRAM_SEND_DELAY_SECONDS)
