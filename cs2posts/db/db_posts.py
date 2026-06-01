from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

from .db_sqlite import SQLite
from cs2posts.dto import Post


class PostDatabase(SQLite):

    async def create_table(self) -> None:
        await self._execute("""
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

    async def save(self, post: Post | None) -> None:
        if post is None:
            return

        await self._execute("""
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

    async def load(self) -> list[Post]:
        rows = await self._fetch_all("SELECT * FROM posts")
        posts = [self._convert_row_to_post(row) for row in rows]
        return [post for post in posts if post is not None]

    async def is_empty(self, table_name: str | None = None) -> bool:
        return await super().is_empty('posts')

    async def import_from_json(self, filepath: Path) -> None:
        await self.create_table()

        with open(filepath, encoding='utf-8') as fs:
            posts = json.load(fs)

        # Backwards compatibility from old .json format
        if posts.get('news') is not None:
            await self.save(Post.from_dict(posts['news']))
        if posts.get('update') is not None:
            await self.save(Post.from_dict(posts['update']))
        if posts.get('external') is not None:
            await self.save(Post.from_dict(posts['external']))

    def _convert_row_to_post(self, row: aiosqlite.Row | None) -> Post | None:
        if row is None:
            return None
        data = dict(row)
        data.pop('type', None)
        data['tags'] = json.loads(data['tags'])
        return Post(**data)

    async def _get_latest(self, post_type: str | None = None) -> Post | None:
        if post_type is None:
            row = await self._fetch_one(
                "SELECT * FROM posts ORDER BY date DESC LIMIT 1")
        else:
            row = await self._fetch_one(
                "SELECT * FROM posts WHERE type = ? ORDER BY date DESC LIMIT 1",
                (post_type,))
        return self._convert_row_to_post(row)

    async def get_latest_news_post(self) -> Post | None:
        return await self._get_latest('news')

    async def get_latest_update_post(self) -> Post | None:
        return await self._get_latest('update')

    async def get_latest_external_post(self) -> Post | None:
        return await self._get_latest('external')

    async def get_latest_post(self) -> Post | None:
        return await self._get_latest()

    async def get_post_by_gid(self, gid: str) -> Post | None:
        row = await self._fetch_one(
            "SELECT * FROM posts WHERE gid = ?", (gid,))
        return self._convert_row_to_post(row)
