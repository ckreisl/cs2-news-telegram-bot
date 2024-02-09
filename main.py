from __future__ import annotations

import logging

from cs2posts.bot import settings
from cs2posts.bot.cs2 import CounterStrike2UpdateBot


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)


def main() -> int:
    cs2_update_bot = CounterStrike2UpdateBot(
        token=settings.TELEGRAM_TOKEN)
    cs2_update_bot.run()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
