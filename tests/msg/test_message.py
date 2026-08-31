from __future__ import annotations

import pytest

from cs2posts.msg import CounterStrikeExternalMessage
from cs2posts.msg import CounterStrikeNewsMessage
from cs2posts.msg import CounterStrikeUpdateMessage
from cs2posts.msg import Sendable
from cs2posts.msg import TelegramMessage
from cs2posts.msg import create_message
from cs2posts.msg import split_text
from cs2posts.msg.constants import TELEGRAM_MAX_MESSAGE_LENGTH
from cs2posts.msg.constants import TELEGRAM_SEND_DELAY_SECONDS
from tests.fakes import FakeBot


def test_telegram_message_msg_not_split():
    telegram_msg = TelegramMessage("Hello World")
    assert telegram_msg.message == "Hello World"
    assert telegram_msg.messages == ["Hello World"]


def test_telegram_message_msg_split():
    telegram_msg = TelegramMessage("foo bar\n" * 600)
    assert len(telegram_msg.message) > TELEGRAM_MAX_MESSAGE_LENGTH
    assert len(telegram_msg.messages) == 2


def test_telegram_message_hard_splits_overlong_single_line():
    # A single line with no newlines that exceeds the limit must still be
    # broken up, otherwise Telegram rejects the whole message.
    long_line = "x" * (TELEGRAM_MAX_MESSAGE_LENGTH * 2 + 100)
    telegram_msg = TelegramMessage(long_line)

    assert len(telegram_msg.messages) == 3
    assert all(
        len(chunk) <= TELEGRAM_MAX_MESSAGE_LENGTH for chunk in telegram_msg.messages
    )
    assert "".join(telegram_msg.messages).strip() == long_line


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fixture_name", "expected"),
    [
        ("mocked_cs2_news_post", CounterStrikeNewsMessage),
        ("mocked_cs2_update_post", CounterStrikeUpdateMessage),
        ("mocked_cs2_external_news", CounterStrikeExternalMessage),
    ],
)
async def test_the_factory_picks_a_renderer_per_post_type(
    request, fixture_name, expected
):
    post = request.getfixturevalue(fixture_name)

    assert isinstance(await create_message(post), expected)


@pytest.mark.asyncio
async def test_every_post_type_has_a_renderer():
    from cs2posts.dto.post import PostType
    from cs2posts.msg.factory import MESSAGE_BY_POST_TYPE

    assert set(MESSAGE_BY_POST_TYPE) == set(PostType)


@pytest.mark.asyncio
async def test_a_news_post_sends_its_media_and_its_prose(
    mocked_cs2_news_post, fast_sleep
):
    message = await create_message(mocked_cs2_news_post)
    bot = FakeBot()

    await message.send(bot, chat_id=1337)

    assert bot.photos
    assert bot.messages


@pytest.mark.asyncio
async def test_a_failing_chunk_stops_a_plain_text_message(fast_sleep):
    message = TelegramMessage("chunk1\nchunk2")
    bot = FakeBot()
    sent = []

    async def failing(**kwargs):
        sent.append(kwargs)
        raise RuntimeError("network error")

    bot.send_message = failing

    with pytest.raises(RuntimeError, match="network error"):
        await message.send(bot, chat_id=42)

    assert len(sent) == 1


@pytest.mark.asyncio
async def test_chunks_are_paced_but_the_last_one_is_not(monkeypatch):
    import asyncio

    delays = []

    async def record(delay):
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", record)

    message = TelegramMessage("x")
    message._messages = ["chunk1", "chunk2", "chunk3"]

    await message.send(FakeBot(), chat_id=42)

    assert delays == [TELEGRAM_SEND_DELAY_SECONDS, TELEGRAM_SEND_DELAY_SECONDS]


def test_split_text_is_available_on_its_own():
    assert split_text("short") == ["short"]
    assert len(split_text("line\n" * 2000)) > 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fixture_name",
    ["mocked_cs2_news_post", "mocked_cs2_update_post", "mocked_cs2_external_news"],
)
async def test_every_message_type_honours_the_sendable_contract(
    request, fixture_name, fast_sleep
):
    """Regression: CounterStrikeNewsMessage inherited from TelegramMessage but
    never called ``super().__init__``, so ``message``/``messages`` raised
    AttributeError on every news and update post."""
    post = request.getfixturevalue(fixture_name)
    message = await create_message(post)

    assert isinstance(message, Sendable)

    bot = FakeBot()
    await message.send(bot, chat_id=1337)

    assert bot.messages or bot.photos or bot.videos or bot.media_groups
