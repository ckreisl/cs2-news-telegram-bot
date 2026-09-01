from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

import aiosqlite

from cs2posts.dto import Post
from cs2posts.dto.post import PostType
from .sqlite import SqliteDatabase

CREATE_TABLE = """
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
"""


class SqlitePostRepository:
    """Post storage backed by a sqlite file.

    ``type`` is denormalised from ``Post.type`` so "newest post of this kind"
    stays a single indexed query; it is recomputed on every write and dropped
    on read, so the column can never drift from the classification rules.
    """

    TABLE = "posts"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "gid",
        "title",
        "url",
        "is_external_url",
        "author",
        "contents",
        "feedlabel",
        "date",
        "feedname",
        "feed_type",
        "appid",
        "tags",
        "type",
    )

    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    @classmethod
    def at(cls, filepath: Path | None = None) -> SqlitePostRepository:
        return cls(SqliteDatabase(filepath))

    @property
    def filepath(self) -> Path:
        return self._db.filepath

    async def setup(self) -> None:
        await self._db.create()
        await self._db.execute(CREATE_TABLE)

    async def is_empty(self) -> bool:
        return await self._db.count(self.TABLE) == 0

    async def save(self, post: Post) -> None:
        placeholders = ", ".join("?" * len(self.COLUMNS))
        await self._db.execute(
            f"INSERT OR REPLACE INTO posts ({', '.join(self.COLUMNS)})"
            f" VALUES ({placeholders})",
            (
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
                str(post.type),
            ),
        )

    def _to_post(self, row: aiosqlite.Row | None) -> Post | None:
        if row is None:
            return None
        data = dict(row)
        data.pop("type", None)
        data["tags"] = json.loads(data["tags"])
        return Post(**data)

    async def load(self) -> list[Post]:
        rows = await self._db.fetch_all("SELECT * FROM posts")
        return [post for row in rows if (post := self._to_post(row)) is not None]

    async def latest(self, post_type: PostType | None = None) -> Post | None:
        """The newest stored post, optionally of one kind.

        Replaces the four ``get_latest_*_post`` methods this class carried.
        """
        if post_type is None:
            row = await self._db.fetch_one(
                "SELECT * FROM posts ORDER BY date DESC LIMIT 1"
            )
        else:
            row = await self._db.fetch_one(
                "SELECT * FROM posts WHERE type = ? ORDER BY date DESC LIMIT 1",
                (str(post_type),),
            )
        return self._to_post(row)

    async def get_by_gid(self, gid: str) -> Post | None:
        row = await self._db.fetch_one("SELECT * FROM posts WHERE gid = ?", (gid,))
        return self._to_post(row)

    async def import_from_json(self, filepath: Path) -> None:
        await self.setup()

        posts = json.loads(filepath.read_text(encoding="utf-8"))

        # Backwards compatibility with the old .json format: a mapping of post
        # type to post. Raise ValueError rather than letting ``.get`` blow up
        # with AttributeError, which bootstrap does not catch and which would
        # therefore take the whole bot down over an unreadable snapshot.
        if not isinstance(posts, dict):
            raise ValueError(
                f"Expected a JSON object in {filepath}, got {type(posts).__name__}"
            )

        for key in ("news", "update", "external"):
            post = posts.get(key)
            if post is not None:
                await self.save(Post.from_dict(post))
