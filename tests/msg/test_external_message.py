from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from cs2posts.msg import CounterStrikeExternalMessage
from cs2posts.msg import TelegramMessageFactory
from cs2posts.msg.cs_external_msg import build_content
from cs2posts.msg.cs_external_msg import build_message
from cs2posts.msg.cs_external_msg import cleanup_soup
from cs2posts.msg.cs_external_msg import extract_read_more_links
from cs2posts.msg.cs_external_msg import remove_read_more_links


def test_counter_strike_external_message_uses_read_more_link_and_strips_media(mocked_cs2_external_news):
    mocked_cs2_external_news.contents = (
        "<p><img src='https://example.com/image.jpg'/>"
        "Lead paragraph<br/>"
        "<a href='https://example.com/story'>Read more</a></p>"
    )

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"

        msg = CounterStrikeExternalMessage(post=mocked_cs2_external_news)

    assert "Read more" not in msg.message
    assert "<img" not in msg.message
    assert "Lead paragraph" in msg.message
    assert "Source: <a href='https://example.com/story'>Link</a>" in msg.message


def test_cleanup_soup_removes_images_and_breaks():
    soup = BeautifulSoup(
        "<p>Hello<img src='https://example.com/image.jpg'/>World<br/>Tail</p>",
        "html.parser",
    )

    cleanup_soup(soup)

    assert str(soup) == "<p>HelloWorldTail</p>"


def test_extract_read_more_links_returns_matching_anchors_only():
    soup = BeautifulSoup(
        ""
        "<a href='https://example.com/1'>Read more</a>"
        "<a href='https://example.com/2'>Read the rest of the story</a>"
        "<a href='https://example.com/3'>Other link</a>"
        "",
        "html.parser",
    )

    read_more = extract_read_more_links(soup)

    assert len(read_more) == 2
    assert read_more[0].get("href") == "https://example.com/1"
    assert read_more[1].get("href") == "https://example.com/2"


def test_remove_read_more_links_removes_anchors_from_soup():
    soup = BeautifulSoup(
        "<p>Lead <a href='https://example.com/story'>Read more</a> tail</p>",
        "html.parser",
    )
    read_more = extract_read_more_links(soup)

    remove_read_more_links(read_more)

    assert "Read more" not in str(soup)


def test_build_content_strips_wrapper_tags_and_whitespace():
    soup = BeautifulSoup("  <p>Lead paragraph</p><br/>  ", "html.parser")

    content = build_content(soup)

    assert content == "Lead paragraph"


def test_build_message_formats_external_message(mocked_cs2_external_news):
    message = build_message(mocked_cs2_external_news, "Lead paragraph")

    assert message.startswith("🔗 <b>External News</b>")
    assert "<b>Some News</b>" in message
    assert "Lead paragraph" in message
    assert "Source: <a href='https://www.counter-strike.net/newsentry/1339'>Link</a>" in message


@pytest.mark.asyncio
async def test_telegram_message_send_external_raises_on_chunk_failure(mocked_cs2_external_news):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://test.com"
        msg = await TelegramMessageFactory.create(mocked_cs2_external_news)

    msg._TelegramMessage__messages = ["chunk1", "chunk2"]

    bot = AsyncMock()
    bot.send_message.side_effect = [RuntimeError("fail"), None]

    with pytest.raises(RuntimeError, match="fail"):
        await msg.send(bot=bot, chat_id=42)

    assert bot.send_message.call_count == 1
