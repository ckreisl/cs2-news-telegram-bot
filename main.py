from __future__ import annotations

import logging

from cs2posts.bot.cs2 import CounterStrike2UpdateBot
from cs2posts.bot.heartbeat import write_heartbeat
from cs2posts.bot.spam import SpamProtector
from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.db import SqliteChatRepository
from cs2posts.db import SqlitePostRepository
from cs2posts.exceptions import ConfigurationError
from cs2posts.settings import Settings

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # Avoid logging every GET and POST httpx makes on our behalf.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def create_bot(settings: Settings) -> CounterStrike2UpdateBot:
    """The composition root: every concrete dependency is chosen here."""
    return CounterStrike2UpdateBot(
        settings=settings,
        crawler=CounterStrike2Crawler(),
        spam_protector=SpamProtector(settings),
        post_db=SqlitePostRepository.at(settings.post_db_filepath),
        chat_db=SqliteChatRepository.at(settings.chat_db_filepath),
    )


def main() -> int:
    configure_logging()

    try:
        settings = Settings.from_env()
    except ConfigurationError as exc:
        logger.error("Cannot start: %s", exc)
        return 1

    # Write the heartbeat before connecting to Telegram so the healthcheck
    # passes ahead of the first crawl cycle; post_checker refreshes it after.
    write_heartbeat(settings.heartbeat_filepath)

    # run() owns the event loop for the whole process; the bot's async
    # startup runs inside it, from the post_init hook.
    create_bot(settings).run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
