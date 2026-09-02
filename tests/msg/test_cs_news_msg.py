from __future__ import annotations

import pytest
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.error import ChatMigrated
from telegram.error import Forbidden
from telegram.error import NetworkError
from telegram.error import RetryAfter
from telegram.error import TimedOut

from cs2posts.content import Carousel
from cs2posts.content import Image
from cs2posts.content import TextBlock
from cs2posts.content import Video
from cs2posts.content import Youtube
from cs2posts.msg import CounterStrikeNewsMessage
from cs2posts.msg.constants import MAX_MEDIA_GROUP_SIZE
from tests.fakes import FakeBot

CHAT_ID = 1337


@pytest.fixture
def news_post(make_post):
    return make_post(
        title="Some News",
        author="Valve",
        contents="A heading\n\nSome body text.",
    )


@pytest.fixture
def message(news_post):
    return CounterStrikeNewsMessage(news_post)


@pytest.fixture
def bot():
    return FakeBot()


def image(url: str = "https://example.com/a.png", is_heading: bool = False) -> Image:
    return Image(text_pos_start=0, text_pos_end=1, is_heading=is_heading, url=url)


def video(**overrides) -> Video:
    defaults = {
        "text_pos_start": 0,
        "text_pos_end": 1,
        "is_heading": False,
        "webm": None,
        "mp4": "https://example.com/v.mp4",
        "poster": None,
        "autoplay": None,
        "controls": None,
    }
    return Video(**{**defaults, **overrides})


# --- assembly ----------------------------------------------------------------


def test_a_message_is_built_from_the_post_body(message):
    assert message.content
    assert all(hasattr(block, "text_pos_start") for block in message.content)


def test_the_header_carries_the_title_and_date(message, news_post):
    assert message.header == (f"<b>{news_post.title}</b>\n({news_post.date_display})")


def test_the_header_and_footer_escape_html(make_post):
    post = make_post(title="5 < 6 & 7 > 2", author="<b>Valve</b>", contents="Body")

    message = CounterStrikeNewsMessage(post)

    assert "5 &lt; 6 &amp; 7 &gt; 2" in message.header
    assert "&lt;b&gt;Valve&lt;/b&gt;" in message.footer
    assert "<b>Valve</b>" not in message.footer


def test_a_text_led_post_gets_the_header_prepended(message):
    first = message.content[0]

    assert isinstance(first, TextBlock)
    assert first.text.startswith(message.header)


def test_the_footer_ends_the_last_text_block(message):
    last = message.content[-1]

    assert isinstance(last, TextBlock)
    assert last.text.endswith(message.footer)


def test_the_footer_sits_one_blank_line_below_the_body(make_post):
    post = make_post(contents="Body text\n\n\n")

    message = CounterStrikeNewsMessage(post)

    assert f"Body text\n\n{message.footer}" in message.content[-1].text


def test_a_media_led_post_keeps_the_header_for_the_caption(make_post):
    post = make_post(contents="[img]https://example.com/a.png[/img]\nBody")

    message = CounterStrikeNewsMessage(post)

    assert isinstance(message.content[0], Image)
    assert message.content[0].is_heading is True


def test_a_footer_is_appended_as_its_own_block_after_media(make_post):
    post = make_post(contents="[img]https://example.com/a.png[/img]")

    message = CounterStrikeNewsMessage(post)

    assert isinstance(message.content[-1], TextBlock)
    assert message.content[-1].text == message.footer


# --- sending each content type -----------------------------------------------


@pytest.mark.asyncio
async def test_a_text_block_is_sent_as_html_without_a_preview(message, bot):
    await message.send_content(TextBlock(0, 1, False, "Hello"), bot, CHAT_ID)

    (sent,) = bot.messages
    assert sent["text"] == "Hello"
    assert sent["chat_id"] == CHAT_ID
    assert sent["parse_mode"] == ParseMode.HTML
    assert sent["disable_web_page_preview"] is True


@pytest.mark.asyncio
async def test_an_overlong_text_block_is_split(message, bot):
    long_text = "line\n" * 2000

    await message.send_content(TextBlock(0, 1, False, long_text), bot, CHAT_ID)

    assert len(bot.messages) > 1


@pytest.mark.asyncio
async def test_an_image_is_sent_as_a_photo(message, bot):
    await message.send_content(image(), bot, CHAT_ID)

    (sent,) = bot.photos
    assert sent["photo"] == "https://example.com/a.png"
    assert sent["caption"] is None


@pytest.mark.asyncio
async def test_a_heading_image_carries_the_header_as_its_caption(message, bot):
    await message.send_content(image(is_heading=True), bot, CHAT_ID)

    assert bot.photos[0]["caption"] == message.header


@pytest.mark.asyncio
async def test_an_unreachable_image_is_skipped(message, bot, http_response, caplog):
    http_response(status_code=404)

    await message.send_content(image(), bot, CHAT_ID)

    assert bot.photos == []
    assert "invalid URL" in caplog.text


@pytest.mark.asyncio
async def test_a_carousel_is_sent_as_a_media_group(message, bot):
    carousel = Carousel(0, 1, False, [image("https://example.com/1.png"), image()])

    await message.send_content(carousel, bot, CHAT_ID)

    (group,) = bot.media_groups
    assert len(group["media"]) == 2


@pytest.mark.asyncio
async def test_a_large_carousel_is_split_into_groups(message, bot):
    images = [image(f"https://example.com/{i}.png") for i in range(15)]

    await message.send_content(Carousel(0, 1, False, images), bot, CHAT_ID)

    sizes = [len(group["media"]) for group in bot.media_groups]
    assert sizes == [MAX_MEDIA_GROUP_SIZE, 5]


@pytest.mark.asyncio
async def test_unreachable_carousel_images_are_dropped(
    message, bot, http_response, caplog
):
    http_response(status_code=500)

    await message.send_content(Carousel(0, 1, False, [image()]), bot, CHAT_ID)

    assert bot.media_groups == []
    assert "invalid URL" in caplog.text


@pytest.mark.asyncio
async def test_a_video_is_sent_with_streaming_enabled(message, bot):
    await message.send_content(video(), bot, CHAT_ID)

    (sent,) = bot.videos
    assert sent["video"] == "https://example.com/v.mp4"
    assert sent["supports_streaming"] is True
    assert sent["thumbnail"] is None


@pytest.mark.asyncio
async def test_a_video_poster_becomes_the_thumbnail(message, bot):
    await message.send_content(video(poster="https://example.com/p.jpg"), bot, CHAT_ID)

    assert bot.videos[0]["thumbnail"] == "https://example.com/p.jpg"


@pytest.mark.asyncio
async def test_a_webm_only_video_is_still_sent(message, bot):
    """Regression: an absent mp4 used to be "" rather than None, which made
    the webm fallback unreachable and dropped the video silently."""
    await message.send_content(
        video(mp4=None, webm="https://example.com/v.webm"), bot, CHAT_ID
    )

    assert bot.videos[0]["video"] == "https://example.com/v.webm"


@pytest.mark.asyncio
async def test_a_video_without_a_source_is_skipped(message, bot):
    await message.send_content(video(mp4=None, webm=None), bot, CHAT_ID)

    assert bot.videos == []


@pytest.mark.asyncio
async def test_an_unreachable_video_is_skipped(message, bot, http_response, caplog):
    http_response(status_code=404)

    await message.send_content(video(), bot, CHAT_ID)

    assert bot.videos == []
    assert "invalid URL" in caplog.text


@pytest.mark.asyncio
async def test_a_youtube_video_is_sent_as_a_previewed_link(message, bot):
    youtube = Youtube(0, 1, False, "dQw4w9WgXcQ")

    await message.send_content(youtube, bot, CHAT_ID)

    (sent,) = bot.messages
    assert youtube.watch_url in sent["text"]
    assert sent["disable_web_page_preview"] is False


@pytest.mark.asyncio
async def test_a_heading_youtube_video_carries_the_header(message, bot):
    await message.send_content(Youtube(0, 1, True, "dQw4w9WgXcQ"), bot, CHAT_ID)

    assert bot.messages[0]["text"].startswith(message.header)


@pytest.mark.asyncio
async def test_an_unknown_content_type_is_rejected(message, bot):
    with pytest.raises(TypeError, match="Unsupported content type"):
        await message.send_content(object(), bot, CHAT_ID)


# --- send() orchestration ----------------------------------------------------


@pytest.mark.asyncio
async def test_send_delivers_every_block(make_post, bot):
    post = make_post(contents="Intro\n[img]https://example.com/a.png[/img]\nOutro")
    message = CounterStrikeNewsMessage(post)

    await message.send(bot, CHAT_ID)

    assert bot.photos
    assert bot.messages


@pytest.mark.asyncio
async def test_one_failing_block_does_not_stop_the_rest(message, bot, fast_sleep):
    message.content = [
        TextBlock(0, 1, False, "first"),
        TextBlock(1, 2, False, "second"),
        TextBlock(2, 3, False, "third"),
    ]
    original = bot.send_message
    calls = {"n": 0}

    async def flaky(**kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise BadRequest("Message is too long")
        await original(**kwargs)

    bot.send_message = flaky

    await message.send(bot, CHAT_ID)

    assert bot.texts == ["first", "third"]


@pytest.mark.asyncio
async def test_a_transient_error_is_retried(message, bot, fast_sleep):
    message.content = [TextBlock(0, 1, False, "hello")]
    attempts = {"n": 0}
    original = bot.send_message

    async def flaky(**kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TimedOut
        await original(**kwargs)

    bot.send_message = flaky

    await message.send(bot, CHAT_ID)

    assert bot.texts == ["hello"]
    assert attempts["n"] == 3


@pytest.mark.asyncio
async def test_retries_eventually_give_up(message, bot, fast_sleep, caplog):
    message.content = [TextBlock(0, 1, False, "hello")]

    async def always_times_out(**kwargs):
        raise TimedOut

    bot.send_message = always_times_out

    await message.send(bot, CHAT_ID)

    assert "Giving up" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        Forbidden("bot was blocked"),
        ChatMigrated(new_chat_id=-100),
        BadRequest("Chat not found"),
    ],
)
async def test_chat_level_errors_propagate_to_the_caller(message, bot, error):
    """The whole post is undeliverable; the bot must drop or migrate the chat."""
    message.content = [TextBlock(0, 1, False, "hello")]

    async def failing(**kwargs):
        raise error

    bot.send_message = failing

    with pytest.raises(type(error)):
        await message.send(bot, CHAT_ID)


@pytest.mark.asyncio
async def test_a_content_level_bad_request_is_swallowed(message, bot, caplog):
    message.content = [TextBlock(0, 1, False, "hello")]

    async def failing(**kwargs):
        raise BadRequest("Message is too long")

    bot.send_message = failing

    await message.send(bot, CHAT_ID)

    assert "Could not send" in caplog.text


@pytest.mark.asyncio
async def test_an_unexpected_error_is_swallowed(message, bot, caplog):
    message.content = [TextBlock(0, 1, False, "hello")]

    async def failing(**kwargs):
        raise RuntimeError("boom")

    bot.send_message = failing

    await message.send(bot, CHAT_ID)

    assert "Could not send" in caplog.text


# --- regressions -------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [TimedOut(), NetworkError("down")])
async def test_the_errors_ptb_actually_raises_are_retried(
    message, bot, fast_sleep, error
):
    """Regression: TRANSIENT_ERRORS listed the raw httpx exceptions, but
    HTTPXRequest wraps every one of them before it reaches us, so the retry
    loop never fired for a real timeout."""
    message.content = [TextBlock(0, 1, False, "hello")]
    attempts = {"n": 0}
    original = bot.send_message

    async def flaky(**kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise error
        await original(**kwargs)

    bot.send_message = flaky

    await message.send(bot, CHAT_ID)

    assert bot.texts == ["hello"]
    assert attempts["n"] == 3


@pytest.mark.asyncio
async def test_flood_control_waits_for_the_interval_telegram_asks_for(
    message, bot, monkeypatch
):
    import asyncio

    delays = []

    async def record(delay):
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", record)

    message.content = [TextBlock(0, 1, False, "hello")]
    attempts = {"n": 0}
    original = bot.send_message

    async def flaky(**kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RetryAfter(17)
        await original(**kwargs)

    bot.send_message = flaky

    await message.send(bot, CHAT_ID)

    assert bot.texts == ["hello"]
    assert 17.0 in delays


@pytest.mark.asyncio
async def test_a_bad_request_is_not_retried(message, bot, fast_sleep):
    """BadRequest subclasses NetworkError, so ordering the except clauses
    wrongly would retry a permanently malformed send."""
    message.content = [TextBlock(0, 1, False, "hello")]
    attempts = {"n": 0}

    async def always_bad(**kwargs):
        attempts["n"] += 1
        raise BadRequest("Message is too long")

    bot.send_message = always_bad

    await message.send(bot, CHAT_ID)

    assert attempts["n"] == 1


@pytest.mark.asyncio
async def test_chat_not_found_still_propagates(message, bot, fast_sleep):
    """The messenger relies on this to drop a chat that no longer exists; it
    must not be absorbed by the transient branch."""
    message.content = [TextBlock(0, 1, False, "hello")]

    async def gone(**kwargs):
        raise BadRequest("Chat not found")

    bot.send_message = gone

    with pytest.raises(BadRequest):
        await message.send(bot, CHAT_ID)


@pytest.mark.asyncio
async def test_a_leading_carousel_captions_the_media_group(message, bot):
    """Regression: _add_header skips media-led posts because the caption is
    meant to carry the header, but the carousel sender never set one, so the
    title and date were dropped from the post entirely."""
    carousel = Carousel(0, 1, True, [image("https://example.com/1.png"), image()])

    await message.send_content(carousel, bot, CHAT_ID)

    (group,) = bot.media_groups
    first, second = group["media"]
    assert first.caption == message.header
    # Telegram takes the group's caption from its first item only.
    assert second.caption is None


@pytest.mark.asyncio
async def test_a_non_heading_carousel_has_no_caption(message, bot):
    await message.send_content(Carousel(0, 1, False, [image()]), bot, CHAT_ID)

    (group,) = bot.media_groups
    assert group["media"][0].caption is None


@pytest.mark.asyncio
async def test_the_caption_rides_the_first_reachable_image(message, bot, monkeypatch):
    """The header must not be lost just because the first image 404s."""

    async def only_the_second_is_valid(url):
        return url == "https://example.com/2.png"

    monkeypatch.setattr(message, "_is_valid_media_url", only_the_second_is_valid)

    carousel = Carousel(
        0,
        1,
        True,
        [image("https://example.com/1.png"), image("https://example.com/2.png")],
    )

    await message.send_content(carousel, bot, CHAT_ID)

    (group,) = bot.media_groups
    (only,) = group["media"]
    assert only.caption == message.header
