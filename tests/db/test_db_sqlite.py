from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cs2posts.db import SQLite


@pytest.mark.asyncio
@patch('aiosqlite.connect')
async def test_sqlite_class_create_db_exists(sqlite_mock):
    mocked_path = Mock()
    mocked_path.exists.return_value = True
    db = SQLite(mocked_path)
    sqlite_mock.assert_not_called()
    await db.create()
    sqlite_mock.assert_not_called()


@pytest.mark.asyncio
@patch('aiosqlite.connect')
async def test_sqlite_class_create_db_exists_overwrite(sqlite_mock):
    mocked_path = Mock()
    mocked_path.exists.side_effect = [True, False]
    db = SQLite(mocked_path)

    sqlite_mock.__aenter__.return_value.execute = AsyncMock()
    sqlite_mock.__aexit__ = AsyncMock()

    await db.create(overwrite=True)
    mocked_path.unlink.assert_called_once()
    sqlite_mock.assert_called_once_with(mocked_path)


@pytest.mark.asyncio
async def test_sqlite_class_backup(tmp_path):
    db = SQLite(tmp_path / 'test.db')
    await db.backup(tmp_path / 'test_backup.db')
    assert Path(tmp_path / 'test_backup.db').exists()
