"""Container liveness probe for the Docker HEALTHCHECK.

Exits 0 if the bot has refreshed its heartbeat recently, non-zero otherwise.
A missing or stale heartbeat means the polling loop / job queue is no longer
running, even if the process is technically still alive.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from cs2posts.bot import settings


logger = logging.getLogger(__name__)


def main() -> int:
    path = Path(settings.HEARTBEAT_FILEPATH)
    if not path.exists():
        logger.error(f'heartbeat file missing: {path}')
        return 1

    age = time.time() - path.stat().st_mtime
    # Tolerate one fully missed crawl cycle before declaring the bot dead.
    max_age = settings.CS2_UPDATE_CHECK_INTERVAL * 2 + 60
    if age > max_age:
        logger.error(f'heartbeat stale: {age:.0f}s old (max {max_age}s)')
        return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
