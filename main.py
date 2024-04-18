from __future__ import annotations

import logging

from cs2posts.bot import settings
from cs2posts.bot.cs2 import CounterStrike2UpdateBot
from cs2posts.bot.spam import SpamProtector
from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.store import LocalChatStore
from cs2posts.store import LocalLatestPostStore


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)


def main() -> int:
    cs2_update_bot = CounterStrike2UpdateBot(
        crawler=CounterStrike2Crawler(),
        spam_protector=SpamProtector(),
        local_post_store=LocalLatestPostStore(
            settings.LOCAL_LATEST_POST_STORE_FILEPATH),
        local_chat_store=LocalChatStore(
            settings.LOCAL_CHAT_STORE_FILEPATH),
        token=settings.TELEGRAM_TOKEN)
    cs2_update_bot.run()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
