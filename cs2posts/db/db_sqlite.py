from __future__ import annotations

from pathlib import Path

import aiosqlite

from .db import Database


class SQLite(Database):

    def __init__(self, filepath: Path | None) -> None:
        if filepath is None:
            filepath = Path(__file__).parent.parent / "database"
            filepath.mkdir(parents=True, exist_ok=True)
            filepath /= "sqlite.db"

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

    async def backup(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.filepath) as conn:
            async with aiosqlite.connect(filepath) as backup_conn:
                await conn.backup(backup_conn)
