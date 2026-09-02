from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from cs2posts.msg import CounterStrikeExternalMessage
from cs2posts.msg import create_message
from cs2posts.msg.cs_external_msg import build_content
from cs2posts.msg.cs_external_msg import find_read_more_links
from cs2posts.msg.cs_external_msg import remove_read_more_links
from cs2posts.msg.cs_external_msg import render_external_message
from cs2posts.msg.cs_external_msg import strip_media
from tests.fakes import FakeBot


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_strip_media_removes_images_and_line_breaks():
    soup = soup_of("<p>Lead<img src='x.jpg'/><br/>Tail</p>")

    strip_media(soup)

    assert soup.find("img") is None
    assert soup.find("br") is None
    assert "Lead" in str(soup)


@pytest.mark.parametrize(
    "label", ["Read more", "READ MORE", "Read the rest of the story"]
)
def test_find_read_more_links_matches_known_labels(label):
    soup = soup_of(f"<a href='https://example.com/story'>{label}</a>")

    (link,) = find_read_more_links(soup)

    assert link.get("href") == "https://example.com/story"


def test_find_read_more_links_ignores_other_anchors():
    soup = soup_of("<a href='https://example.com'>Home</a>")

    assert find_read_more_links(soup) == []


def test_remove_read_more_links_takes_them_out_of_the_body():
    soup = soup_of("Lead <a href='https://example.com/story'>Read more</a>")

    remove_read_more_links(find_read_more_links(soup))

    assert "Read more" not in str(soup)


def test_build_content_strips_paragraph_wrappers():
    soup = soup_of("<p>Lead<br/>Tail</p>")

    assert build_content(soup) == "LeadTail"


def test_render_external_message_includes_title_date_and_source(make_post):
    post = make_post(title="Some <News>", date=1700000000)

    message = render_external_message(post, "Body", "https://example.com/story")

    assert "🔗 <b>External News</b>" in message
    assert "Some &lt;News&gt;" in message
    assert post.date_display in message
    assert "Body" in message
    assert "href='https://example.com/story'" in message


def test_the_read_more_target_wins_over_the_steam_redirect(make_post):
    post = make_post(
        feed_type=0,
        url="https://steam.example/redirect",
        contents=(
            "<p><img src='https://example.com/image.jpg'/>"
            "Lead paragraph<br/>"
            "<a href='https://example.com/story'>Read more</a></p>"
        ),
    )

    message = CounterStrikeExternalMessage(post)

    assert "https://example.com/story" in message.message
    assert "Read more" not in message.message
    assert "image.jpg" not in message.message


def test_the_steam_redirect_is_used_when_there_is_no_read_more(
    make_post, http_response
):
    http_response(url="https://example.com/resolved")
    post = make_post(feed_type=0, contents="<p>Just a paragraph</p>")

    message = CounterStrikeExternalMessage(post)

    assert "https://example.com/resolved" in message.message


def test_an_external_message_exposes_its_text_chunks(make_post):
    post = make_post(feed_type=0, contents="<a href='https://x.test'>Read more</a>Body")

    message = CounterStrikeExternalMessage(post)

    assert message.messages == [message.message]


@pytest.mark.asyncio
async def test_create_message_builds_an_external_message(make_post):
    post = make_post(feed_type=0, contents="<a href='https://x.test'>Read more</a>Body")

    message = await create_message(post)

    assert isinstance(message, CounterStrikeExternalMessage)


@pytest.mark.asyncio
async def test_sending_delivers_the_rendered_text(make_post):
    post = make_post(feed_type=0, contents="<a href='https://x.test'>Read more</a>Body")
    message = CounterStrikeExternalMessage(post)
    bot = FakeBot()

    await message.send(bot, chat_id=1337)

    assert bot.texts == [message.message]
    assert bot.messages[0]["chat_id"] == 1337
