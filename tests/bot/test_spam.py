from __future__ import annotations

from datetime import timedelta

import pytest
from telegram.constants import ParseMode

from cs2posts.bot.spam import SpamProtector
from cs2posts.bot.spam import spam_banned_message
from cs2posts.bot.spam import spam_warning_message
from cs2posts.dto.chats import Chat
from tests.conftest import NOW
from tests.fakes import FakeBot


@pytest.fixture
def chat():
    # Last active long enough ago that the chat does not look like a spammer.
    return Chat(chat_id=1337, last_activity=NOW - timedelta(hours=2))


@pytest.fixture
def protector(settings, clock):
    return SpamProtector(settings, clock)


@pytest.fixture
def bot():
    return FakeBot()


def active_at(chat: Chat, ago: timedelta) -> None:
    chat.last_activity = NOW - ago


def test_warning_message_shows_the_strike_count(chat):
    chat.strikes = 1

    assert (
        spam_warning_message(chat, 3)
        == "<b>Spamming</b> bot results in Timeout <b>(1/3)</b>."
    )


def test_banned_message_shows_the_timeout_in_minutes(chat):
    chat.strikes = 3

    assert spam_banned_message(chat, 180, 3) == (
        "<b>Strike (3/3)</b> Chat is now <b>banned</b> for spamming (Timeout: 3 mins)."
    )


def test_thresholds_come_from_settings(settings, clock):
    protector = SpamProtector(settings, clock)

    assert protector.max_strikes == settings.max_strikes
    assert protector.ban_timeout_seconds == settings.ban_timeout_seconds


def test_update_chat_activity_records_the_current_time(protector, chat):
    protector.update_chat_activity(chat)

    assert chat.last_activity == NOW


def test_a_rapid_second_message_counts_as_spam(protector, chat, settings):
    active_at(chat, timedelta(milliseconds=settings.spam_interval_ms - 1))

    assert protector.is_spamming(chat)


def test_a_slow_second_message_does_not(protector, chat, settings):
    active_at(chat, timedelta(milliseconds=settings.spam_interval_ms + 1))

    assert not protector.is_spamming(chat)


def test_strikes_stop_at_the_maximum(protector, chat, settings):
    for _ in range(settings.max_strikes + 5):
        protector.increase_strike_level(chat)

    assert chat.strikes == settings.max_strikes


def test_strikes_never_go_negative(protector, chat):
    protector.reduce_strike_level(chat)

    assert chat.strikes == 0


@pytest.mark.asyncio
async def test_spamming_earns_a_warning(protector, chat, bot):
    active_at(chat, timedelta(0))

    await protector.check(bot, chat)

    assert chat.strikes == 1
    assert not chat.is_banned
    assert bot.texts == [spam_warning_message(chat, protector.max_strikes)]
    assert bot.messages[0]["parse_mode"] == ParseMode.HTML


@pytest.mark.asyncio
async def test_reaching_the_strike_limit_bans_the_chat(protector, chat, bot, settings):
    chat.strikes = settings.max_strikes - 1
    active_at(chat, timedelta(0))

    await protector.check(bot, chat)

    assert chat.is_banned
    assert chat.strikes == settings.max_strikes
    assert "banned" in bot.texts[0]


@pytest.mark.asyncio
async def test_a_banned_chat_is_ignored_during_its_timeout(protector, chat, bot):
    chat.is_banned = True
    active_at(chat, timedelta(seconds=1))

    await protector.check(bot, chat)

    assert chat.is_banned
    assert bot.messages == []


@pytest.mark.asyncio
async def test_serving_the_timeout_clears_the_ban_and_the_strikes(
    protector, chat, bot, settings
):
    chat.is_banned = True
    chat.strikes = settings.max_strikes
    active_at(chat, timedelta(seconds=settings.ban_timeout_seconds + 1))

    await protector.check(bot, chat)

    assert not chat.is_banned
    assert chat.strikes == 0
    assert bot.messages == []


@pytest.mark.asyncio
async def test_an_unbanned_chat_is_not_immediately_re_banned(
    protector, chat, bot, settings
):
    """Regression: strikes left at the maximum used to re-ban on the next message."""
    chat.is_banned = True
    chat.strikes = settings.max_strikes
    active_at(chat, timedelta(seconds=settings.ban_timeout_seconds + 1))
    await protector.check(bot, chat)

    # A second, fast message right after the unban.
    await protector.check(bot, chat)

    assert not chat.is_banned
    assert chat.strikes == 1


@pytest.mark.asyncio
async def test_inactivity_recovers_a_strike(protector, chat, bot, settings):
    chat.strikes = 2
    active_at(chat, timedelta(minutes=settings.strike_recovery_minutes + 1))

    await protector.check(bot, chat)

    assert chat.strikes == 1


@pytest.mark.asyncio
async def test_recovery_does_nothing_without_strikes(protector, chat, bot, settings):
    active_at(chat, timedelta(minutes=settings.strike_recovery_minutes + 1))

    await protector.check(bot, chat)

    assert chat.strikes == 0


@pytest.mark.asyncio
async def test_a_short_absence_does_not_recover_a_strike(
    protector, chat, bot, settings
):
    chat.strikes = 2
    active_at(chat, timedelta(minutes=settings.strike_recovery_minutes - 1))

    await protector.check(bot, chat)

    assert chat.strikes == 2


@pytest.mark.asyncio
async def test_checking_a_missing_chat_is_a_no_op(protector, bot):
    await protector.check(bot, None)

    assert bot.messages == []


@pytest.mark.asyncio
async def test_striking_an_already_banned_chat_sends_nothing(protector, chat, bot):
    chat.is_banned = True

    await protector.strike(bot, chat)

    assert bot.messages == []
    assert chat.strikes == 0


@pytest.mark.asyncio
async def test_every_check_refreshes_the_activity_timestamp(protector, chat, bot):
    active_at(chat, timedelta(hours=5))

    await protector.check(bot, chat)

    assert chat.last_activity == NOW
