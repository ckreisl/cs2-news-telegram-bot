from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from cs2posts.msg import CounterStrikeUpdateMessage
from cs2posts.msg import TelegramMessageFactory


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
async def test_telegram_message_send_update(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        msg = await TelegramMessageFactory.create(mocked_cs2_update_post)
        mocked_bot = AsyncMock()

    await msg.send(bot=mocked_bot, chat_id=1337)

    mocked_bot.send_photo.assert_not_called()
    mocked_bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_telegram_message_send_update_raises_on_chunk_failure(mocked_cs2_update_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        msg = await TelegramMessageFactory.create(mocked_cs2_update_post)

    msg._TelegramMessage__messages = ["chunk1", "chunk2"]

    bot = AsyncMock()
    bot.send_message.side_effect = [RuntimeError("fail"), None]

    with pytest.raises(RuntimeError, match="fail"):
        await msg.send(bot=bot, chat_id=42)

    assert bot.send_message.call_count == 1
