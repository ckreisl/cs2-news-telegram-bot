from __future__ import annotations

import json
from pathlib import Path

from .db_sqlite import SQLite
from cs2posts.dto import Chat


class ChatDatabase(SQLite):

    def __init__(self, filepath: Path | None) -> None:
        super().__init__(filepath)

    COLUMNS = (
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

    def _row_values(self, chat: Chat) -> tuple:
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

    async def create_table(self) -> None:
        await self._execute("""
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
        """)

    async def _insert(self, chat: Chat, *, replace: bool) -> None:
        verb = "INSERT OR REPLACE" if replace else "INSERT"
        columns = ", ".join(self.COLUMNS)
        placeholders = ", ".join("?" * len(self.COLUMNS))
        await self._execute(
            f"{verb} INTO chats ({columns}) VALUES ({placeholders})",
            self._row_values(chat))

    async def save(self, chat: Chat) -> None:
        if chat is None:
            return
        await self._insert(chat, replace=True)

    async def _query_chats(self, where: str = "", params: tuple = ()) -> list[Chat]:
        query = "SELECT * FROM chats"
        if where:
            query += f" WHERE {where}"
        return [Chat.from_dict(dict(row)) for row in await self._fetch_all(query, params)]

    async def load(self) -> list[Chat]:
        return await self._query_chats()

    async def is_empty(self, table_name: str | None = None) -> bool:
        return await super().is_empty("chats")

    async def get(self, chat_id: int) -> Chat | None:
        row = await self._fetch_one(
            "SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
        return Chat.from_dict(dict(row)) if row is not None else None

    async def add(self, chat: Chat) -> Chat:
        await self._insert(chat, replace=False)
        return chat

    async def remove(self, chat: Chat) -> None:
        await self._execute(
            "DELETE FROM chats WHERE chat_id = ?", (chat.chat_id,))

    async def update(self, chat: Chat) -> None:
        assignments = ", ".join(f"{col} = ?" for col in self.COLUMNS if col != "chat_id")
        values = self._row_values(chat)[1:] + (chat.chat_id,)
        await self._execute(
            f"UPDATE chats SET {assignments} WHERE chat_id = ?", values)

    async def import_from_json(self, filepath: Path) -> None:
        await self.create_table()

        with open(filepath, encoding='utf-8') as fs:
            chats = json.load(fs)

        # Backwards compatibility from old .json format
        if chats.get('chats') is not None:
            chats = chats['chats']

        for chat in chats:
            await self.add(Chat.from_dict(chat))

    async def exists(self, chat_id: int) -> bool:
        count = await self._scalar(
            "SELECT COUNT(*) FROM chats WHERE chat_id = ?", (chat_id,))
        return count == 1

    async def migrate(self, chat: Chat, new_chat_id: int) -> Chat:
        await self.remove(chat)
        chat.chat_id = new_chat_id
        await self.add(chat)
        return chat

    async def get_running_chats(self) -> list[Chat]:
        return await self._query_chats("is_running = 1")

    async def get_interested_in_news_chats(self) -> list[Chat]:
        return await self._query_chats("is_news_interested = 1")

    async def get_interested_in_updates_chats(self) -> list[Chat]:
        return await self._query_chats("is_update_interested = 1")

    async def get_interested_in_external_news_chats(self) -> list[Chat]:
        return await self._query_chats("is_external_news_interested = 1")

    async def get_running_and_interested_in_news_chats(self) -> list[Chat]:
        return await self._query_chats("is_running = 1 AND is_news_interested = 1")

    async def get_running_and_interested_in_updates_chats(self) -> list[Chat]:
        return await self._query_chats("is_running = 1 AND is_update_interested = 1")

    async def get_running_and_interested_in_external_news_chats(self) -> list[Chat]:
        return await self._query_chats("is_running = 1 AND is_external_news_interested = 1")

    async def contains(self, chat: Chat) -> bool:
        return await self.exists(chat.chat_id)

    async def size(self) -> int:
        count = await self._scalar("SELECT COUNT(*) FROM chats")
        return count if count is not None else 0
