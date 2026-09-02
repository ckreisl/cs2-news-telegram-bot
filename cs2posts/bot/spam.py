from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from telegram.constants import ParseMode

from cs2posts.clock import Clock
from cs2posts.clock import SystemClock
from cs2posts.dto.chats import Chat
from cs2posts.settings import Settings

logger = logging.getLogger(__name__)


def spam_warning_message(chat: Chat, max_strikes: int) -> str:
    return (
        f"<b>Spamming</b> bot results in Timeout <b>({chat.strikes}/{max_strikes})</b>."
    )


def spam_banned_message(chat: Chat, timeout_seconds: int, max_strikes: int) -> str:
    minutes = timeout_seconds // 60
    return (
        f"<b>Strike ({chat.strikes}/{max_strikes})</b> Chat is now"
        f" <b>banned</b> for spamming (Timeout: {minutes} mins)."
    )


class SpamProtector:
    """Rate-limits a chat's commands, escalating to a temporary ban.

    Settings and the clock are injected rather than read from module globals,
    so the thresholds have one lifetime and tests can drive time directly.
    """

    def __init__(self, settings: Settings, clock: Clock | None = None) -> None:
        self._settings = settings
        self._clock = clock if clock is not None else SystemClock()

    @property
    def max_strikes(self) -> int:
        return self._settings.max_strikes

    @property
    def ban_timeout_seconds(self) -> int:
        return self._settings.ban_timeout_seconds

    def _since_last_activity(self, chat: Chat) -> timedelta:
        return self._clock.now() - chat.last_activity

    async def check(self, bot: Any, chat: Chat | None) -> None:
        if chat is None:
            return

        logger.info("Checking chat %s", chat.chat_id)

        if chat.is_banned and self.is_timeouted(chat):
            logger.info("Chat %s is timeouted", chat.chat_id)
            return

        if chat.is_banned:
            self.unban(chat)

        if self.is_spamming(chat):
            await self.strike(bot, chat)
        else:
            logger.info("Chat %s is not spamming", chat.chat_id)
            self.recover_strikes(chat)

        self.update_chat_activity(chat)

    def update_chat_activity(self, chat: Chat) -> None:
        logger.info("Updated chat activity for %s", chat.chat_id)
        chat.last_activity = self._clock.now()

    def is_spamming(self, chat: Chat) -> bool:
        limit = timedelta(milliseconds=self._settings.spam_interval_ms)
        return self._since_last_activity(chat) <= limit

    def is_timeouted(self, chat: Chat) -> bool:
        elapsed = self._since_last_activity(chat).total_seconds()
        return 0 <= elapsed < self.ban_timeout_seconds

    def reduce_strike_level(self, chat: Chat) -> None:
        logger.info("Reduce strike level for %s", chat.chat_id)
        if chat.strikes > 0:
            chat.strikes -= 1

    def increase_strike_level(self, chat: Chat) -> None:
        logger.info("Increase strike level for %s", chat.chat_id)
        if chat.strikes < self.max_strikes:
            chat.strikes += 1

    def recover_strikes(self, chat: Chat) -> None:
        recovery = timedelta(minutes=self._settings.strike_recovery_minutes)
        if self._since_last_activity(chat) >= recovery and chat.strikes > 0:
            logger.info(
                "Chat %s recovered from inactivity, reducing strikes", chat.chat_id
            )
            self.reduce_strike_level(chat)

    def ban(self, chat: Chat) -> None:
        logger.info("Ban chat %s", chat.chat_id)
        chat.is_banned = True

    def unban(self, chat: Chat) -> None:
        logger.info("Unban chat %s", chat.chat_id)
        chat.is_banned = False
        # Serving the ban timeout earns a clean slate; otherwise strikes stay
        # at max_strikes and the next fast message would immediately re-ban.
        chat.strikes = 0

    def is_banned(self, chat: Chat) -> bool:
        return chat.is_banned

    async def strike(self, bot: Any, chat: Chat) -> None:
        if chat.is_banned:
            logger.info("Chat %s is already banned", chat.chat_id)
            return

        logger.info("Strike for %s", chat.chat_id)
        self.increase_strike_level(chat)

        if chat.strikes == self.max_strikes:
            self.ban(chat)
            text = spam_banned_message(chat, self.ban_timeout_seconds, self.max_strikes)
        else:
            text = spam_warning_message(chat, self.max_strikes)

        await bot.send_message(
            chat_id=chat.chat_id, text=text, parse_mode=ParseMode.HTML
        )
