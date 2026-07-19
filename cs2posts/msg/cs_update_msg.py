from __future__ import annotations

import logging

from .cs_news_msg import CounterStrikeNewsMessage
from cs2posts.dto.post import Post
from cs2posts.parser.steam2telegram_html import Steam2TelegramHTML
from cs2posts.parser.steam_update_heading import SteamUpdateHeadingParser


logger = logging.getLogger(__name__)


class CounterStrikeUpdateMessage(CounterStrikeNewsMessage):
    """Shares the news content pipeline (text, images, videos, ...) and
    additionally formats bracketed section headings like "[ MAPS ]"."""

    def _create_parser(self, post: Post) -> Steam2TelegramHTML:
        parser = super()._create_parser(post)
        parser.add_parser(parser=SteamUpdateHeadingParser, priority=3)
        return parser
