from __future__ import annotations

import abc
import json
import logging
from pathlib import Path
from typing import Any

import aiosqlite

from cs2posts.bot.chats import Chat
from cs2posts.post import Post


logger = logging.getLogger(__name__)


class Database:

    def __init__(self, filepath: Path | None) -> None:
        self.__filepath = filepath

    @property
    def filepath(self) -> Path:
        return self.__filepath

    @abc.abstractmethod
    async def create(self, *, overwrite=False) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    async def save(self, data: Any) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    async def is_empty(self, table_name: str) -> bool:
        pass  # pragma: no cover


class SQLite(Database):

    def __init__(self, filepath: Path | None) -> None:
        if filepath is None:
            filepath = Path(__file__).parent.parent / "sqlite.db"

        super().__init__(filepath)

    async def is_empty(self, table_name: str) -> bool:
        async with aiosqlite.connect(self.filepath) as conn:
            async with conn.execute(f"""SELECT COUNT(*) FROM {table_name}""") as cursor:
                result = await cursor.fetchone()
                return result[0] == 0

    async def create(self, *, overwrite=False) -> None:
        if overwrite and self.filepath.exists():
            self.filepath.unlink()

        if self.filepath.exists():
            return

        async with aiosqlite.connect(self.filepath):
            pass


class PostDatabase(SQLite):

    def __init__(self, filepath: Path | None) -> None:
        super().__init__(filepath)

    async def create_table(self) -> None:
        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    gid TEXT PRIMARY KEY NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    is_external_url BOOLEAN NOT NULL,
                    author TEXT,
                    contents TEXT NOT NULL,
                    feedlabel TEXT NOT NULL,
                    date INTEGER NOT NULL,
                    feedname TEXT NOT NULL,
                    feed_type INTEGER NOT NULL,
                    appid INTEGER NOT NULL,
                    tags TEXT,
                    type TEXT NOT NULL
                )
            """)
            await conn.commit()

    async def save(self, post: Post) -> None:
        if post is None:
            return

        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO posts (
                    gid,
                    title,
                    url,
                    is_external_url,
                    author,
                    contents,
                    feedlabel,
                    date,
                    feedname,
                    feed_type,
                    appid,
                    tags,
                    type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post.gid,
                post.title,
                post.url,
                post.is_external_url,
                post.author,
                post.contents,
                post.feedlabel,
                post.date,
                post.feedname,
                post.feed_type,
                post.appid,
                json.dumps(post.tags),
                str(post.get_type())
            ))
            await conn.commit()

    async def load(self) -> list[Post]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM posts
            """) as cursor:
                return [await self._convert_row_to_post(row) for row in await cursor.fetchall()]

    async def _convert_row_to_post(self, row: aiosqlite.Row) -> Post:
        if row is None:
            return None
        data = dict(row)
        data.pop('type', None)
        data['tags'] = json.loads(data['tags'])
        return Post(**data)

    async def get_latest_news_post(self) -> Post | None:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM posts WHERE type = 'news' ORDER BY date DESC LIMIT 1
            """) as cursor:
                return await self._convert_row_to_post(await cursor.fetchone())

    async def get_latest_update_post(self) -> Post | None:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM posts WHERE type = 'update' ORDER BY date DESC LIMIT 1
            """) as cursor:
                return await self._convert_row_to_post(await cursor.fetchone())

    async def get_latest_external_post(self) -> Post | None:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM posts WHERE type = 'external' ORDER BY date DESC LIMIT 1
            """) as cursor:
                return await self._convert_row_to_post(await cursor.fetchone())

    async def get_latest_post(self) -> Post:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM posts ORDER BY date DESC LIMIT 1
            """) as cursor:
                return await self._convert_row_to_post(await cursor.fetchone())

    async def is_empty(self) -> bool:
        return await super().is_empty('posts')


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
