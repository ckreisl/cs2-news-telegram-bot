from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Protocol

from cs2posts.clock import UTC

logger = logging.getLogger(__name__)

DEFAULT_BACKUP_FILEPATH = Path(__file__).parent.parent.parent / "backups" / "backup.db"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


class BackupDatabase(Protocol):
    async def backup(self, filepath: Path) -> None: ...


class ChatDatabaseBackupManager:
    """Writes timestamped copies of the chat database and prunes old ones."""

    def __init__(
        self,
        chat_db: BackupDatabase,
        backup_filepath: Path | None = None,
        max_backups: int = 5,
    ) -> None:
        self._chat_db = chat_db
        self._backup_filepath = backup_filepath or DEFAULT_BACKUP_FILEPATH
        self._max_backups = max_backups

    @property
    def backup_filepath(self) -> Path:
        return self._backup_filepath

    @property
    def max_backups(self) -> int:
        return self._max_backups

    def create_timestamped_backup_filepath(self) -> Path:
        # UTC, not local time: ``rotate_backups`` orders backups by sorting
        # these names, and a DST rollback would make local timestamps sort
        # out of chronological order and prune the wrong file.
        timestamp = datetime.now(tz=UTC).strftime(TIMESTAMP_FORMAT)
        filepath = self.backup_filepath
        return filepath.with_stem(f"{filepath.stem}_{timestamp}")

    async def backup(self) -> Path:
        backup_filepath = self.create_timestamped_backup_filepath()
        await self._chat_db.backup(backup_filepath)
        return backup_filepath

    def rotate_backups(self) -> None:
        if self.max_backups <= 0:
            return

        filepath = self.backup_filepath
        pattern = f"{filepath.stem}_*{filepath.suffix}"
        backups = sorted(filepath.parent.glob(pattern), key=lambda path: path.stem)

        while len(backups) > self.max_backups:
            backups.pop(0).unlink()

    async def run(self) -> Path:
        backup_filepath = await self.backup()
        logger.info("Created backup: %s", backup_filepath)
        self.rotate_backups()
        return backup_filepath
