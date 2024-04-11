from __future__ import annotations

import logging
from datetime import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from telegram.constants import ParseMode

from cs2posts.bot import settings
from cs2posts.bot.chats import Chat


logger = logging.getLogger(__name__)


class SpamProtectorMessages:

    @staticmethod
    def warning(chat: Chat, max_strikes: int) -> str:
        return f"<b>Spamming</b> bot results in Timeout <b>({chat.strikes}/{max_strikes})</b>."

    @staticmethod
    def banned(chat: Chat, timout: int, max_strikes: int) -> str:
        return f"<b>Strike ({chat.strikes}/{max_strikes})</b> Chat is now <b>banned</b> for spamming (Timeout: {int(timout/60)} mins)."


class SpamProtector:

    MAX_STRIKES = settings.CHAT_MAX_STRIKES
    BAN_TIMEOUT = settings.CHAT_BAN_TIMEOUT_SECONDS

    async def check(self, bot, chat: Chat) -> None:
        if chat is None:
            return

        logger.info(f'Checking chat {chat.chat_id}')

        if self.is_banned(chat) and self.is_timeouted(chat):
            logger.info(f'Chat {chat.chat_id} is timeouted')
            return

        if chat.is_banned:
            self.unban(chat)

        if self.is_spamming(chat):
            await self.strike(bot, chat)

        logger.info(f'Chat {chat.chat_id} is not spamming')

        self.update_chat_activity(chat)

    def _get_utc_now(self) -> datetime:
        return datetime.now(tz=ZoneInfo('UTC')).replace(tzinfo=None)

    def update_chat_activity(self, chat: Chat) -> None:
        logger.info(f'Updated chat activity for {chat.chat_id}')
        chat.last_activity = self._get_utc_now()

    def reduce_strike_level(self, chat: Chat) -> None:
        logger.info(f'Reduce strike level for {chat.chat_id}')
        if chat.strikes > 0:
            chat.strikes -= 1

    def increase_strike_level(self, chat: Chat) -> None:
        logger.info(f'Increase strike level for {chat.chat_id}')
        if chat.strikes < self.MAX_STRIKES:
            chat.strikes += 1

    def is_spamming(self, chat: Chat) -> bool:
        time_diff = self._get_utc_now() - chat.last_activity
        limit = timedelta(milliseconds=settings.CHAT_SPAM_INTERVAL_MS)
        return time_diff <= limit

    def ban(self, chat: Chat) -> None:
        logger.info(f'Ban chat {chat.chat_id}')
        chat.is_banned = True

    def unban(self, chat: Chat) -> None:
        logger.info(f'Unban chat {chat.chat_id}')
        chat.is_banned = False

    def is_banned(self, chat: Chat) -> bool:
        return chat.is_banned

    def is_timeouted(self, chat: Chat) -> bool:
        time_diff = self._get_utc_now() - chat.last_activity
        return time_diff.seconds < self.BAN_TIMEOUT

    async def strike(self, bot, chat: Chat) -> None:
        if chat.is_banned:
            logger.info(f'Chat {chat.chat_id} is already banned')
            return

        logger.info(f'Strike for {chat.chat_id}')

        self.increase_strike_level(chat)

        if chat.strikes == self.MAX_STRIKES:
            self.ban(chat)
            await bot.send_message(
                chat_id=chat.chat_id,
                text=SpamProtectorMessages.banned(
                    chat, self.BAN_TIMEOUT, self.MAX_STRIKES),
                parse_mode=ParseMode.HTML)
            return

        await bot.send_message(
            chat_id=chat.chat_id,
            text=SpamProtectorMessages.warning(chat, self.MAX_STRIKES),
            parse_mode=ParseMode.HTML)
