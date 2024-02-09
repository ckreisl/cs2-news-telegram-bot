from __future__ import annotations

import pytest

from cs2posts.bot.message import CounterStrikeUpdateMessage
from cs2posts.post import Post


@pytest.fixture
def mocked_cs2_update_post():
    return Post(gid="1337",
                posterid="42",
                headline="Hello World",
                posttime=1234567890,
                updatetime=9876543210,
                body="This is a test message.",
                event_type=12)


def test_counter_strike_update_message(mocked_cs2_update_post):
    mocked_cs2_update_post.body = "[ UI ]\n[list]\n[*]Fixed cases where there was a visible delay loading map images in the Play menu\n[*]Fixed a bug where items that can't be equipped were visible in the Loadout menu\n[*]Fixed a bug where loadout items couldn't be unequipped\n[*]Fixed a bug where loadout changes weren't saved if the game was quit shortly after making changes\n[*]Fixed a bug where loadout changes on the main menu character were delayed\n[/list]\n[ MISC ]\n[list]\n[*]Fixed some visual issues with demo playback\n[*]Fixed an issue where animations would not play back correctly in a CSTV broadcast\n[*]Adjusted wear values of some community stickers to better match CS:GO\n[/list]\n[ MAPS ]\n[i]Ancient:[/i][list]\n[*]Added simplified grenade collisions to corner trims and central pillar on B site\n[/list]\n[i]Anubis:[/i][list]\n[*]Adjusted clipping at A site steps between Walkway and Heaven\n[/list]"
    msg = CounterStrikeUpdateMessage(post=mocked_cs2_update_post)
    expected = "<b>Hello World</b>\n(2009-02-14 00:31:30)\n\n<b>[ UI ]</b>\n\n• Fixed cases where there was a visible delay loading map images in the Play menu\n• Fixed a bug where items that can&#39;t be equipped were visible in the Loadout menu\n• Fixed a bug where loadout items couldn&#39;t be unequipped\n• Fixed a bug where loadout changes weren&#39;t saved if the game was quit shortly after making changes\n• Fixed a bug where loadout changes on the main menu character were delayed\n\n<b>[ MISC ]</b>\n\n• Fixed some visual issues with demo playback\n• Fixed an issue where animations would not play back correctly in a CSTV broadcast\n• Adjusted wear values of some community stickers to better match CS:GO\n\n<b>[ MAPS ]</b>\n<em>Ancient:</em>\n• Added simplified grenade collisions to corner trims and central pillar on B site\n\n<em>Anubis:</em>\n• Adjusted clipping at A site steps between Walkway and Heaven\n\n\nSource: <a href='https://www.counter-strike.net/news/updates'>https://www.counter-strike.net/news/updates</a>"

    assert len(msg.messages) == 1
    assert msg.message == expected


def test_counter_strike_update_message_too_long(mocked_cs2_update_post):
    mocked_cs2_update_post.body = "foo bar" * 570
    msg = CounterStrikeUpdateMessage(post=mocked_cs2_update_post)

    assert len(msg.message) > 4096
    assert len(msg.messages) == 2
