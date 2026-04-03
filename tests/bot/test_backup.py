from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from cs2posts.bot.backup import ChatDatabaseBackupManager


def test_create_timestamped_backup_filepath(tmp_path):
    manager = ChatDatabaseBackupManager(
        chat_db=AsyncMock(),
        backup_filepath=tmp_path / 'backup.db',
        max_backups=5,
    )

    backup_filepath = manager.create_timestamped_backup_filepath()

    assert backup_filepath.parent == tmp_path
    assert backup_filepath.name.startswith('backup_')
    assert backup_filepath.suffix == '.db'


def test_rotate_backups_removes_oldest_by_date(tmp_path):
    dates = ['20260401_120000', '20260402_120000', '20260403_120000', '20260404_120000', '20260405_120000']
    for date in dates:
        (tmp_path / f'backup_{date}.db').touch()

    manager = ChatDatabaseBackupManager(
        chat_db=AsyncMock(),
        backup_filepath=tmp_path / 'backup.db',
        max_backups=3,
    )

    manager.rotate_backups()
    remaining = sorted(tmp_path.glob('*.db'), key=lambda p: p.stem)

    assert len(remaining) == 3
    assert remaining[0].name == 'backup_20260403_120000.db'
    assert remaining[1].name == 'backup_20260404_120000.db'
    assert remaining[2].name == 'backup_20260405_120000.db'


def test_rotate_backups_no_removal_needed(tmp_path):
    dates = ['20260401_120000', '20260402_120000', '20260403_120000']
    for date in dates:
        (tmp_path / f'backup_{date}.db').touch()

    manager = ChatDatabaseBackupManager(
        chat_db=AsyncMock(),
        backup_filepath=tmp_path / 'backup.db',
        max_backups=5,
    )

    manager.rotate_backups()
    remaining = list(tmp_path.glob('*.db'))

    assert len(remaining) == 3


def test_rotate_backups_zero_max(tmp_path):
    dates = ['20260401_120000', '20260402_120000', '20260403_120000']
    for date in dates:
        (tmp_path / f'backup_{date}.db').touch()

    manager = ChatDatabaseBackupManager(
        chat_db=AsyncMock(),
        backup_filepath=tmp_path / 'backup.db',
        max_backups=0,
    )

    manager.rotate_backups()
    remaining = list(tmp_path.glob('*.db'))

    assert len(remaining) == 3


def test_rotate_backups_empty_dir(tmp_path):
    manager = ChatDatabaseBackupManager(
        chat_db=AsyncMock(),
        backup_filepath=tmp_path / 'backup.db',
        max_backups=5,
    )

    manager.rotate_backups()
    remaining = list(tmp_path.glob('*.db'))

    assert len(remaining) == 0


@pytest.mark.asyncio
async def test_backup_calls_database_with_timestamped_filepath(tmp_path):
    mocked_db = AsyncMock()
    manager = ChatDatabaseBackupManager(
        chat_db=mocked_db,
        backup_filepath=tmp_path / 'backup.db',
        max_backups=5,
    )

    with patch.object(manager, 'create_timestamped_backup_filepath', return_value=tmp_path / 'backup_20260403_120000.db'):
        backup_filepath = await manager.backup()

    mocked_db.backup.assert_called_once_with(tmp_path / 'backup_20260403_120000.db')
    assert backup_filepath == tmp_path / 'backup_20260403_120000.db'
