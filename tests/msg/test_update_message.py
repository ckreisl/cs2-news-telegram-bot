from __future__ import annotations

import pytest

from cs2posts.content import Image
from cs2posts.content import TextBlock
from cs2posts.msg import CounterStrikeUpdateMessage
from cs2posts.msg import create_message
from tests.fakes import FakeBot


def test_an_update_renders_title_body_and_source(mocked_cs2_update_post):
    message = CounterStrikeUpdateMessage(mocked_cs2_update_post)

    assert len(message.content) == 1
    (block,) = message.content
    assert isinstance(block, TextBlock)
    assert block.text == (
        "<b>Release Notes for 2/13/2009</b>\n"
        "(2009-02-13 23:31:30)\n\n"
        "my content\n\n"
        "(Author: Valve)\n\n"
        "Source: <a href='https://example.com/resolved'>Link</a>"
    )


def test_section_headings_and_bullets_are_formatted(mocked_cs2_update_post):
    mocked_cs2_update_post.contents = (
        "[ MISC ]\n[list]\n[*]Fixed some visual issues with demo playback\n[/list]"
    )

    message = CounterStrikeUpdateMessage(mocked_cs2_update_post)

    (block,) = message.content
    assert "<b>[ MISC ]</b>" in block.text
    assert "• Fixed some visual issues with demo playback" in block.text


def test_an_inline_image_becomes_its_own_block(mocked_cs2_update_post):
    mocked_cs2_update_post.contents = (
        "[ MISC ]\n"
        "Select the appropriate option using the Workshop Tool:\n\n"
        "[img]https://example.com/image.png[/img]\n"
        "We're excited to see your submissions!"
    )

    message = CounterStrikeUpdateMessage(mocked_cs2_update_post)

    images = [block for block in message.content if isinstance(block, Image)]
    # bbcode turns a bare URL into an anchor before extraction; the href is
    # pulled back out at send time.
    (image,) = images
    assert "https://example.com/image.png" in image.url
    # The markup must not leak into the surrounding prose.
    for block in message.content:
        if isinstance(block, TextBlock):
            assert "[img]" not in block.text
            assert "[/img]" not in block.text


@pytest.mark.asyncio
async def test_a_text_only_update_sends_no_media(mocked_cs2_update_post, fast_sleep):
    message = await create_message(mocked_cs2_update_post)
    bot = FakeBot()

    await message.send(bot, chat_id=1337)

    assert bot.photos == []
    assert bot.messages


@pytest.mark.asyncio
async def test_an_update_with_an_image_sends_the_photo_and_the_prose(
    mocked_cs2_update_post, fast_sleep
):
    mocked_cs2_update_post.contents = (
        "[ MISC ]\n"
        "Select the appropriate option using the Workshop Tool:\n\n"
        "[img]https://example.com/image.png[/img]\n"
        "We're excited to see your submissions!"
    )
    message = await create_message(mocked_cs2_update_post)
    bot = FakeBot()

    await message.send(bot, chat_id=1337)

    assert [photo["photo"] for photo in bot.photos] == ["https://example.com/image.png"]
    assert len(bot.messages) == 2
