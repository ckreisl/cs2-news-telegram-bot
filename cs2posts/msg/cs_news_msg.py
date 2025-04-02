from __future__ import annotations

import logging

from telegram import InputMediaPhoto
from telegram.constants import ParseMode

from .telegram import TelegramMessage
from cs2posts.content import Carousel
from cs2posts.content import ContentExtractor
from cs2posts.content import Image
from cs2posts.content import TextBlock
from cs2posts.content import Video
from cs2posts.content import Youtube
from cs2posts.dto.post import Post
from cs2posts.msg.constants import MAX_MEDIA_GROUP_SIZE
from cs2posts.parser.steam2telegram_html import Steam2TelegramHTML
from cs2posts.parser.steam_list import SteamListParser
from cs2posts.utils import Utils


logger = logging.getLogger(__name__)


class CounterStrikeNewsMessage(TelegramMessage):

    def __init__(self, post: Post) -> None:
        self.post = post
        parser = Steam2TelegramHTML(post.contents)
        parser.add_parser(parser=SteamListParser, priority=1)

        self.content = ContentExtractor(parser.parse()).extract()
        self.__add_header()
        self.__add_footer()

    def __add_header(self) -> None:
        if (isinstance(self.content[0], Image) or  # noqa
            isinstance(self.content[0], Video) or  # noqa
            isinstance(self.content[0], Youtube) or  # noqa
            isinstance(self.content[0], Carousel)):  # noqa
            # Ignore header we set it as caption
            return

        header = self.get_header()
        if isinstance(self.content[0], TextBlock):
            if self.content[0].is_heading and header not in self.content[0].text:
                self.content[0].text = self.get_header() + "\n\n" + \
                    self.content[0].text

    def __add_footer(self) -> None:
        url = Utils.get_redirected_url(self.post.url)
        footer = (
            f"\n\n(Author: {self.post.author})\n\n"
            f"Source: <a href='{url}'>Link</a>"
        )

        if isinstance(self.content[-1], TextBlock):
            self.content[-1].text += footer
        else:
            self.content.append(TextBlock(
                text_pos_start=self.content[-1].text_pos_end + 1,
                text_pos_end=len(footer),
                is_heading=False,
                text=footer))

    def get_header(self) -> str:
        return f"<b>{self.post.title}</b>\n({self.post.date_as_datetime})"

    async def send_message(self, bot, chat_id: int, message: TextBlock) -> None:
        for text in self.split(message.text):
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)

    async def send_image(self, bot, chat_id: int, image: Image) -> None:
        image_url = Utils.extract_url(image.url)

        if not Utils.is_valid_url(image_url):
            logger.error(
                f"Not sending image due to invalid image URL {image_url=}")
            return

        caption = self.get_header() if image.is_heading else None
        await bot.send_photo(
            chat_id=chat_id,
            photo=image_url,
            caption=caption,
            parse_mode=ParseMode.HTML)

    async def send_carousel(self, bot, chat_id: int, carousel: Carousel) -> None:
        media = []
        for image in carousel.images:
            image_url = Utils.extract_url(image.url)

            if not Utils.is_valid_url(image_url):
                logger.error(
                    f"Not sending image due to invalid image URL {image_url=}")
                continue

            media.append(InputMediaPhoto(media=image_url))

        chunks = [media[i:i + MAX_MEDIA_GROUP_SIZE] for i in range(0, len(media), MAX_MEDIA_GROUP_SIZE)]

        for chunk in chunks:
            await bot.send_media_group(
                chat_id=chat_id,
                media=chunk)

    async def send_video(self, bot, chat_id: int, video: Video) -> None:
        video_url = Utils.extract_url(video.mp4)

        if not Utils.is_valid_url(video_url):
            logger.error(
                f"Not sending video due to invalid video URL {video_url=}")
            return

        thumbnail_url = Utils.extract_url(video.poster)
        caption = self.get_header() if video.is_heading else None
        await bot.send_video(
            chat_id=chat_id,
            video=video_url,
            thumbnail=thumbnail_url,
            caption=caption,
            supports_streaming=True,
            parse_mode=ParseMode.HTML)

    async def send_youtube_video(self, bot, chat_id: int, youtube: Youtube) -> None:
        text: str = ""
        if youtube.is_heading:
            text = self.get_header() + "\n\n"
        text += f"<a href='{youtube.get_url()}'>{youtube.get_url()}</a>"

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False)

    async def send(self, bot, chat_id: int) -> None:
        for content in self.content:
            if isinstance(content, TextBlock):
                await self.send_message(bot, chat_id, content)
            elif isinstance(content, Image):
                await self.send_image(bot, chat_id, content)
            elif isinstance(content, Carousel):
                await self.send_carousel(bot, chat_id, content)
            elif isinstance(content, Video):
                await self.send_video(bot, chat_id, content)
            elif isinstance(content, Youtube):
                await self.send_youtube_video(bot, chat_id, content)
