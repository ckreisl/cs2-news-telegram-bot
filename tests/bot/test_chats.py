from __future__ import annotations

import pytest

from cs2posts.bot.chats import Chat
from cs2posts.bot.chats import Chats


@pytest.fixture
def chats():
    return Chats(chats=[Chat(1), Chat(2), Chat(3)])


def test_chats_contains(chats):
    assert chats.contains(chat_id=1) is True
    assert Chat(1) in chats
    assert Chat(4) not in chats


def test_chats_iter(chats):
    assert list(chats) == chats.chats


def test_chats_add(chats):
    chat = Chat(4)
    chats.add(chat=chat)
    assert chat in chats


def test_chats_remove(chats):
    chat = Chat(2)
    chats.remove(chat=chat)
    assert chat not in chats


def test_chats_get_by_id(chats):
    assert chats.get(chat_id=1) == Chat(1)
    assert chats.get(chat_id=4) is None


def test_chats_create(chats):
    chat = chats.create(chat_id=4)
    assert isinstance(chat, Chat)
    assert chat.chat_id == 4


def test_chats_update(chats):
    chat = chats.get(chat_id=2)
    assert chat.is_running is False
    assert chat.is_banned is False

    chat = Chat(2, is_running=True, is_banned=True)
    chats.update(chat=chat)
    assert chat.is_running is True
    assert chat.is_banned is True


def test_chats_create_and_add(chats):
    chat = chats.create_and_add(chat_id=4)
    assert chat in chats


def test_chats_get_running_chats(chats):
    assert chats.get_running_chats() == []
    chat = chats.get(chat_id=1)
    chat.is_running = True
    assert chats.get_running_chats() == [chat]


def test_chats_get_interested_in_news(chats):
    assert len(chats.get_interested_in_news()) == len(chats)
    chat = chats.get(chat_id=1)
    chat.is_news_interested = False
    assert len(chats.get_interested_in_news()) == len(chats) - 1


def test_chats_get_interested_in_updates(chats):
    assert len(chats.get_interested_in_updates()) == len(chats)
    chat = chats.get(chat_id=1)
    chat.is_update_interested = False
    assert len(chats.get_interested_in_updates()) == len(chats) - 1
