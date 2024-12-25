from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

from .db_sqlite import SQLite
from cs2posts.dto import Post


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

    async def is_empty(self) -> bool:
        return await super().is_empty('posts')

    async def import_from_json(self, filepath: Path) -> None:
        await self.create_table()

        with open(filepath, encoding='utf-8') as fs:
            posts = json.load(fs)

        # Backwards compatibility from old .json format
        if posts.get('news') is not None:
            await self.save(Post.from_json(posts['news']))
        if posts.get('update') is not None:
            await self.save(Post.from_json(posts['update']))
        if posts.get('external') is not None:
            await self.save(Post.from_json(posts['external']))

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

    async def get_post_by_gid(self, gid: str) -> Post | None:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM posts WHERE gid = ?
            """, (gid,)) as cursor:
                return await self._convert_row_to_post(await cursor.fetchone())
