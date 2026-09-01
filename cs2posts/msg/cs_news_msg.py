from __future__ import annotations

import asyncio
import html
import logging
from functools import singledispatchmethod
from typing import Any

import httpcore
import httpx
from telegram import InputMediaPhoto
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.error import ChatMigrated
from telegram.error import Forbidden

from cs2posts.content import Carousel
from cs2posts.content import Content
from cs2posts.content import ContentExtractor
from cs2posts.content import Image
from cs2posts.content import TextBlock
from cs2posts.content import Video
from cs2posts.content import Youtube
from cs2posts.dto.post import Post
from cs2posts.msg.constants import MAX_MEDIA_GROUP_SIZE
from cs2posts.msg.constants import MAX_SEND_RETRIES
from cs2posts.msg.constants import TELEGRAM_SEND_DELAY_SECONDS
from cs2posts.msg.sendable import send_in_sequence
from cs2posts.msg.telegram import split_text
from cs2posts.parser import Steam2TelegramHTML
from cs2posts.parser import SteamListParser
from cs2posts.parser import SteamNewsTableParser
from cs2posts.utils import extract_url
from cs2posts.utils import get_redirected_url
from cs2posts.utils import is_valid_url

logger = logging.getLogger(__name__)

# Errors that are worth another attempt: the network hiccupped.
TRANSIENT_ERRORS = (httpx.ReadTimeout, httpcore.ReadTimeout, httpx.ConnectError)
CHAT_NOT_FOUND = "Chat not found"


class CounterStrikeNewsMessage:
    """A news post rendered as an ordered sequence of Telegram sends.

    Implements :class:`~cs2posts.msg.sendable.Sendable` directly rather than
    inheriting from ``TelegramMessage``: a post is a mixed media sequence, not
    one chunked string, and the previous inheritance left ``message`` and
    ``messages`` permanently unset on every instance.
    """

    def __init__(self, post: Post) -> None:
        self.post = post
        self.content: list[Content] = ContentExtractor(
            self._create_parser().parse(post.contents)
        ).extract()
        self._add_header()
        self._add_footer()

    def _create_parser(self) -> Steam2TelegramHTML:
        return (
            Steam2TelegramHTML()
            .add_parser(SteamListParser(), priority=1)
            .add_parser(SteamNewsTableParser(), priority=2)
        )

    @property
    def header(self) -> str:
        return f"<b>{html.escape(self.post.title)}</b>\n({self.post.date_display})"

    @property
    def footer(self) -> str:
        url = get_redirected_url(self.post.url)
        return (
            f"(Author: {html.escape(self.post.author)})\n\n"
            f"Source: <a href='{html.escape(url, quote=True)}'>Link</a>"
        )

    def _add_header(self) -> None:
        if not self.content:
            return

        first = self.content[0]
        if not isinstance(first, TextBlock):
            # Media leads the post; the header becomes its caption instead.
            return

        if first.is_heading and self.header not in first.text:
            first.text = f"{self.header}\n\n{first.text}"

    def _add_footer(self) -> None:
        footer = self.footer

        if not self.content:
            self.content = [TextBlock(0, len(footer), False, footer)]
            return

        last = self.content[-1]
        if isinstance(last, TextBlock):
            # The extracted text keeps whatever trailing newlines the source
            # markup had; strip them so the footer always sits exactly one
            # blank line below the last line of content. A media-only post
            # still ends in an empty TextBlock, which has nothing to sit below.
            body = last.text.rstrip()
            last.text = f"{body}\n\n{footer}" if body else footer
            return

        self.content.append(
            TextBlock(
                text_pos_start=last.text_pos_end + 1,
                text_pos_end=last.text_pos_end + 1 + len(footer),
                is_heading=False,
                text=footer,
            )
        )

    async def _is_valid_media_url(self, url: str | None) -> bool:
        return await asyncio.to_thread(is_valid_url, url)

    def _caption(self, content: Content) -> str | None:
        return self.header if content.is_heading else None

    @singledispatchmethod
    async def send_content(self, content: Content, bot: Any, chat_id: int) -> None:
        """Deliver one piece of content.

        Registered per content type, so adding a new one means adding a
        handler here rather than extending an ``isinstance`` chain.
        """
        raise TypeError(f"Unsupported content type: {type(content)!r}")

    @send_content.register
    async def _(self, content: TextBlock, bot: Any, chat_id: int) -> None:
        async def send_chunk(text: str) -> None:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

        await send_in_sequence(split_text(content.text), send_chunk)

    @send_content.register
    async def _(self, content: Image, bot: Any, chat_id: int) -> None:
        image_url = extract_url(content.url)

        if not await self._is_valid_media_url(image_url):
            logger.error("Not sending image, invalid URL: %s", image_url)
            return

        await bot.send_photo(
            chat_id=chat_id,
            photo=image_url,
            caption=self._caption(content),
            parse_mode=ParseMode.HTML,
        )

    @send_content.register
    async def _(self, content: Carousel, bot: Any, chat_id: int) -> None:
        media = []
        for image in content.images:
            image_url = extract_url(image.url)
            if image_url is None or not await self._is_valid_media_url(image_url):
                logger.error("Not sending image, invalid URL: %s", image_url)
                continue
            media.append(InputMediaPhoto(media=image_url))

        groups = [
            media[start : start + MAX_MEDIA_GROUP_SIZE]
            for start in range(0, len(media), MAX_MEDIA_GROUP_SIZE)
        ]

        async def send_group(group: list[InputMediaPhoto]) -> None:
            await bot.send_media_group(chat_id=chat_id, media=group)

        await send_in_sequence(groups, send_group)

    @send_content.register
    async def _(self, content: Video, bot: Any, chat_id: int) -> None:
        source_url = content.source_url
        if source_url is None:
            return

        video_url = extract_url(source_url)
        if not await self._is_valid_media_url(video_url):
            logger.error("Not sending video, invalid URL: %s", video_url)
            return

        await bot.send_video(
            chat_id=chat_id,
            video=video_url,
            thumbnail=extract_url(content.poster) if content.poster else None,
            caption=self._caption(content),
            supports_streaming=True,
            parse_mode=ParseMode.HTML,
        )

    @send_content.register
    async def _(self, content: Youtube, bot: Any, chat_id: int) -> None:
        link = f"<a href='{content.watch_url}'>{content.watch_url}</a>"
        caption = self._caption(content)
        text = f"{caption}\n\n{link}" if caption else link

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )

    async def _send_with_retry(
        self,
        content: Content,
        bot: Any,
        chat_id: int,
        max_retries: int = MAX_SEND_RETRIES,
    ) -> bool:
        kind = type(content).__name__

        for attempt in range(max_retries + 1):
            try:
                await self.send_content(content, bot, chat_id)
                return True
            except TRANSIENT_ERRORS as exc:
                if attempt >= max_retries:
                    logger.exception(
                        "Giving up after %s retries for chat_id=%s content=%s: %s",
                        max_retries,
                        chat_id,
                        kind,
                        exc,
                    )
                    return False
                delay = TELEGRAM_SEND_DELAY_SECONDS * (2**attempt)
                logger.warning(
                    "Transient error for chat_id=%s content=%s attempt=%s/%s"
                    " retry_in=%ss: %s",
                    chat_id,
                    kind,
                    attempt + 1,
                    max_retries + 1,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
            except Forbidden, ChatMigrated:
                # Chat-level failures: the whole post is undeliverable to this
                # chat. Propagate so the bot can drop or migrate the chat
                # instead of failing again on every future post.
                raise
            except BadRequest as exc:
                if exc.message == CHAT_NOT_FOUND:
                    raise
                logger.error(
                    "Could not send to chat_id=%s content=%s: %s", chat_id, kind, exc
                )
                return False
            except Exception as exc:
                logger.exception(
                    "Could not send to chat_id=%s content=%s: %s", chat_id, kind, exc
                )
                return False

        return False

    async def send(self, bot: Any, chat_id: int) -> None:
        async def send_one(content: Content) -> None:
            await self._send_with_retry(content, bot, chat_id)

        await send_in_sequence(self.content, send_one)
