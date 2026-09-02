from __future__ import annotations

import html
import logging

from bs4 import BeautifulSoup
from bs4 import Tag

from cs2posts.dto.post import Post
from cs2posts.utils import get_redirected_url
from .telegram import TelegramMessage

logger = logging.getLogger(__name__)

READ_MORE_PHRASES = ("read more", "read the rest of the story")


def strip_media(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(["img", "br"]):
        tag.decompose()


def find_read_more_links(soup: BeautifulSoup) -> list[Tag]:
    return [
        anchor
        for anchor in soup.find_all("a")
        if isinstance(anchor, Tag)
        and any(phrase in anchor.text.lower() for phrase in READ_MORE_PHRASES)
    ]


def remove_read_more_links(read_more: list[Tag]) -> None:
    for anchor in read_more:
        anchor.extract()


def build_content(soup: BeautifulSoup) -> str:
    content = str(soup)
    content = content.replace("<p>", "").replace("</p>", "")
    content = content.replace("<br/>", "")
    return content.strip()


def render_external_message(post: Post, content: str, source_url: str) -> str:
    return (
        "🔗 <b>External News</b>\n\n"
        f"<b>{html.escape(post.title)}</b>\n"
        f"({post.date_display})\n"
        "\n"
        f"{content}"
        "\n\n"
        f"Source: <a href='{html.escape(source_url, quote=True)}'>Link</a>"
    )


def _source_url(post: Post, read_more: list[Tag]) -> str:
    """Prefer the article's own "read more" target over Steam's redirect."""
    if read_more:
        href = read_more[0].get("href")
        if isinstance(href, str):
            return href
    return get_redirected_url(post.url)


class CounterStrikeExternalMessage(TelegramMessage):
    """A third-party article summary, rendered as plain text."""

    def __init__(self, post: Post) -> None:
        self.post = post

        soup = BeautifulSoup(post.contents, "html.parser")
        strip_media(soup)
        read_more = find_read_more_links(soup)
        remove_read_more_links(read_more)

        super().__init__(
            render_external_message(
                post, build_content(soup), _source_url(post, read_more)
            )
        )
