from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from cs2posts.dto import Chat
from cs2posts.dto.post import PostType
from .sqlite import SqliteDatabase

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY NOT NULL,
        chat_id_admin INTEGER NOT NULL,
        strikes INTEGER NOT NULL,
        is_running BOOLEAN NOT NULL,
        is_banned BOOLEAN NOT NULL,
        is_removed_while_banned BOOLEAN NOT NULL,
        is_news_interested BOOLEAN NOT NULL,
        is_update_interested BOOLEAN NOT NULL,
        is_external_news_interested BOOLEAN NOT NULL,
        last_activity TEXT NOT NULL
    )
"""


class SqliteChatRepository:
    """Chat storage backed by a sqlite file."""

    TABLE = "chats"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "chat_id",
        "chat_id_admin",
        "strikes",
        "is_running",
        "is_banned",
        "is_removed_while_banned",
        "is_news_interested",
        "is_update_interested",
        "is_external_news_interested",
        "last_activity",
    )

    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    @classmethod
    def at(cls, filepath: Path | None = None) -> SqliteChatRepository:
        return cls(SqliteDatabase(filepath))

    @property
    def filepath(self) -> Path:
        return self._db.filepath

    async def setup(self) -> None:
        await self._db.create()
        await self._db.execute(CREATE_TABLE)

    async def backup(self, filepath: Path) -> None:
        await self._db.backup(filepath)

    async def is_empty(self) -> bool:
        return await self._db.count(self.TABLE) == 0

    async def size(self) -> int:
        return await self._db.count(self.TABLE)

    def _row_values(self, chat: Chat) -> tuple[object, ...]:
        return (
            chat.chat_id,
            chat.chat_id_admin,
            chat.strikes,
            chat.is_running,
            chat.is_banned,
            chat.is_removed_while_banned,
            chat.is_news_interested,
            chat.is_update_interested,
            chat.is_external_news_interested,
            chat.last_activity.isoformat(),
        )

    async def _insert(self, chat: Chat, *, replace: bool) -> None:
        verb = "INSERT OR REPLACE" if replace else "INSERT"
        columns = ", ".join(self.COLUMNS)
        placeholders = ", ".join("?" * len(self.COLUMNS))
        await self._db.execute(
            f"{verb} INTO chats ({columns}) VALUES ({placeholders})",
            self._row_values(chat),
        )

    async def _query(self, where: str = "", params: tuple = ()) -> list[Chat]:
        query = "SELECT * FROM chats"
        if where:
            query += f" WHERE {where}"
        return [
            Chat.from_dict(dict(row)) for row in await self._db.fetch_all(query, params)
        ]

    async def load(self) -> list[Chat]:
        return await self._query()

    async def get(self, chat_id: int) -> Chat | None:
        row = await self._db.fetch_one(
            "SELECT * FROM chats WHERE chat_id = ?", (chat_id,)
        )
        return Chat.from_dict(dict(row)) if row is not None else None

    async def save(self, chat: Chat) -> None:
        await self._insert(chat, replace=True)

    async def add(self, chat: Chat) -> Chat:
        await self._insert(chat, replace=False)
        return chat

    async def remove(self, chat: Chat) -> None:
        await self.remove_by_id(chat.chat_id)

    async def remove_by_id(self, chat_id: int) -> None:
        await self._db.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))

    async def update(self, chat: Chat) -> None:
        assignments = ", ".join(
            f"{column} = ?" for column in self.COLUMNS if column != "chat_id"
        )
        values = (*self._row_values(chat)[1:], chat.chat_id)
        await self._db.execute(
            f"UPDATE chats SET {assignments} WHERE chat_id = ?", values
        )

    async def migrate(self, chat: Chat, new_chat_id: int) -> Chat:
        """Move ``chat`` to ``new_chat_id``.

        Telegram reports one migration twice -- as a service message and as a
        ``ChatMigrated`` error on the next send -- so this has to be safe to
        run again. The new row is written before the old one is dropped: the
        previous delete-then-INSERT lost the chat entirely whenever a row
        already sat at ``new_chat_id``, because the insert then failed with
        the old row already gone.
        """
        old_chat_id = chat.chat_id
        chat.chat_id = new_chat_id

        await self.save(chat)
        if old_chat_id != new_chat_id:
            await self.remove_by_id(old_chat_id)

        return chat

    async def exists(self, chat_id: int) -> bool:
        count = await self._db.scalar(
            "SELECT COUNT(*) FROM chats WHERE chat_id = ?", (chat_id,)
        )
        return bool(count == 1)

    async def contains(self, chat: Chat) -> bool:
        return await self.exists(chat.chat_id)

    async def running_chats_interested_in(self, post_type: PostType) -> list[Chat]:
        """Chats that are started and want this kind of post.

        One parameterised query replaces the six hand-written variants this
        class used to carry, so a new post type needs no new method here.
        """
        column = Chat.INTEREST_ATTRIBUTE[post_type]
        return await self._query(f"is_running = 1 AND {column} = 1")

    async def import_from_json(self, filepath: Path) -> None:
        await self.setup()

        chats = json.loads(filepath.read_text(encoding="utf-8"))

        # Backwards compatibility with the old .json format.
        if isinstance(chats, dict) and chats.get("chats") is not None:
            chats = chats["chats"]

        if not isinstance(chats, list):
            raise ValueError(
                f"Expected a list of chats in {filepath}, got {type(chats).__name__}"
            )

        # ``save`` rather than ``add``: re-importing a snapshot over a
        # populated database must refresh those chats, not abort on the first
        # one that already exists.
        for chat in chats:
            await self.save(Chat.from_dict(chat))
