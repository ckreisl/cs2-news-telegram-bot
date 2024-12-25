from __future__ import annotations

import abc
import logging

from cs2posts.msg.constants import TELEGRAM_MAX_MESSAGE_LENGTH


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

    @abc.abstractmethod
    async def send(self, bot, chat_id: int) -> None:
        raise NotImplementedError("Method not implemented")  # pragma: no cover
