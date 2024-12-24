from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from cs2posts.dto.post import Post
from cs2posts.msg import CounterStrikeExternalMessage
from cs2posts.msg import CounterStrikeNewsMessage
from cs2posts.msg import CounterStrikeUpdateMessage
from cs2posts.msg import TelegramMessage
from cs2posts.msg import TelegramMessageFactory
from cs2posts.msg.constants import TELEGRAM_MAX_MESSAGE_LENGTH


@pytest.fixture
def mocked_cs2_update_post():
    return Post(gid="1337",
                title="Release Notes for 2/13/2009",
                url="https://test.com",
                is_external_url=True,
                author="Valve",
                contents="my content",
                date=1234567890,
                feedlabel="feedlabel",
                feedname="feedname",
                feed_type=1,
                appid=730,
                tags=["patchnotes"])


@pytest.fixture
def mocked_cs2_news_post():
    return Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="[img]https://example.com/image.jpg[/img]\nThis is a test message.",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)


@pytest.fixture
def mocked_cs2_external_news():
    return Post(
        gid="1339",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1339",
        author="",
        contents="<a href='https://example.com'>Link</a> External News",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=0,
        appid=730)


def test_telegram_message_msg_not_split():
    telegram_msg = TelegramMessage("Hello World")
    assert telegram_msg.message == "Hello World"
    assert telegram_msg.messages == ["Hello World"]


def test_telegram_message_msg_split():
    telegram_msg = TelegramMessage("foo bar\n" * 600)
    assert len(telegram_msg.message) > TELEGRAM_MAX_MESSAGE_LENGTH
    assert len(telegram_msg.messages) == 2


# TODO: Add test for CounterStrikeNewsMessage


def test_counter_strike_update_message(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        mocked_cs2_update_post.body = "[ UI ]\n[list]\n[*]Fixed cases where there was a visible delay loading map images in the Play menu\n[*]Fixed a bug where items that can't be equipped were visible in the Loadout menu\n[*]Fixed a bug where loadout items couldn't be unequipped\n[*]Fixed a bug where loadout changes weren't saved if the game was quit shortly after making changes\n[*]Fixed a bug where loadout changes on the main menu character were delayed\n[/list]\n[ MISC ]\n[list]\n[*]Fixed some visual issues with demo playback\n[*]Fixed an issue where animations would not play back correctly in a CSTV broadcast\n[*]Adjusted wear values of some community stickers to better match CS:GO\n[/list]\n[ MAPS ]\n[i]Ancient:[/i][list]\n[*]Added simplified grenade collisions to corner trims and central pillar on B site\n[/list]\n[i]Anubis:[/i][list]\n[*]Adjusted clipping at A site steps between Walkway and Heaven\n[/list]"
        msg = CounterStrikeUpdateMessage(post=mocked_cs2_update_post)
        expected = "<b>Release Notes for 2/13/2009</b>\n(2009-02-13 23:31:30)\n\nmy content\n\n(Author: Valve)\n\nSource: <a href='https://test.com'>Link</a>"
        assert len(msg.messages) == 1
        assert msg.message == expected


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
async def test_telegram_message_send_news(mocked_cs2_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        msg = await TelegramMessageFactory.create(mocked_cs2_news_post)

        mocked_bot = AsyncMock()
        await msg.send(bot=mocked_bot, chat_id=1337)

        assert mocked_bot.send_photo.called
        assert mocked_bot.send_message.called


@pytest.mark.asyncio
async def test_telegram_message_send_update(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        msg = await TelegramMessageFactory.create(mocked_cs2_update_post)
        mocked_bot = AsyncMock()

    await msg.send(bot=mocked_bot, chat_id=1337)

    mocked_bot.send_photo.assert_not_called()
    mocked_bot.send_message.assert_called()
