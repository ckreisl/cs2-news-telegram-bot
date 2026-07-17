from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from cs2posts.content.content import Image
from cs2posts.content.content import TextBlock
from cs2posts.msg import CounterStrikeUpdateMessage
from cs2posts.msg import create_message


def test_counter_strike_update_message(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        msg = CounterStrikeUpdateMessage(post=mocked_cs2_update_post)

    expected = "<b>Release Notes for 2/13/2009</b>\n(2009-02-13 23:31:30)\n\nmy content\n\n(Author: Valve)\n\nSource: <a href='https://test.com'>Link</a>"
    assert len(msg.content) == 1
    assert isinstance(msg.content[0], TextBlock)
    assert msg.content[0].text == expected


def test_counter_strike_update_message_formats_headings(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        mocked_cs2_update_post.contents = "[ MISC ]\n[list]\n[*]Fixed some visual issues with demo playback\n[/list]"
        msg = CounterStrikeUpdateMessage(post=mocked_cs2_update_post)

    assert len(msg.content) == 1
    assert isinstance(msg.content[0], TextBlock)
    assert "<b>[ MISC ]</b>" in msg.content[0].text
    assert "• Fixed some visual issues with demo playback" in msg.content[0].text


def test_counter_strike_update_message_with_image(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        mocked_cs2_update_post.contents = (
            "[ MISC ]\n"
            "Select the appropriate option using the Workshop Tool:\n\n"
            "[img]https://example.com/image.png[/img]\n"
            "We're excited to see your submissions!")
        msg = CounterStrikeUpdateMessage(post=mocked_cs2_update_post)

    images = [c for c in msg.content if isinstance(c, Image)]
    assert len(images) == 1
    assert "https://example.com/image.png" in images[0].url

    # The image tag must not leak into any text block
    for content in msg.content:
        if isinstance(content, TextBlock):
            assert "[img]" not in content.text
            assert "[/img]" not in content.text


@pytest.mark.asyncio
async def test_telegram_message_send_update(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        msg = await create_message(mocked_cs2_update_post)
        mocked_bot = AsyncMock()

    await msg.send(bot=mocked_bot, chat_id=1337)

    mocked_bot.send_photo.assert_not_called()
    mocked_bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_telegram_message_send_update_with_image(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        mocked_cs2_update_post.contents = (
            "[ MISC ]\n"
            "Select the appropriate option using the Workshop Tool:\n\n"
            "[img]https://example.com/image.png[/img]\n"
            "We're excited to see your submissions!")
        msg = await create_message(mocked_cs2_update_post)

    mocked_bot = AsyncMock()
    with patch('cs2posts.msg.cs_news_msg.is_valid_url', return_value=True):
        await msg.send(bot=mocked_bot, chat_id=1337)

    mocked_bot.send_photo.assert_called_once()
    call_kwargs = mocked_bot.send_photo.call_args[1]
    assert call_kwargs['photo'] == "https://example.com/image.png"
    # Header and body are sent as regular messages
    assert mocked_bot.send_message.call_count == 2
