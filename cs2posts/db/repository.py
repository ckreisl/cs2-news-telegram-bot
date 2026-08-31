from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from cs2posts.dto import Chat
from cs2posts.dto import Post
from cs2posts.dto.post import PostType


class ChatRepository(Protocol):
    """Everything the bot needs from chat storage.

    The bot depends on this rather than on the sqlite implementation, so the
    storage backend can change and tests can substitute an in-memory double.
    """

    async def setup(self) -> None: ...

    async def get(self, chat_id: int) -> Chat | None: ...

    async def add(self, chat: Chat) -> Chat: ...

    async def update(self, chat: Chat) -> None: ...

    async def remove(self, chat: Chat) -> None: ...

    async def migrate(self, chat: Chat, new_chat_id: int) -> Chat: ...

    async def running_chats_interested_in(
        self, post_type: PostType
    ) -> Sequence[Chat]: ...

    async def import_from_json(self, filepath: Path) -> None: ...

    async def backup(self, filepath: Path) -> None: ...


class PostRepository(Protocol):
    """Everything the bot needs from post storage."""

    async def setup(self) -> None: ...

    async def is_empty(self) -> bool: ...

    async def save(self, post: Post) -> None: ...

    async def latest(self, post_type: PostType | None = None) -> Post | None: ...

    async def import_from_json(self, filepath: Path) -> None: ...
