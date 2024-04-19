from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from cs2posts.bot.constants import TELEGRAM_MAX_MESSAGE_LENGTH
from cs2posts.bot.message import CounterStrikeNewsMessage
from cs2posts.bot.message import CounterStrikeUpdateMessage
from cs2posts.bot.message import ImageContainer
from cs2posts.bot.message import TelegramMessage
from cs2posts.bot.message import TelegramMessageFactory
from cs2posts.post import Post


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


def test_telegram_message_msg_not_split():
    telegram_msg = TelegramMessage("Hello World")
    assert telegram_msg.message == "Hello World"
    assert telegram_msg.messages == ["Hello World"]


def test_telegram_message_msg_split():
    telegram_msg = TelegramMessage("foo bar\n" * 600)
    assert len(telegram_msg.message) > TELEGRAM_MAX_MESSAGE_LENGTH
    assert len(telegram_msg.messages) == 2


def test_image_container_is_empty(mocked_cs2_news_post):
    mocked_cs2_news_post.contents = "There is no image in this post."
    img = ImageContainer(mocked_cs2_news_post)
    assert img.is_empty() is True
    assert img.caption is None


def test_image_container_is_valid(mocked_cs2_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        img = ImageContainer(mocked_cs2_news_post)

        assert img.is_valid() is True
        mocked_get.assert_called_once_with("https://example.com/image.jpg")


def test_image_container_is_not_valid(mocked_cs2_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = False
        img = ImageContainer(mocked_cs2_news_post)

        assert img.is_valid() is False
        mocked_get.assert_called_once_with("https://example.com/image.jpg")

        mocked_get.side_effect = Exception
        assert img.is_valid() is False

        mocked_cs2_news_post.body = "[img]example.com/image.jpg[/img]"
        img = ImageContainer(mocked_cs2_news_post)
        assert img.is_valid() is False

        mocked_cs2_news_post.body = "Is empty"
        img = ImageContainer(mocked_cs2_news_post)
        assert img.is_valid() is False


def test_image_container_caption(mocked_cs2_news_post):
    img = ImageContainer(mocked_cs2_news_post)
    expected = "<b>Some News</b> (2009-02-13 23:31:30)"
    assert img.caption == expected


def test_counter_strike_news_message_no_image(mocked_cs2_news_post):
    mocked_cs2_news_post.contents = "This is a test message."
    msg = CounterStrikeNewsMessage(post=mocked_cs2_news_post)
    expected = "<b>Some News</b>\n(2009-02-13 23:31:30)\n\nThis is a test message.\n\n(Author: Valve)\n\nSource: <a href='https://www.counter-strike.net/newsentry/1338'>https://www.counter-strike.net/newsentry/1338</a>"
    assert len(msg.messages) == 1
    assert msg.message == expected


def test_counter_strike_news_message_with_image(mocked_cs2_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        msg = CounterStrikeNewsMessage(post=mocked_cs2_news_post)
        expected = "\nThis is a test message.\n\n(Author: Valve)\n\nSource: <a href='https://www.counter-strike.net/newsentry/1338'>https://www.counter-strike.net/newsentry/1338</a>"

        assert len(msg.messages) == 1
        assert msg.message == expected


def test_counter_strike_update_message(mocked_cs2_update_post):
    mocked_cs2_update_post.body = "[ UI ]\n[list]\n[*]Fixed cases where there was a visible delay loading map images in the Play menu\n[*]Fixed a bug where items that can't be equipped were visible in the Loadout menu\n[*]Fixed a bug where loadout items couldn't be unequipped\n[*]Fixed a bug where loadout changes weren't saved if the game was quit shortly after making changes\n[*]Fixed a bug where loadout changes on the main menu character were delayed\n[/list]\n[ MISC ]\n[list]\n[*]Fixed some visual issues with demo playback\n[*]Fixed an issue where animations would not play back correctly in a CSTV broadcast\n[*]Adjusted wear values of some community stickers to better match CS:GO\n[/list]\n[ MAPS ]\n[i]Ancient:[/i][list]\n[*]Added simplified grenade collisions to corner trims and central pillar on B site\n[/list]\n[i]Anubis:[/i][list]\n[*]Adjusted clipping at A site steps between Walkway and Heaven\n[/list]"
    msg = CounterStrikeUpdateMessage(post=mocked_cs2_update_post)
    expected = "<b>Release Notes for 2/13/2009</b>\n(2009-02-13 23:31:30)\n\nmy content(Author: Valve)\n\nSource: <a href='https://test.com'>https://test.com</a>"

    assert len(msg.messages) == 1
    assert msg.message == expected


def test_telegram_message_factory(mocked_cs2_news_post, mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        msg = TelegramMessageFactory.create(mocked_cs2_news_post)
        assert isinstance(msg, CounterStrikeNewsMessage)

    msg = TelegramMessageFactory.create(mocked_cs2_update_post)
    assert isinstance(msg, CounterStrikeUpdateMessage)

    # TODO: We consider everything as news if not Release or patchnotes in tags is given
    """
    with pytest.raises(ValueError):
        TelegramMessageFactory.create(mocked_cs2_news_post)
    """


@pytest.mark.asyncio
async def test_telegram_message_send_news(mocked_cs2_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        msg = TelegramMessageFactory.create(mocked_cs2_news_post)

        mocked_bot = AsyncMock()
        await msg.send(bot=mocked_bot, chat_id=1337)

        assert mocked_bot.send_photo.called
        assert mocked_bot.send_message.called


@pytest.mark.asyncio
async def test_telegram_message_send_update(mocked_cs2_update_post):
    msg = TelegramMessageFactory.create(mocked_cs2_update_post)
    mocked_bot = AsyncMock()

    await msg.send(bot=mocked_bot, chat_id=1337)

    assert mocked_bot.send_photo.not_called
    assert mocked_bot.send_message.called
