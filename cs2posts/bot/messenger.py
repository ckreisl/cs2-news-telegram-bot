from __future__ import annotations

import logging
from typing import Any

from telegram.error import BadRequest
from telegram.error import ChatMigrated
from telegram.error import Forbidden

from cs2posts.db import ChatRepository
from cs2posts.dto.chats import Chat
from cs2posts.msg import Sendable

logger = logging.getLogger(__name__)

CHAT_NOT_FOUND = "Chat not found"
MAX_MIGRATION_HOPS = 3


class ChatMessenger:
    """Delivers messages to a chat and keeps chat storage in step with Telegram.

    A failed send is rarely just a failed send: it tells us the chat was
    deleted, blocked the bot, or was upgraded to a supergroup. Owning that
    reaction here keeps chat lifecycle out of the bot's command handlers.
    """

    def __init__(self, chat_db: ChatRepository) -> None:
        self._chat_db = chat_db

    async def send(self, bot: Any, message: Sendable, chat: Chat | None) -> bool:
        """Send ``message`` to ``chat``. Returns whether it was delivered."""
        if chat is None:
            logger.error("No chat to send to; dropping message.")
            return False
        return await self._send(bot, message, chat, hops=0)

    async def _send(self, bot: Any, message: Sendable, chat: Chat, hops: int) -> bool:
        try:
            await message.send(bot, chat_id=chat.chat_id)
            return True
        except BadRequest as exc:
            if exc.message == CHAT_NOT_FOUND:
                logger.error("Chat %s no longer exists; removing it.", chat.chat_id)
                await self._chat_db.remove(chat)
            else:
                logger.error("Bad request for chat %s: %s", chat.chat_id, exc)
            return False
        except Forbidden as exc:
            logger.error("Blocked by chat %s (%s); removing it.", chat.chat_id, exc)
            await self._chat_db.remove(chat)
            return False
        except ChatMigrated as exc:
            return await self._resend_after_migration(bot, message, chat, exc, hops)

    async def _resend_after_migration(
        self, bot: Any, message: Sendable, chat: Chat, exc: ChatMigrated, hops: int
    ) -> bool:
        logger.info("Chat %s migrated to %s.", chat.chat_id, exc.new_chat_id)
        migrated = await self._chat_db.migrate(chat, exc.new_chat_id)

        if hops >= MAX_MIGRATION_HOPS:
            # Guard against a migration cycle walking us off the stack.
            logger.error(
                "Giving up on chat %s after %s migrations.", chat.chat_id, hops
            )
            return False

        return await self._send(bot, message, migrated, hops + 1)
