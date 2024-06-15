from __future__ import annotations

import abc
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

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
    def create(self, *, overwrite=False) -> None:
        pass

    @abc.abstractmethod
    def save(self, data: Any) -> None:
        pass

    @abc.abstractmethod
    def is_empty(self, table_name: str) -> bool:
        pass


class SQLite(Database):

    def __init__(self, filepath: Path | None) -> None:
        if filepath is None:
            filepath = Path(__file__).parent.parent / "sqlite.db"

        super().__init__(filepath)
        self.create()

    def is_empty(self, table_name: str) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {table_name}
            """)
            return cursor.fetchone()[0] == 0

    def create(self, *, overwrite=False) -> None:
        if overwrite and self.filepath.exists():
            self.filepath.unlink()

        if self.filepath.exists():
            return

        with sqlite3.connect(self.filepath):
            pass


class PostDatabase(SQLite):

    def __init__(self, filepath: Path | None) -> None:
        super().__init__(filepath)
        self.create_table()

    def create_table(self) -> None:
        with sqlite3.connect(self.filepath) as conn:
            conn.execute("""
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
            conn.commit()

    def save(self, post: Post) -> None:
        with sqlite3.connect(self.filepath) as conn:
            conn.execute("""
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
            conn.commit()

    def _convert_row_to_post(self, row: sqlite3.Row) -> Post:
        if row is None:
            return None
        data = dict(row)
        data.pop('type', None)
        data['tags'] = json.loads(data['tags'])
        return Post(**data)

    def get_latest_news_post(self) -> Post | None:
        with sqlite3.connect(self.filepath) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM posts WHERE type = 'news' ORDER BY date DESC LIMIT 1
            """)
            return self._convert_row_to_post(cursor.fetchone())

    def get_latest_update_post(self) -> Post | None:
        with sqlite3.connect(self.filepath) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM posts WHERE type = 'update' ORDER BY date DESC LIMIT 1
            """)
        return self._convert_row_to_post(cursor.fetchone())

    def get_latest_external_post(self) -> Post | None:
        with sqlite3.connect(self.filepath) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM posts WHERE type = 'external' ORDER BY date DESC LIMIT 1
            """)
            return self._convert_row_to_post(cursor.fetchone())

    def get_latest_post(self) -> Post:
        with sqlite3.connect(self.filepath) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM posts ORDER BY date DESC LIMIT 1
            """)
            return self._convert_row_to_post(cursor.fetchone())

    def is_empty(self) -> bool:
        return super().is_empty('posts')


class ChatDatabase(SQLite):

    def __init__(self, filepath: Path | None) -> None:
        super().__init__(filepath)
        self.create_table()

    def create_table(self) -> None:
        with sqlite3.connect(self.filepath) as conn:
            conn.execute("""
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
            conn.commit()

    def save(self, chat: Chat) -> None:
        with sqlite3.connect(self.filepath) as conn:
            conn.execute("""
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
            conn.commit()

    def load(self) -> list[Chat]:
        with sqlite3.connect(self.filepath) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM chats
            """)
            return [Chat.from_json(dict(row)) for row in cursor.fetchall()]

    def is_empty(self, table_name: str) -> bool:
        return super().is_empty(table_name)
