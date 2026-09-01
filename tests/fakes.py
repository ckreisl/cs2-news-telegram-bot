"""In-memory doubles for the repository protocols.

Substituting these for ``AsyncMock`` lets the bot tests assert on observable
state ("the chat was removed") rather than on call bookkeeping ("remove was
awaited once"), so they survive refactoring of the code they cover.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from cs2posts.db import ChatRepository
from cs2posts.db import PostRepository
from cs2posts.dto.chats import Chat
from cs2posts.dto.post import Post
from cs2posts.dto.post import PostType


class InMemoryChatRepository:
    def __init__(self, chats: list[Chat] | None = None) -> None:
        self.chats: dict[int, Chat] = {chat.chat_id: chat for chat in chats or []}
        self.backups: list[Path] = []
        self.imported: list[Path] = []
        self.is_setup = False

    async def setup(self) -> None:
        self.is_setup = True

    async def get(self, chat_id: int) -> Chat | None:
        return self.chats.get(chat_id)

    async def add(self, chat: Chat) -> Chat:
        if chat.chat_id in self.chats:
            # Mirrors the bare INSERT the sqlite repository issues, so a test
            # that adds over an existing chat fails here rather than passing
            # against a double that is more forgiving than production.
            raise ValueError(f"chat {chat.chat_id} already exists")
        self.chats[chat.chat_id] = chat
        return chat

    async def save(self, chat: Chat) -> None:
        self.chats[chat.chat_id] = chat

    async def update(self, chat: Chat) -> None:
        self.chats[chat.chat_id] = chat

    async def remove(self, chat: Chat) -> None:
        self.chats.pop(chat.chat_id, None)

    async def migrate(self, chat: Chat, new_chat_id: int) -> Chat:
        old_chat_id = chat.chat_id
        chat.chat_id = new_chat_id
        self.chats[new_chat_id] = chat
        if old_chat_id != new_chat_id:
            self.chats.pop(old_chat_id, None)
        return chat

    async def running_chats_interested_in(self, post_type: PostType) -> list[Chat]:
        return [
            chat
            for chat in self.chats.values()
            if chat.is_running and chat.is_interested_in(post_type)
        ]

    async def import_from_json(self, filepath: Path) -> None:
        self.imported.append(filepath)

    async def backup(self, filepath: Path) -> None:
        self.backups.append(filepath)


class InMemoryPostRepository:
    def __init__(self, posts: list[Post] | None = None) -> None:
        self.posts: dict[str, Post] = {post.gid: post for post in posts or []}
        self.imported: list[Path] = []
        self.is_setup = False

    async def setup(self) -> None:
        self.is_setup = True

    async def is_empty(self) -> bool:
        return not self.posts

    async def save(self, post: Post) -> None:
        self.posts[post.gid] = post

    async def latest(self, post_type: PostType | None = None) -> Post | None:
        candidates = [
            post
            for post in self.posts.values()
            if post_type is None or post.type is post_type
        ]
        return max(candidates, key=lambda post: post.date, default=None)

    async def import_from_json(self, filepath: Path) -> None:
        self.imported.append(filepath)


class FakeBot:
    """Records what would have been sent to Telegram."""

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self.photos: list[dict[str, Any]] = []
        self.videos: list[dict[str, Any]] = []
        self.media_groups: list[dict[str, Any]] = []
        self.deleted: list[dict[str, Any]] = []
        self.edited: list[dict[str, Any]] = []

    @property
    def texts(self) -> list[str]:
        return [message["text"] for message in self.messages]

    async def send_message(self, **kwargs: Any) -> None:
        self.messages.append(kwargs)

    async def send_photo(self, **kwargs: Any) -> None:
        self.photos.append(kwargs)

    async def send_video(self, **kwargs: Any) -> None:
        self.videos.append(kwargs)

    async def send_media_group(self, **kwargs: Any) -> None:
        self.media_groups.append(kwargs)

    async def delete_message(self, **kwargs: Any) -> None:
        self.deleted.append(kwargs)

    async def edit_message_text(self, **kwargs: Any) -> None:
        self.edited.append(kwargs)


class RaisingBot(FakeBot):
    """A bot whose first ``send_message`` raises, to drive error handling."""

    def __init__(self, error: BaseException, raises: int = 1) -> None:
        super().__init__()
        self._error = error
        self._remaining = raises

    async def send_message(self, **kwargs: Any) -> None:
        if self._remaining > 0:
            self._remaining -= 1
            raise self._error
        await super().send_message(**kwargs)


if TYPE_CHECKING:
    # Type-checked so the doubles cannot drift from the protocols they stand
    # in for; a fake that no longer matches would otherwise pass silently.
    _chat_repository: ChatRepository = InMemoryChatRepository()
    _post_repository: PostRepository = InMemoryPostRepository()
