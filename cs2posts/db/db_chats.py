from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

from .db_sqlite import SQLite
from cs2posts.dto import Chat


class ChatDatabase(SQLite):

    def __init__(self, filepath: Path | None) -> None:
        super().__init__(filepath)

    async def create_table(self) -> None:
        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute("""
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
            await conn.commit()

    async def save(self, chat: Chat) -> None:
        if chat is None:
            return

        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO chats (
                    chat_id,
                    chat_id_admin,
                    strikes,
                    is_running,
                    is_banned,
                    is_removed_while_banned,
                    is_news_interested,
                    is_update_interested,
                    is_external_news_interested,
                    last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat.chat_id,
                chat.chat_id_admin,
                chat.strikes,
                chat.is_running,
                chat.is_banned,
                chat.is_removed_while_banned,
                chat.is_news_interested,
                chat.is_update_interested,
                chat.is_external_news_interested,
                chat.last_activity.isoformat()
            ))
            await conn.commit()

    async def load(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def is_empty(self) -> bool:
        return await super().is_empty("chats")

    async def get(self, chat_id: int) -> Chat | None:
        if not await self.exists(chat_id):
            return None

        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE chat_id = ?
            """, (chat_id,)) as cursor:
                return Chat.from_json(dict(await cursor.fetchone()))

    async def add(self, chat: Chat) -> Chat:
        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute("""
                INSERT INTO chats (
                    chat_id,
                    chat_id_admin,
                    strikes,
                    is_running,
                    is_banned,
                    is_removed_while_banned,
                    is_news_interested,
                    is_update_interested,
                    is_external_news_interested,
                    last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat.chat_id,
                chat.chat_id_admin,
                chat.strikes,
                chat.is_running,
                chat.is_banned,
                chat.is_removed_while_banned,
                chat.is_news_interested,
                chat.is_update_interested,
                chat.is_external_news_interested,
                chat.last_activity.isoformat()
            ))
            await conn.commit()
        return chat

    async def remove(self, chat: Chat) -> None:
        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute("""
                DELETE FROM chats WHERE chat_id = ?
            """, (chat.chat_id,))
            await conn.commit()

    async def update(self, chat: Chat) -> None:
        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute("""
                UPDATE chats SET
                    chat_id_admin = ?,
                    strikes = ?,
                    is_running = ?,
                    is_banned = ?,
                    is_removed_while_banned = ?,
                    is_news_interested = ?,
                    is_update_interested = ?,
                    is_external_news_interested = ?,
                    last_activity = ?
                WHERE chat_id = ?
            """, (
                chat.chat_id_admin,
                chat.strikes,
                chat.is_running,
                chat.is_banned,
                chat.is_removed_while_banned,
                chat.is_news_interested,
                chat.is_update_interested,
                chat.is_external_news_interested,
                chat.last_activity.isoformat(),
                chat.chat_id
            ))
            await conn.commit()

    async def import_from_json(self, filepath: Path) -> None:
        await self.create_table()

        with open(filepath, encoding='utf-8') as fs:
            chats = json.load(fs)

        # Backwards compatibility from old .json format
        if chats.get('chats') is not None:
            chats = chats['chats']

        for chat in chats:
            await self.add(Chat.from_json(chat))

    async def exists(self, chat_id: Chat) -> bool:
        async with aiosqlite.connect(self.filepath) as conn:
            async with conn.execute("""
                SELECT COUNT(*) FROM chats WHERE chat_id = ?
            """, (chat_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] == 1

    async def migrate(self, chat: Chat, new_chat_id: int) -> Chat:
        await self.remove(chat)
        chat.chat_id = new_chat_id
        await self.add(chat)
        return chat

    async def get_running_chats(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE is_running = 1
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def get_interested_in_news_chats(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE is_news_interested = 1
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def get_interested_in_updates_chats(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE is_update_interested = 1
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def get_interested_in_external_news_chats(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE is_external_news_interested = 1
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def get_running_and_interested_in_news_chats(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE is_running = 1 AND is_news_interested = 1
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def get_running_and_interested_in_updates_chats(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE is_running = 1 AND is_update_interested = 1
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def get_running_and_interested_in_external_news_chats(self) -> list[Chat]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM chats WHERE is_running = 1 AND is_external_news_interested = 1
            """) as cursor:
                return [Chat.from_json(dict(row)) for row in await cursor.fetchall()]

    async def contains(self, chat: Chat) -> bool:
        async with aiosqlite.connect(self.filepath) as conn:
            async with conn.execute("""
                SELECT COUNT(*) FROM chats WHERE chat_id = ?
            """, (chat.chat_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] == 1

    async def size(self) -> int:
        async with aiosqlite.connect(self.filepath) as conn:
            async with conn.execute("""
                SELECT COUNT(*) FROM chats
            """) as cursor:
                return (await cursor.fetchone())[0]
