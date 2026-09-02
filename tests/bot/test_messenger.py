from __future__ import annotations

import pytest
from telegram.error import BadRequest
from telegram.error import ChatMigrated
from telegram.error import Forbidden

from cs2posts.bot.messenger import ChatMessenger
from cs2posts.dto.chats import Chat
from tests.fakes import FakeBot
from tests.fakes import InMemoryChatRepository


class RecordingMessage:
    """A Sendable that records deliveries, and can fail a given number of times."""

    def __init__(self, error: BaseException | None = None, failures: int = 0) -> None:
        self.error = error
        self.failures = failures
        self.sent_to: list[int] = []

    async def send(self, bot, chat_id: int) -> None:
        if self.error is not None and self.failures > 0:
            self.failures -= 1
            raise self.error
        self.sent_to.append(chat_id)


@pytest.fixture
def chat():
    return Chat(chat_id=1337)


@pytest.fixture
def chat_db(chat):
    return InMemoryChatRepository([chat])


@pytest.fixture
def messenger(chat_db):
    return ChatMessenger(chat_db)


@pytest.fixture
def bot():
    return FakeBot()


@pytest.mark.asyncio
async def test_a_message_reaches_the_chat(messenger, bot, chat):
    message = RecordingMessage()

    assert await messenger.send(bot, message, chat) is True
    assert message.sent_to == [1337]


@pytest.mark.asyncio
async def test_sending_to_no_chat_is_reported_not_raised(messenger, bot, caplog):
    assert await messenger.send(bot, RecordingMessage(), None) is False
    assert "No chat to send to" in caplog.text


@pytest.mark.asyncio
async def test_a_deleted_chat_is_removed_from_storage(messenger, bot, chat, chat_db):
    message = RecordingMessage(BadRequest("Chat not found"), failures=1)

    assert await messenger.send(bot, message, chat) is False
    assert await chat_db.get(1337) is None


@pytest.mark.asyncio
async def test_another_bad_request_keeps_the_chat(messenger, bot, chat, chat_db):
    message = RecordingMessage(BadRequest("Message is too long"), failures=1)

    assert await messenger.send(bot, message, chat) is False
    assert await chat_db.get(1337) is not None


@pytest.mark.asyncio
async def test_being_blocked_removes_the_chat(messenger, bot, chat, chat_db):
    message = RecordingMessage(Forbidden("bot was blocked by the user"), failures=1)

    assert await messenger.send(bot, message, chat) is False
    assert await chat_db.get(1337) is None


@pytest.mark.asyncio
async def test_a_migrated_chat_is_updated_and_the_message_resent(
    messenger, bot, chat, chat_db
):
    message = RecordingMessage(ChatMigrated(new_chat_id=-100), failures=1)

    assert await messenger.send(bot, message, chat) is True
    assert await chat_db.get(1337) is None
    assert await chat_db.get(-100) is not None
    assert message.sent_to == [-100]


@pytest.mark.asyncio
async def test_repeated_migrations_give_up_instead_of_recursing(
    messenger, bot, chat, caplog
):
    """A migration loop must not walk the bot off the stack."""
    message = RecordingMessage(ChatMigrated(new_chat_id=-100), failures=99)

    assert await messenger.send(bot, message, chat) is False
    assert "Giving up" in caplog.text
