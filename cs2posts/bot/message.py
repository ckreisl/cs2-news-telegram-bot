from __future__ import annotations

import abc
import logging
import re

import requests
from telegram.constants import ParseMode

from cs2posts.bot.constants import TELEGRAM_MAX_MESSAGE_LENGTH
from cs2posts.parser.steam2telegram_html import Steam2TelegramHTML
from cs2posts.parser.steam_list import SteamListParser
from cs2posts.parser.steam_news_image import SteamNewsImageParser
from cs2posts.parser.steam_news_youtube import SteamNewsYoutubeParser
from cs2posts.parser.steam_update_heading import SteamUpdateHeadingParser
from cs2posts.post import Post


logger = logging.getLogger(__name__)


class TelegramMessage:

    def __init__(self, message: str) -> None:
        self.__message = message
        self.__messages = self.split()

    @property
    def message(self) -> str:
        return self.__message

    @property
    def messages(self) -> list[str]:
        return self.__messages

    def split(self) -> list[str]:

        if len(self.message) < TELEGRAM_MAX_MESSAGE_LENGTH:
            return [self.message]

        lines = self.message.split('\n')
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
        raise NotImplementedError("Method not implemented")


class ImageContainer:

    STEAM_CLAN_IMAGE: str = "https://clan.akamai.steamstatic.com/images/"

    def __init__(self, post: Post) -> None:
        self.__post = post
        self.__matches = re.findall(
            re.compile(r'\[img\](.*?)\[/img\]'), self.post.contents)
        self.__url = None if self.is_empty() else self.__matches[0]

        if self.__url is not None:
            self.__url = self.resolve_image_url()

    @property
    def post(self) -> Post:
        return self.__post

    @property
    def url(self) -> str | None:
        return self.__url

    @property
    def caption(self) -> str | None:
        if self.is_empty():
            return None
        return f"<b>{self.post.title}</b> ({self.post.date_as_datetime})"

    def is_empty(self) -> bool:
        if self.__matches is None:
            return True
        return len(self.__matches) == 0

    def resolve_image_url(self) -> str:
        return self.url.replace("{STEAM_CLAN_IMAGE}", self.STEAM_CLAN_IMAGE)

    def is_valid_url(self) -> bool:
        if self.is_empty():
            return False

        if not self.url.startswith("http"):
            return False

        try:
            response = requests.get(self.url)
        except Exception as e:
            logger.error(f"Failed to get image from {self.url}: {e}")
            return False

        return response.ok

    def is_valid(self) -> bool:
        return self.is_valid_url()


class CounterStrikeNewsMessage(TelegramMessage):

    def __init__(self, post: Post) -> None:
        self.post = post

        self.image = ImageContainer(post)

        parser = Steam2TelegramHTML(post.contents)
        parser.add_parser(parser=SteamListParser, priority=1)
        if not self.image.is_empty():
            parser.add_parser(parser=SteamNewsImageParser, priority=2)
        parser.add_parser(parser=SteamNewsYoutubeParser, priority=3)

        msg = ""
        if not self.image.is_valid():
            msg += f"<b>{post.title}</b>\n"
            msg += f"({post.date_as_datetime})\n\n"

        msg += parser.parse()
        msg += "\n\n"
        msg += f"(Author: {post.author})"
        msg += "\n\n"
        msg += f"Source: <a href='{post.url}'>{post.url}</a>"

        super().__init__(msg)

    async def send(self, bot, chat_id: int) -> None:
        if self.image.is_valid():
            await bot.send_photo(
                chat_id=chat_id,
                photo=self.image.url,
                caption=self.image.caption,
                parse_mode=ParseMode.HTML)

        for msg in self.messages:
            await bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)


class CounterStrikeUpdateMessage(TelegramMessage):

    def __init__(self, post: Post) -> None:

        parser = Steam2TelegramHTML(post.contents)
        parser.add_parser(parser=SteamListParser, priority=1)
        parser.add_parser(parser=SteamUpdateHeadingParser, priority=2)

        msg = f"<b>{post.title}</b>\n"
        msg += f"({post.date_as_datetime})\n"
        msg += "\n"
        msg += parser.parse()
        msg += f"(Author: {post.author})"
        msg += "\n\n"
        msg += f"Source: <a href='{post.url}'>{post.url}</a>"

        super().__init__(msg)

    async def send(self, bot, chat_id: int) -> None:
        for msg in self.messages:
            await bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)


class TelegramMessageFactory:

    @staticmethod
    def create(post: Post) -> TelegramMessage:
        if post.is_news():
            return CounterStrikeNewsMessage(post)
        if post.is_update():
            return CounterStrikeUpdateMessage(post)
        raise ValueError(f"Unknown post type {post.title=} {post.url=}")
