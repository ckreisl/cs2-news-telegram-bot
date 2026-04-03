from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from cs2posts.msg import CounterStrikeExternalMessage
from cs2posts.msg import CounterStrikeNewsMessage
from cs2posts.msg import CounterStrikeUpdateMessage
from cs2posts.msg import TelegramMessage
from cs2posts.msg import TelegramMessageFactory
from cs2posts.msg.constants import TELEGRAM_MAX_MESSAGE_LENGTH
from cs2posts.msg.constants import TELEGRAM_SEND_DELAY_SECONDS


def test_telegram_message_msg_not_split():
    telegram_msg = TelegramMessage("Hello World")
    assert telegram_msg.message == "Hello World"
    assert telegram_msg.messages == ["Hello World"]


def test_telegram_message_msg_split():
    telegram_msg = TelegramMessage("foo bar\n" * 600)
    assert len(telegram_msg.message) > TELEGRAM_MAX_MESSAGE_LENGTH
    assert len(telegram_msg.messages) == 2


@pytest.mark.asyncio
async def test_telegram_message_factory(mocked_cs2_news_post, mocked_cs2_update_post, mocked_cs2_external_news):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        msg = await TelegramMessageFactory.create(mocked_cs2_news_post)
        assert isinstance(msg, CounterStrikeNewsMessage)

        msg = await TelegramMessageFactory.create(mocked_cs2_update_post)
        assert isinstance(msg, CounterStrikeUpdateMessage)

        msg = await TelegramMessageFactory.create(mocked_cs2_external_news)
        assert isinstance(msg, CounterStrikeExternalMessage)


@pytest.mark.asyncio
async def test_telegram_message_factory_raises_for_unknown_post_type(mocked_cs2_update_post):
    with patch.object(mocked_cs2_update_post, 'is_news', return_value=False), \
            patch.object(mocked_cs2_update_post, 'is_update', return_value=False), \
            patch.object(mocked_cs2_update_post, 'is_external', return_value=False):
        with pytest.raises(ValueError, match="Unknown post type"):
            await TelegramMessageFactory.create(mocked_cs2_update_post)


@pytest.mark.asyncio
async def test_telegram_message_send_news(mocked_cs2_news_post):
    with patch('requests.get') as mocked_get, \
            patch('cs2posts.utils.Utils.is_valid_url', return_value=True):
        mocked_get.return_value.ok = True
        msg = await TelegramMessageFactory.create(mocked_cs2_news_post)

        mocked_bot = AsyncMock()
        await msg.send(bot=mocked_bot, chat_id=1337)

        assert mocked_bot.send_photo.called
        assert mocked_bot.send_message.called


@pytest.mark.asyncio
async def test_telegram_message_send_raises_on_chunk_failure():
    msg = TelegramMessage("hello")
    msg._TelegramMessage__messages = ["chunk1", "chunk2", "chunk3"]

    bot = AsyncMock()
    bot.send_message.side_effect = [None, RuntimeError("network error"), None]

    with pytest.raises(RuntimeError, match="network error"):
        await msg.send(bot=bot, chat_id=42)

    assert bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_telegram_message_send_uses_configured_delay_between_chunks():
    msg = TelegramMessage("hello")
    msg._TelegramMessage__messages = ["chunk1", "chunk2", "chunk3"]

    bot = AsyncMock()

    with patch('cs2posts.msg.telegram.asyncio.sleep', new=AsyncMock()) as mocked_sleep:
        await msg.send(bot=bot, chat_id=42)

    assert mocked_sleep.await_count == 2
    mocked_sleep.assert_any_await(TELEGRAM_SEND_DELAY_SECONDS)
