from __future__ import annotations

import pytest
import pytest_asyncio

from cs2posts.db import ChatDatabase
from cs2posts.dto import Chat


@pytest.fixture
def data_chats():
    return {"chats": [Chat(1337), Chat(42)]}


@pytest_asyncio.fixture
async def chats_empty_database(tmp_path):
    filepath = tmp_path / "test_chats.db"
    db = ChatDatabase(filepath)
    await db.create_table()
    yield db


@pytest_asyncio.fixture
async def chats_database(chats_empty_database, data_chats):
    for chat in data_chats["chats"]:
        await chats_empty_database.save(chat)

    yield chats_empty_database


@pytest.mark.asyncio
async def test_database_is_empty(chats_empty_database):
    is_empty_chat = await chats_empty_database.is_empty()
    assert is_empty_chat


@pytest.mark.asyncio
async def test_database_is_not_empty(chats_database):
    chat_db_empty = await chats_database.is_empty()
    assert not chat_db_empty


@pytest.mark.asyncio
async def test_chats_database_load(chats_database):
    chats = await chats_database.load()
    assert isinstance(chats, list)
    assert len(chats) == 2
    assert Chat(1337) in chats
    assert Chat(42) in chats


@pytest.mark.asyncio
async def test_chats_database_get(chats_database):
    chat = await chats_database.get(1337)
    assert chat.chat_id == 1337
    assert chat.strikes == 0
    assert not chat.is_banned
    chat = await chats_database.get(43)
    assert chat is None


@pytest.mark.asyncio
async def test_chats_database_add(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    actual_chat = await chats_empty_database.get(1337)
    assert actual_chat == chat


@pytest.mark.asyncio
async def test_chats_database_remove(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    assert await chats_empty_database.get(1337) == chat
    await chats_empty_database.remove(chat)
    assert await chats_empty_database.get(1337) is None


@pytest.mark.asyncio
async def test_chats_database_update(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    assert chat.strikes == 0
    chat.strikes = 3
    await chats_empty_database.update(chat)
    actual_chat = await chats_empty_database.get(1337)
    assert actual_chat.strikes == 3


@pytest.mark.asyncio
async def test_chats_database_migrate(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    assert await chats_empty_database.get(1337) == chat
    chat = await chats_empty_database.migrate(chat, 42)
    assert await chats_empty_database.get(1337) is None
    assert await chats_empty_database.get(42) == chat


@pytest.mark.asyncio
async def test_chats_database_save(chats_empty_database):
    assert await chats_empty_database.load() == []
    await chats_empty_database.save(None)
    assert await chats_empty_database.load() == []

    expected_chats = [Chat(41), Chat(1338)]
    for chat in expected_chats:
        await chats_empty_database.save(chat=chat)
    actual_chats = await chats_empty_database.load()

    assert len(expected_chats) == len(actual_chats)
    assert actual_chats == expected_chats


@pytest.mark.asyncio
async def test_chats_database_get_running_chats(chats_database):
    chat = await chats_database.get(1337)
    assert not chat.is_running
    chat.is_running = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_chats()) == 1
    acutal_running_chats = await chats_database.get_running_chats()
    assert acutal_running_chats[0] == chat


@pytest.mark.asyncio
async def test_chats_database_interested_in_news(chats_database):
    assert len(await chats_database.get_interested_in_news_chats()) == 2
    chat = await chats_database.get(1337)
    chat.is_news_interested = False
    await chats_database.update(chat)
    assert len(await chats_database.get_interested_in_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_interested_in_updates(chats_database):
    assert len(await chats_database.get_interested_in_updates_chats()) == 2
    chat = await chats_database.get(1337)
    chat.is_update_interested = False
    await chats_database.update(chat)
    assert len(await chats_database.get_interested_in_updates_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_interested_in_external_news(chats_database):
    assert len(await chats_database.get_interested_in_external_news_chats()) == 2
    chat = await chats_database.get(1337)
    chat.is_external_news_interested = False
    await chats_database.update(chat)
    assert len(await chats_database.get_interested_in_external_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_get_running_and_interested_in_news_chats(chats_database):
    assert len(await chats_database.get_running_and_interested_in_news_chats()) == 0
    chat = await chats_database.get(1337)
    chat.is_running = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_and_interested_in_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_get_running_and_interested_in_updates_chats(chats_database):
    assert len(await chats_database.get_running_and_interested_in_updates_chats()) == 0
    chat = await chats_database.get(1337)
    chat.is_running = True
    chat.is_update_interested = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_and_interested_in_updates_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_get_running_and_interested_in_external_news_chats(chats_database):
    assert len(await chats_database.get_running_and_interested_in_external_news_chats()) == 0
    chat = await chats_database.get(1337)
    chat.is_running = True
    chat.is_external_news_interested = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_and_interested_in_external_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_contains(chats_database):
    assert await chats_database.contains(Chat(1337))
    assert not await chats_database.contains(Chat(43))
    assert await chats_database.contains(Chat(42))


@pytest.mark.asyncio
async def test_chat_database_len(chats_database):
    assert await chats_database.size() == 2
    chat = Chat(43)
    await chats_database.add(chat)
    assert await chats_database.size() == 3
    await chats_database.remove(chat)
    assert await chats_database.size() == 2
