from __future__ import annotations

import asyncio
import logging

from cs2posts.bot import settings
from cs2posts.bot.cs2 import CounterStrike2UpdateBot
from cs2posts.bot.heartbeat import write_heartbeat
from cs2posts.bot.spam import SpamProtector
from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.db import ChatDatabase
from cs2posts.db import PostDatabase


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)


def main() -> int:
    # Write heartbeat immediately on startup, before Telegram connection.
    # This ensures the healthcheck passes before the first crawl cycle.
    # The heartbeat will be refreshed in post_checker() each crawl cycle.
    write_heartbeat(settings.HEARTBEAT_FILEPATH)

    cs2_update_bot = CounterStrike2UpdateBot(
        crawler=CounterStrike2Crawler(),
        spam_protector=SpamProtector(),
        post_db=PostDatabase(settings.POST_DB_FILEPATH),
        chat_db=ChatDatabase(settings.CHAT_DB_FILEPATH),
        token=settings.TELEGRAM_TOKEN)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cs2_update_bot.async_init())
    cs2_update_bot.run()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
