from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import aiosqlite

from .db import Database


class SQLite(Database):

    def __init__(self, filepath: Path | None) -> None:
        if filepath is None:
            filepath = Path(__file__).parent.parent.parent / "database"
            filepath.mkdir(parents=True, exist_ok=True)
            filepath /= "sqlite.db"

        super().__init__(filepath)

    async def _execute(self, query: str, params: Sequence[Any] = ()) -> None:
        async with aiosqlite.connect(self.filepath) as conn:
            await conn.execute(query, params)
            await conn.commit()

    async def _fetch_all(self, query: str, params: Sequence[Any] = ()) -> list[aiosqlite.Row]:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                return list(await cursor.fetchall())

    async def _fetch_one(self, query: str, params: Sequence[Any] = ()) -> aiosqlite.Row | None:
        async with aiosqlite.connect(self.filepath) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchone()

    async def _scalar(self, query: str, params: Sequence[Any] = ()) -> Any:
        async with aiosqlite.connect(self.filepath) as conn:
            async with conn.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return row[0] if row is not None else None

    async def is_empty(self, table_name: str) -> bool:
        count = await self._scalar(f"SELECT COUNT(*) FROM {table_name}")
        return count is None or count == 0

    async def create(self, *, overwrite: bool = False) -> None:
        if overwrite and self.filepath.exists():
            self.filepath.unlink()

        if self.filepath.exists():
            return

        async with aiosqlite.connect(self.filepath):
            pass

    async def backup(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.filepath) as conn:
            async with aiosqlite.connect(filepath) as backup_conn:
                await conn.backup(backup_conn)
