from __future__ import annotations

import asyncio
import logging

from telegram.constants import ParseMode

from cs2posts.msg.constants import TELEGRAM_MAX_MESSAGE_LENGTH
from cs2posts.msg.constants import TELEGRAM_SEND_DELAY_SECONDS


logger = logging.getLogger(__name__)


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

    async def send(self, bot, chat_id: int) -> None:
        """Default implementation: sends each text chunk in ``self.messages``.

        Subclasses that handle richer content (images, carousels, etc.) should
        override this method.
        """
        for i, msg in enumerate(self.messages):
            await bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)
            if i < len(self.messages) - 1:
                await asyncio.sleep(TELEGRAM_SEND_DELAY_SECONDS)
