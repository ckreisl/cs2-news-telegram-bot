from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from cs2posts.db import ChatRepository
from cs2posts.db import PostRepository
from .notifier import PostNotifier

logger = logging.getLogger(__name__)


class JsonImportable(Protocol):
    async def import_from_json(self, filepath: Path) -> None: ...


async def import_json(
    repository: JsonImportable, filepath: Path | None, label: str
) -> None:
    """Best-effort import of the legacy JSON snapshots.

    A malformed or missing file must not stop the bot from starting, so
    failures are logged and swallowed here rather than at each call site.
    """
    if filepath is None:
        return

    try:
        await repository.import_from_json(filepath)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        logger.error("Could not import %s from %s: %s", label, filepath, exc)


async def bootstrap(
    *,
    chat_db: ChatRepository,
    post_db: PostRepository,
    notifier: PostNotifier,
    import_chats_from: Path | None = None,
    import_posts_from: Path | None = None,
) -> None:
    """Bring storage and the notifier's view of the world up to date."""
    await post_db.setup()
    await chat_db.setup()

    await import_json(chat_db, import_chats_from, "chats")
    await import_json(post_db, import_posts_from, "posts")

    await notifier.seed_if_empty()
    await notifier.load()
