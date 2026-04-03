from __future__ import annotations

import logging

from bs4 import BeautifulSoup
from bs4 import Tag

from .telegram import TelegramMessage
from cs2posts.dto.post import Post
from cs2posts.utils import Utils


logger = logging.getLogger(__name__)


def cleanup_soup(soup: BeautifulSoup) -> None:
    for img in soup.find_all("img"):
        img.decompose()

    for br in soup.find_all("br"):
        br.decompose()


def extract_read_more_links(soup: BeautifulSoup) -> list[Tag]:
    read_more: list[Tag] = []
    for anchor in soup.find_all("a"):
        if not isinstance(anchor, Tag):
            continue

        text = anchor.text.lower()
        if "read more" in text or "read the rest of the story" in text:
            read_more.append(anchor)

    return read_more


def remove_read_more_links(read_more: list[Tag]) -> None:
    for anchor in read_more:
        anchor.extract()


def build_content(soup: BeautifulSoup) -> str:
    content = str(soup)
    content = content.replace("<p>", "").replace("</p>", "")
    content = content.replace("<br/>", "")
    return content.strip()


def build_message(post: Post, content: str) -> str:
    msg = "🔗 <b>External News</b>\n\n"
    msg += f"<b>{post.title}</b>\n"
    msg += f"({post.date_as_datetime})\n"
    msg += "\n"
    msg += content
    msg += "\n\n"
    msg += f"Source: <a href='{post.url}'>Link</a>"
    return msg


class CounterStrikeExternalMessage(TelegramMessage):

    def __init__(self, post: Post) -> None:
        post.url = Utils.get_redirected_url(post.url)
        self.post = post

        soup = BeautifulSoup(post.contents, "html.parser")

        cleanup_soup(soup)
        read_more = extract_read_more_links(soup)
        remove_read_more_links(read_more)

        content = build_content(soup)

        if len(read_more) > 0:
            href = read_more[0].get("href")
            if isinstance(href, str):
                post.url = href

        msg = build_message(post, content)

        super().__init__(msg)
