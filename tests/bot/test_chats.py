from __future__ import annotations

import pytest

from cs2posts.bot.chats import Chat
from cs2posts.bot.chats import Chats


@pytest.fixture
def chats():
    return Chats(chats=[Chat(1), Chat(2), Chat(3)])


def test_chats_contains(chats):
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
