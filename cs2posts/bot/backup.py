from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol


class BackupDatabase(Protocol):

    async def backup(self, filepath: Path) -> None:
        ...


class ChatDatabaseBackupManager:

    def __init__(
        self,
        chat_db: BackupDatabase,
        backup_filepath: str | Path | None,
        max_backups: int,
    ) -> None:
        self.__chat_db = chat_db
        self.__backup_filepath = backup_filepath
        self.__max_backups = max_backups

    @property
    def backup_filepath(self) -> Path:
        if self.__backup_filepath is None:
            return Path(__file__).parent.parent.parent / "backups" / "backup.db"
        return Path(self.__backup_filepath)

    @property
    def max_backups(self) -> int:
        return self.__max_backups

    def create_timestamped_backup_filepath(self) -> Path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.backup_filepath
        return filepath.with_stem(f"{filepath.stem}_{timestamp}")

    async def backup(self) -> Path:
        backup_filepath = self.create_timestamped_backup_filepath()
        await self.__chat_db.backup(backup_filepath)
        return backup_filepath

    def rotate_backups(self) -> None:
        if self.max_backups <= 0:
            return

        filepath = self.backup_filepath
        backup_glob = f"{filepath.stem}_*{filepath.suffix}"
        backups = sorted(filepath.parent.glob(backup_glob), key=lambda p: p.stem)

        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            oldest.unlink()
