from __future__ import annotations

import logging

from telegram.constants import ParseMode

from .telegram import TelegramMessage
from cs2posts.dto.post import Post
from cs2posts.parser.steam2telegram_html import Steam2TelegramHTML
from cs2posts.parser.steam_list import SteamListParser
from cs2posts.parser.steam_update_heading import SteamUpdateHeadingParser
from cs2posts.utils import Utils


logger = logging.getLogger(__name__)


class CounterStrikeUpdateMessage(TelegramMessage):

    def __init__(self, post: Post) -> None:
        post.url = Utils.get_redirected_url(post.url)

        parser = Steam2TelegramHTML(post.contents)
        parser.add_parser(parser=SteamListParser, priority=1)
        parser.add_parser(parser=SteamUpdateHeadingParser, priority=2)

        msg = f"<b>{post.title}</b>\n"
        msg += f"({post.date_as_datetime})\n"
        msg += "\n"
        msg += parser.parse()
        msg += "\n\n" if not msg.endswith("\n\n") else ""
        msg += f"(Author: {post.author})"
        msg += "\n\n"
        msg += f"Source: <a href='{post.url}'>Link</a>"

        super().__init__(msg)

    async def send(self, bot, chat_id: int) -> None:
        for msg in self.messages:
            await bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)
