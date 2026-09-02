from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import aiosqlite

DEFAULT_DATABASE_DIR = Path(__file__).parent.parent.parent / "database"
DEFAULT_DATABASE_FILE = "sqlite.db"


def default_database_filepath() -> Path:
    DEFAULT_DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DATABASE_DIR / DEFAULT_DATABASE_FILE


class SqliteDatabase:
    """A sqlite file plus the small query helpers the repositories share.

    Repositories *hold* one of these rather than inherit from it: a chat
    repository is not a kind of database, and the previous inheritance forced
    subclasses to widen ``is_empty``'s signature and ignore its argument.
    """

    def __init__(self, filepath: Path | None = None) -> None:
        self._filepath = (
            filepath if filepath is not None else default_database_filepath()
        )

    @property
    def filepath(self) -> Path:
        return self._filepath

    async def create(self, *, overwrite: bool = False) -> None:
        if overwrite and self._filepath.exists():
            self._filepath.unlink()

        if self._filepath.exists():
            return

        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._filepath):
            pass

    async def execute(self, query: str, params: Sequence[Any] = ()) -> None:
        async with aiosqlite.connect(self._filepath) as conn:
            await conn.execute(query, params)
            await conn.commit()

    async def fetch_all(
        self, query: str, params: Sequence[Any] = ()
    ) -> list[aiosqlite.Row]:
        async with aiosqlite.connect(self._filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                return list(await cursor.fetchall())

    async def fetch_one(
        self, query: str, params: Sequence[Any] = ()
    ) -> aiosqlite.Row | None:
        async with aiosqlite.connect(self._filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchone()

    async def scalar(self, query: str, params: Sequence[Any] = ()) -> Any:
        async with (
            aiosqlite.connect(self._filepath) as conn,
            conn.execute(query, params) as cursor,
        ):
            row = await cursor.fetchone()
            return row[0] if row is not None else None

    async def count(self, table_name: str) -> int:
        count = await self.scalar(f"SELECT COUNT(*) FROM {table_name}")
        return int(count) if count is not None else 0

    async def backup(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        async with (
            aiosqlite.connect(self._filepath) as conn,
            aiosqlite.connect(filepath) as backup_conn,
        ):
            await conn.backup(backup_conn)
