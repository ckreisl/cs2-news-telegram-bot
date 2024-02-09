from __future__ import annotations

import json

import pytest

from cs2posts.bot.chats import Chat
from cs2posts.bot.chats import Chats
from cs2posts.store import LocalChatStore
from cs2posts.store import LocalLatestPostStore
from cs2posts.store import Post


@pytest.fixture
def data_latest():
    return {
        "update": {
            "gid": "12341122312",
            "posterid": "76561199571358539",
            "headline": "Release Notes for 1/4/2024",
            "posttime": 1704407492,
            "updatetime": 1704407760,
            "body": "fixture_body_update",
            "event_type": 12
        },
        "news": {
            "gid": "1234567890",
            "posterid": "76561197971400048",
            "headline": "A Call to Arms",
            "posttime": 1707265365,
            "updatetime": 1707347147,
            "body": "fixtre_body_news",
            "event_type": 13
        }
    }


@pytest.fixture
def local_latest_post_store(tmp_path, data_latest):
    filepath = tmp_path / "latest.json"

    with open(filepath, "w") as fs:
        json.dump(data_latest, fs)

    store = LocalLatestPostStore(filepath)
    yield store


@pytest.fixture
def data_chats():
    return {"chats": [Chat(1337).to_json(), Chat(42).to_json()]}


@pytest.fixture
def local_chat_store(tmp_path, data_chats):
    filepath = tmp_path / "chats.json"

    with open(filepath, "w") as fs:
        json.dump(data_chats, fs)

    store = LocalChatStore(filepath)
    yield store


def test_local_latest_post_store_load(local_latest_post_store, data_latest):
    content = local_latest_post_store.load()
    assert isinstance(content, dict)
    assert content == data_latest


def test_local_latest_post_store_save(local_latest_post_store, data_latest):
    expected_temp_update_title = data_latest["news"]["headline"]

    data_latest["update"]["headline"] = "New Update headline"
    data_latest["news"]["headline"] = "New News headline"

    actual_post_update = Post(**data_latest["update"])
    actual_post_news = Post(**data_latest["news"])

    local_latest_post_store.save(actual_post_update)
    content = local_latest_post_store.load()

    # News headline should not be changed
    assert content["news"]["headline"] == expected_temp_update_title
    assert content["update"]["headline"] == "New Update headline"

    local_latest_post_store.save(actual_post_news)

    content = local_latest_post_store.load()
    assert content["news"]["headline"] == "New News headline"


def test_local_latest_post_store_get_latest_news_post(local_latest_post_store, data_latest):
    actual_post = local_latest_post_store.get_latest_news_post()
    expected_post = Post(**data_latest["news"])
    assert actual_post == expected_post


def test_local_latest_post_store_get_latest_update_post(local_latest_post_store, data_latest):
    actual_post = local_latest_post_store.get_latest_update_post()
    expected_post = Post(**data_latest["update"])
    assert actual_post == expected_post


def test_local_chat_store_load(local_chat_store, data_chats):
    chats = local_chat_store.load()
    assert isinstance(chats, Chats)
    assert len(chats) == 2
    assert Chat(1337) in chats
    assert Chat(42) in chats


def test_local_chat_store_save(local_chat_store):
    chats = [Chat(41), Chat(1338)]
    chats_expected = Chats(chats=chats)
    local_chat_store.save(chats=chats_expected)
    actual_chats = local_chat_store.load()

    for chat in chats:
        assert chat in actual_chats
