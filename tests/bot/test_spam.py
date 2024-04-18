from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

from cs2posts.bot import settings
from cs2posts.bot.chats import Chat
from cs2posts.bot.spam import SpamProtector
from cs2posts.bot.spam import SpamProtectorMessages


@pytest.fixture
def chat():
    return Chat(chat_id=1337)


@pytest.fixture
def spam_protector():
    return SpamProtector()


def get_utc_now():
    return datetime.now(tz=ZoneInfo('UTC')).replace(tzinfo=None)


def test_spam_protector_messages_warning(chat: Chat):
    chat.strikes = 1
    max_strikes = 3
    expected = "<b>Spamming</b> bot results in Timeout <b>(1/3)</b>."
    assert SpamProtectorMessages.warning(chat, max_strikes) == expected


def test_spam_protector_messages_banned(chat: Chat):
    chat.strikes = 3
    timout = 180
    max_strikes = 3
    expected = "<b>Strike (3/3)</b> Chat is now <b>banned</b> for spamming (Timeout: 3 mins)."
    assert SpamProtectorMessages.banned(chat, timout, max_strikes) == expected


def test_spam_protector_init(spam_protector):
    assert spam_protector.MAX_STRIKES == settings.CHAT_MAX_STRIKES
    assert spam_protector.BAN_TIMEOUT == settings.CHAT_BAN_TIMEOUT_SECONDS


def test_spam_protector_update_chat_activity(spam_protector, chat):
    spam_protector.update_chat_activity(chat)
    assert chat.last_activity is not None


def test_spam_protector_increase_strike_level(spam_protector, chat):
    spam_protector.increase_strike_level(chat)
    assert chat.strikes == 1
    spam_protector.increase_strike_level(chat)
    assert chat.strikes == 2
    spam_protector.increase_strike_level(chat)
    assert chat.strikes == 3
    spam_protector.increase_strike_level(chat)
    assert chat.strikes == 3


def test_spam_protector_reduce_strike_level(spam_protector, chat):
    chat.strikes = 3
    spam_protector.reduce_strike_level(chat)
    assert chat.strikes == 2
    spam_protector.reduce_strike_level(chat)
    assert chat.strikes == 1
    spam_protector.reduce_strike_level(chat)
    assert chat.strikes == 0
    spam_protector.reduce_strike_level(chat)
    assert chat.strikes == 0


def test_spam_protector_is_spamming(spam_protector, chat):
    chat.last_activity = get_utc_now()
    assert spam_protector.is_spamming(chat)
    chat.last_activity = get_utc_now(
    ) - timedelta(milliseconds=settings.CHAT_SPAM_INTERVAL_MS + 1)
    assert spam_protector.is_spamming(chat) is False


def test_spam_protector_ban(spam_protector, chat):
    spam_protector.ban(chat)
    assert chat.is_banned


def test_spam_protector_unban(spam_protector, chat):
    chat.is_banned = True
    spam_protector.unban(chat)
    assert chat.is_banned is False


def test_spam_protector_is_banned(spam_protector, chat):
    chat.is_banned = True
    assert spam_protector.is_banned(chat)
    chat.is_banned = False
    assert spam_protector.is_banned(chat) is False


def test_spam_protector_is_timeouted(spam_protector, chat):
    chat.last_activity = get_utc_now()
    assert spam_protector.is_timeouted(chat)
    chat.last_activity = get_utc_now(
    ) - timedelta(seconds=settings.CHAT_BAN_TIMEOUT_SECONDS + 1)
    assert spam_protector.is_timeouted(chat) is False


@pytest.mark.asyncio
async def test_spam_protector_check(spam_protector, chat):
    mock_bot = AsyncMock()
    await spam_protector.check(mock_bot, None)

    chat.is_banned = True
    chat.last_activity = get_utc_now()
    await spam_protector.check(mock_bot, chat)

    chat.last_activity = get_utc_now(
    ) - timedelta(seconds=settings.CHAT_BAN_TIMEOUT_SECONDS + 1)
    await spam_protector.check(mock_bot, chat)
    chat.is_banned = False

    chat.last_activity = get_utc_now()
    chat.strikes = 3
    await spam_protector.check(mock_bot, chat)
    assert chat.is_banned


@pytest.mark.asyncio
async def test_spam_protector_strike(spam_protector, chat):
    chat.is_banned = True
    await spam_protector.strike(None, chat)
    assert chat.strikes == 0

    mock_bot = AsyncMock()
    chat.is_banned = False
    await spam_protector.strike(mock_bot, chat)
    assert chat.strikes == 1
    assert await mock_bot.send_message.called_once_with(
        chat.chat_id,
        SpamProtectorMessages.warning(chat, settings.CHAT_MAX_STRIKES))

    await spam_protector.strike(mock_bot, chat)
    assert chat.strikes == 2
    assert await mock_bot.send_message.called_once_with(
        chat.chat_id,
        SpamProtectorMessages.warning(chat, settings.CHAT_MAX_STRIKES))

    await spam_protector.strike(mock_bot, chat)
    assert chat.strikes == 3
    assert await mock_bot.send_message.called_once_with(
        chat.chat_id,
        SpamProtectorMessages.banned(chat, settings.CHAT_BAN_TIMEOUT_SECONDS, settings.CHAT_MAX_STRIKES))
    assert chat.is_banned
