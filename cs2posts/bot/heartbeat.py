from __future__ import annotations

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def write_heartbeat(filepath: Path) -> None:
    """Record a liveness timestamp for the container healthcheck.

    Called once per crawl cycle so a stale file signals that the polling
    loop / job queue has stopped. Failures are logged but never raised:
    a missing heartbeat must not take down the bot itself.
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(str(time.time()))
    except OSError as exc:
        logger.warning("Could not write heartbeat to %s: %s", filepath, exc)
