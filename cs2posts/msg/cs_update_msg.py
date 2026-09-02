from __future__ import annotations

from cs2posts.parser import Steam2TelegramHTML
from cs2posts.parser import SteamUpdateHeadingParser
from .cs_news_msg import CounterStrikeNewsMessage


class CounterStrikeUpdateMessage(CounterStrikeNewsMessage):
    """Shares the news content pipeline (text, images, videos, ...) and
    additionally formats bracketed section headings like "[ MAPS ]"."""

    def _create_parser(self) -> Steam2TelegramHTML:
        return (
            super()._create_parser().add_parser(SteamUpdateHeadingParser(), priority=3)
        )
