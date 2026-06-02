from __future__ import annotations

import logging
import time
from pathlib import Path


logger = logging.getLogger(__name__)


def write_heartbeat(filepath: str) -> None:
    """Record a liveness timestamp for the container healthcheck.

    Called once per crawl cycle so a stale file signals that the polling
    loop / job queue has stopped. Failures are logged but never raised:
    a missing heartbeat must not take down the bot itself.
    """
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(time.time()))
    except OSError as e:
        logger.warning(f'Could not write heartbeat to {filepath}: {e}')
