from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

import pytest
import pytest_asyncio

from cs2posts.clock import UTC
from cs2posts.db import SqliteChatRepository
from cs2posts.dto import Chat
from cs2posts.dto.post import PostType


def _as_json_dict(chat: Chat) -> dict:
    data = asdict(chat)
    data["last_activity"] = chat.last_activity.isoformat()
    return data


@pytest_asyncio.fixture
async def repository(tmp_path):
    repository = SqliteChatRepository.at(tmp_path / "chats.db")
    await repository.setup()
    return repository


@pytest_asyncio.fixture
async def populated(repository):
    for chat in (Chat(1337), Chat(42)):
        await repository.save(chat)
    return repository


@pytest.mark.asyncio
async def test_a_new_repository_is_empty(repository):
    assert await repository.is_empty()
    assert await repository.size() == 0


@pytest.mark.asyncio
async def test_saved_chats_can_be_loaded_back(populated):
    chats = await populated.load()

    assert {chat.chat_id for chat in chats} == {1337, 42}
    assert not await populated.is_empty()


@pytest.mark.asyncio
async def test_get_returns_none_for_an_unknown_chat(populated):
    assert await populated.get(1337) is not None
    assert await populated.get(43) is None


@pytest.mark.asyncio
async def test_add_then_get_round_trips_the_chat(repository):
    chat = Chat(1337, chat_id_admin=99, strikes=2, is_running=True)

    await repository.add(chat)

    assert await repository.get(1337) == chat


@pytest.mark.asyncio
async def test_last_activity_round_trips_as_utc(repository):
    moment = datetime(2024, 5, 23, 12, 30, tzinfo=UTC)
    await repository.add(Chat(1337, last_activity=moment))

    stored = await repository.get(1337)

    assert stored is not None
    assert stored.last_activity == moment
    assert stored.last_activity.tzinfo is not None


@pytest.mark.asyncio
async def test_rows_written_before_timezones_are_read_as_utc(repository):
    await repository.add(Chat(1337))
    # Simulate a legacy row: a naive ISO timestamp with no offset.
    await repository._db.execute(
        "UPDATE chats SET last_activity = ? WHERE chat_id = ?",
        ("2024-05-23T12:30:00", 1337),
    )

    stored = await repository.get(1337)

    assert stored is not None
    assert stored.last_activity == datetime(2024, 5, 23, 12, 30, tzinfo=UTC)


@pytest.mark.asyncio
async def test_remove_deletes_the_chat(repository):
    chat = Chat(1337)
    await repository.add(chat)

    await repository.remove(chat)

    assert await repository.get(1337) is None


@pytest.mark.asyncio
async def test_update_persists_changed_fields(repository):
    chat = Chat(1337)
    await repository.add(chat)

    chat.strikes = 3
    chat.is_banned = True
    await repository.update(chat)

    stored = await repository.get(1337)
    assert stored is not None
    assert stored.strikes == 3
    assert stored.is_banned


@pytest.mark.asyncio
async def test_migrate_moves_the_chat_to_its_new_id(repository):
    chat = Chat(1337, chat_id_admin=7)
    await repository.add(chat)

    migrated = await repository.migrate(chat, 42)

    assert await repository.get(1337) is None
    assert await repository.get(42) == migrated
    assert migrated.chat_id_admin == 7


@pytest.mark.asyncio
async def test_save_overwrites_an_existing_chat(repository):
    await repository.save(Chat(1337, strikes=1))
    await repository.save(Chat(1337, strikes=2))

    stored = await repository.get(1337)
    assert stored is not None
    assert stored.strikes == 2
    assert await repository.size() == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("post_type", list(PostType))
async def test_running_chats_interested_in_filters_on_both_flags(repository, post_type):
    interested = Chat(1, is_running=True)
    not_running = Chat(2, is_running=False)
    uninterested = Chat(3, is_running=True)
    uninterested.set_interest(post_type, False)

    for chat in (interested, not_running, uninterested):
        await repository.save(chat)

    chats = await repository.running_chats_interested_in(post_type)

    assert [chat.chat_id for chat in chats] == [1]


@pytest.mark.asyncio
async def test_contains_and_exists_agree(populated):
    assert await populated.contains(Chat(1337))
    assert await populated.exists(42)
    assert not await populated.contains(Chat(43))


@pytest.mark.asyncio
async def test_size_tracks_additions_and_removals(populated):
    assert await populated.size() == 2

    chat = Chat(43)
    await populated.add(chat)
    assert await populated.size() == 3

    await populated.remove(chat)
    assert await populated.size() == 2


@pytest.mark.asyncio
async def test_import_from_json_accepts_the_legacy_wrapped_format(repository, tmp_path):
    payload = {"chats": [_as_json_dict(Chat(1337)), _as_json_dict(Chat(42))]}
    json_file = tmp_path / "chats.json"
    json_file.write_text(json.dumps(payload), encoding="utf-8")

    await repository.import_from_json(json_file)

    assert {chat.chat_id for chat in await repository.load()} == {1337, 42}


@pytest.mark.asyncio
async def test_import_from_json_accepts_a_bare_list(repository, tmp_path):
    json_file = tmp_path / "chats.json"
    json_file.write_text(json.dumps([_as_json_dict(Chat(7))]), encoding="utf-8")

    await repository.import_from_json(json_file)

    assert {chat.chat_id for chat in await repository.load()} == {7}


@pytest.mark.asyncio
async def test_migrate_onto_an_existing_id_keeps_the_chat(repository):
    """Regression: migrate deleted the old row and then failed to insert the
    new one, so a migration Telegram reported twice lost the chat entirely."""
    await repository.add(Chat(1337, chat_id_admin=7))
    await repository.add(Chat(42, chat_id_admin=99))

    migrated = await repository.migrate(await repository.get(1337), 42)

    assert await repository.get(1337) is None
    stored = await repository.get(42)
    assert stored is not None
    assert stored.chat_id_admin == 7
    assert migrated.chat_id == 42


@pytest.mark.asyncio
async def test_migrating_a_chat_to_its_own_id_is_a_no_op(repository):
    await repository.add(Chat(1337, chat_id_admin=7))

    await repository.migrate(await repository.get(1337), 1337)

    stored = await repository.get(1337)
    assert stored is not None
    assert stored.chat_id_admin == 7


@pytest.mark.asyncio
async def test_import_from_json_can_run_over_a_populated_database(repository, tmp_path):
    """Regression: the import used a bare INSERT, so re-importing a snapshot
    aborted on the first chat that already existed."""
    await repository.add(Chat(1337, chat_id_admin=7))
    json_file = tmp_path / "chats.json"
    json_file.write_text(
        json.dumps([_as_json_dict(Chat(1337, chat_id_admin=1234))]), encoding="utf-8"
    )

    await repository.import_from_json(json_file)

    stored = await repository.get(1337)
    assert stored is not None
    assert stored.chat_id_admin == 1234


@pytest.mark.asyncio
async def test_import_from_json_rejects_a_non_list_payload(repository, tmp_path):
    json_file = tmp_path / "chats.json"
    json_file.write_text(json.dumps({"nope": 1}), encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a list of chats"):
        await repository.import_from_json(json_file)
