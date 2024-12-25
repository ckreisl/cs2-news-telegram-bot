from __future__ import annotations

import logging

from bs4 import BeautifulSoup
from telegram.constants import ParseMode

from .telegram import TelegramMessage
from cs2posts.dto.post import Post
from cs2posts.utils import Utils


logger = logging.getLogger(__name__)


class CounterStrikeExternalMessage(TelegramMessage):

    def __init__(self, post: Post) -> None:
        post.url = Utils.get_redirected_url(post.url)
        self.post = post

        soup = BeautifulSoup(post.contents, "html.parser")

        for img in soup.find_all("img"):
            img.decompose()

        for br in soup.find_all("br"):
            br.decompose()

        read_more_all = soup.find_all("a")

        read_more = []
        for a in read_more_all:
            if "read more" in a.text.lower():
                read_more.append(a)
            if "read the rest of the story" in a.text.lower():
                read_more.append(a)

        if len(read_more) > 0:
            for a in read_more:
                a.extract()

        content = str(soup)
        content = content.replace("<p>", "").replace("</p>", "")
        content = content.replace("<br/>", "")
        content = content.lstrip().rstrip()

        msg = "🔗 <b>External News</b>\n\n"
        msg += f"<b>{post.title}</b>\n"
        msg += f"({post.date_as_datetime})\n"
        msg += "\n"
        msg += content
        msg += "\n\n"

        if len(read_more) > 0:
            post.url = read_more[0].get("href")

        msg += f"Source: <a href='{post.url}'>Link</a>"

        super().__init__(msg)

    async def send(self, bot, chat_id: int) -> None:
        for msg in self.messages:
            await bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)
