"""Container liveness probe for the Docker HEALTHCHECK.

Exits 0 if the bot has refreshed its heartbeat recently, non-zero otherwise.
A missing or stale heartbeat means the polling loop / job queue is no longer
running, even if the process is technically still alive.
"""

from __future__ import annotations

import logging
import time

from cs2posts.exceptions import ConfigurationError
from cs2posts.settings import Settings

logger = logging.getLogger(__name__)


def check(settings: Settings) -> int:
    """Exit status for the given configuration. Separated from ``main`` so the
    probe can be tested without touching the process environment."""
    path = settings.heartbeat_filepath
    if not path.exists():
        logger.error("heartbeat file missing: %s", path)
        return 1

    age = time.time() - path.stat().st_mtime
    max_age = settings.max_heartbeat_age_seconds
    if age > max_age:
        logger.error("heartbeat stale: %.0fs old (max %ss)", age, max_age)
        return 1

    return 0


def main() -> int:
    try:
        settings = Settings.from_env()
    except ConfigurationError as exc:
        logger.error("misconfigured: %s", exc)
        return 1

    return check(settings)


if __name__ == "__main__":
    raise SystemExit(main())
