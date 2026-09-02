from __future__ import annotations

import pytest

from cs2posts.db import SqliteDatabase


@pytest.mark.asyncio
async def test_create_makes_the_file(tmp_path):
    db = SqliteDatabase(tmp_path / "test.db")

    await db.create()

    assert db.filepath.exists()


@pytest.mark.asyncio
async def test_create_is_idempotent(tmp_path):
    db = SqliteDatabase(tmp_path / "test.db")
    await db.create()
    db.filepath.write_bytes(b"")
    marker = db.filepath.stat().st_mtime_ns

    await db.create()

    assert db.filepath.stat().st_mtime_ns == marker


@pytest.mark.asyncio
async def test_create_with_overwrite_replaces_an_existing_file(tmp_path):
    db = SqliteDatabase(tmp_path / "test.db")
    await db.create()
    await db.execute("CREATE TABLE t (id INTEGER)")
    await db.execute("INSERT INTO t VALUES (1)")

    await db.create(overwrite=True)

    assert await db.count("sqlite_master") == 0


@pytest.mark.asyncio
async def test_create_makes_missing_parent_directories(tmp_path):
    db = SqliteDatabase(tmp_path / "nested" / "deeper" / "test.db")

    await db.create()

    assert db.filepath.exists()


@pytest.mark.asyncio
async def test_count_reports_rows(tmp_path):
    db = SqliteDatabase(tmp_path / "test.db")
    await db.create()
    await db.execute("CREATE TABLE t (id INTEGER)")

    assert await db.count("t") == 0

    await db.execute("INSERT INTO t VALUES (?)", (1,))

    assert await db.count("t") == 1


@pytest.mark.asyncio
async def test_fetch_one_returns_none_when_empty(tmp_path):
    db = SqliteDatabase(tmp_path / "test.db")
    await db.create()
    await db.execute("CREATE TABLE t (id INTEGER)")

    assert await db.fetch_one("SELECT * FROM t") is None
    assert await db.fetch_all("SELECT * FROM t") == []
    assert await db.scalar("SELECT id FROM t") is None


@pytest.mark.asyncio
async def test_backup_writes_a_usable_copy(tmp_path):
    db = SqliteDatabase(tmp_path / "test.db")
    await db.create()
    await db.execute("CREATE TABLE t (id INTEGER)")
    await db.execute("INSERT INTO t VALUES (42)")

    backup_path = tmp_path / "backups" / "test_backup.db"
    await db.backup(backup_path)

    assert backup_path.exists()
    assert await SqliteDatabase(backup_path).scalar("SELECT id FROM t") == 42


@pytest.mark.asyncio
async def test_default_filepath_is_used_when_none_given():
    db = SqliteDatabase(None)

    assert db.filepath.name == "sqlite.db"
