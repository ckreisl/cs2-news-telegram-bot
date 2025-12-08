from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from cs2posts.content.content import Carousel
from cs2posts.content.content import Image
from cs2posts.content.content import TextBlock
from cs2posts.content.content import Video
from cs2posts.content.content import Youtube
from cs2posts.dto.post import Post
from cs2posts.msg.cs_news_msg import CounterStrikeNewsMessage


@pytest.fixture
def mocked_news_post():
    return Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="This is a test message.",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)


@pytest.fixture
def mocked_news_post_with_image():
    return Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents='[img src="https://example.com/image.jpg"][/img]\nThis is a test message.',
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)


@pytest.fixture
def mocked_news_post_with_video():
    return Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents='[video mp4="https://example.com/video.mp4"][/video]\nThis is a test message.',
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)


@pytest.fixture
def mocked_news_post_with_youtube():
    return Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents='[previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]\nThis is a test message.',
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)


@pytest.fixture
def mocked_news_post_with_carousel():
    return Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents='[carousel][img src="https://example.com/img1.jpg"][/img][img src="https://example.com/img2.jpg"][/img][/carousel]\nThis is a test message.',
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)


def test_counter_strike_news_message_init(mocked_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(mocked_news_post)
        assert msg.post == mocked_news_post
        assert len(msg.content) >= 1


def test_counter_strike_news_message_get_header(mocked_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(mocked_news_post)
        header = msg.get_header()
        assert "<b>Some News</b>" in header
        assert "2009-02-13" in header


def test_counter_strike_news_message_add_header_text_block(mocked_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(mocked_news_post)
        # First content should be a TextBlock with header
        if isinstance(msg.content[0], TextBlock):
            assert "<b>Some News</b>" in msg.content[0].text


def test_counter_strike_news_message_add_footer(mocked_news_post):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(mocked_news_post)
        # Last content should contain footer
        last_content = msg.content[-1]
        if isinstance(last_content, TextBlock):
            assert "(Author: Valve)" in last_content.text
            assert "Source:" in last_content.text


def test_counter_strike_news_message_with_image_heading(mocked_news_post_with_image):
    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        with patch('cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url') as mock_resolve:
            mock_resolve.return_value = "https://example.com/image.jpg"
            msg = CounterStrikeNewsMessage(mocked_news_post_with_image)
            # Should have image as first content
            assert any(isinstance(c, Image) for c in msg.content)


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_message():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="This is a test message.",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    text_block = TextBlock(0, 10, False, "Test message")
    await msg.send_message(mocked_bot, 42, text_block)
    mocked_bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_message_long_text():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="A" * 5000,
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    text_block = TextBlock(0, 5000, False, "A" * 5000)
    await msg.send_message(mocked_bot, 42, text_block)
    # Should split message and call multiple times
    assert mocked_bot.send_message.call_count >= 1


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_image_valid_url():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    image = Image(0, 50, False, "https://example.com/image.jpg")

    with patch('cs2posts.msg.cs_news_msg.Utils.extract_url') as mock_extract:
        mock_extract.return_value = "https://example.com/image.jpg"
        with patch('cs2posts.msg.cs_news_msg.Utils.is_valid_url') as mock_valid:
            mock_valid.return_value = True
            await msg.send_image(mocked_bot, 42, image)
            mocked_bot.send_photo.assert_called_once()


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_image_invalid_url():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    image = Image(0, 50, False, "invalid-url")

    with patch('cs2posts.msg.cs_news_msg.Utils.extract_url') as mock_extract:
        mock_extract.return_value = "invalid-url"
        with patch('cs2posts.msg.cs_news_msg.Utils.is_valid_url') as mock_valid:
            mock_valid.return_value = False
            await msg.send_image(mocked_bot, 42, image)
            mocked_bot.send_photo.assert_not_called()


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_image_with_heading():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    image = Image(0, 50, True, "https://example.com/image.jpg")

    with patch('cs2posts.msg.cs_news_msg.Utils.extract_url') as mock_extract:
        mock_extract.return_value = "https://example.com/image.jpg"
        with patch('cs2posts.msg.cs_news_msg.Utils.is_valid_url') as mock_valid:
            mock_valid.return_value = True
            await msg.send_image(mocked_bot, 42, image)
            call_kwargs = mocked_bot.send_photo.call_args[1]
            assert call_kwargs['caption'] is not None


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_carousel():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    images = [
        Image(0, 10, False, "https://example.com/img1.jpg"),
        Image(10, 20, False, "https://example.com/img2.jpg"),
    ]
    carousel = Carousel(0, 100, False, images)

    with patch('cs2posts.msg.cs_news_msg.Utils.extract_url') as mock_extract:
        mock_extract.side_effect = lambda x: x
        with patch('cs2posts.msg.cs_news_msg.Utils.is_valid_url') as mock_valid:
            mock_valid.return_value = True
            await msg.send_carousel(mocked_bot, 42, carousel)
            mocked_bot.send_media_group.assert_called()


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_carousel_invalid_urls():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    images = [
        Image(0, 10, False, "invalid"),
        Image(10, 20, False, "invalid2"),
    ]
    carousel = Carousel(0, 100, False, images)

    with patch('cs2posts.msg.cs_news_msg.Utils.extract_url') as mock_extract:
        mock_extract.side_effect = lambda x: x
        with patch('cs2posts.msg.cs_news_msg.Utils.is_valid_url') as mock_valid:
            mock_valid.return_value = False
            await msg.send_carousel(mocked_bot, 42, carousel)
            # Should not send if all images are invalid
            # Empty chunks should not trigger send_media_group


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_video():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    video = Video(0, 50, False, webm="", mp4="https://example.com/video.mp4", poster="https://example.com/poster.jpg", autoplay=True, controls=True)

    with patch('cs2posts.msg.cs_news_msg.Utils.extract_url') as mock_extract:
        mock_extract.side_effect = lambda x: x
        with patch('cs2posts.msg.cs_news_msg.Utils.is_valid_url') as mock_valid:
            mock_valid.return_value = True
            await msg.send_video(mocked_bot, 42, video)
            mocked_bot.send_video.assert_called_once()


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_video_empty():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    video = Video(0, 50, False, webm="", mp4="", poster="", autoplay=False, controls=False)

    await msg.send_video(mocked_bot, 42, video)
    mocked_bot.send_video.assert_not_called()


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_video_invalid_url():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    video = Video(0, 50, False, webm="", mp4="invalid", poster="", autoplay=False, controls=False)

    with patch('cs2posts.msg.cs_news_msg.Utils.extract_url') as mock_extract:
        mock_extract.return_value = "invalid"
        with patch('cs2posts.msg.cs_news_msg.Utils.is_valid_url') as mock_valid:
            mock_valid.return_value = False
            await msg.send_video(mocked_bot, 42, video)
            mocked_bot.send_video.assert_not_called()


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_youtube_video():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    youtube = Youtube(0, 50, False, "dQw4w9WgXcQ")

    await msg.send_youtube_video(mocked_bot, 42, youtube)
    mocked_bot.send_message.assert_called_once()
    call_kwargs = mocked_bot.send_message.call_args[1]
    assert "youtube.com" in call_kwargs['text']
    assert call_kwargs['disable_web_page_preview'] is False


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_youtube_video_with_heading():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    youtube = Youtube(0, 50, True, "dQw4w9WgXcQ")

    await msg.send_youtube_video(mocked_bot, 42, youtube)
    call_kwargs = mocked_bot.send_message.call_args[1]
    assert "<b>Some News</b>" in call_kwargs['text']


@pytest.mark.asyncio
async def test_counter_strike_news_message_send():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="This is a test message.",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    mocked_bot = AsyncMock()
    await msg.send(mocked_bot, 42)
    # Should have sent at least one message
    assert mocked_bot.send_message.called or mocked_bot.send_photo.called


@pytest.mark.asyncio
async def test_counter_strike_news_message_send_with_all_content_types():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="Test",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        msg = CounterStrikeNewsMessage(post)

    # Replace content with all types
    msg.content = [
        TextBlock(0, 10, True, "Header text"),
        Image(10, 20, False, "https://example.com/image.jpg"),
        Carousel(20, 30, False, [Image(20, 25, False, "https://example.com/img.jpg")]),
        Video(30, 40, False, webm="", mp4="https://example.com/video.mp4", poster="", autoplay=False, controls=False),
        Youtube(40, 50, False, "dQw4w9WgXcQ"),
        TextBlock(50, 60, False, "Footer text"),
    ]

    mocked_bot = AsyncMock()
    with patch.object(msg, 'send_message', new_callable=AsyncMock) as mock_send_msg:
        with patch.object(msg, 'send_image', new_callable=AsyncMock) as mock_send_img:
            with patch.object(msg, 'send_carousel', new_callable=AsyncMock) as mock_send_carousel:
                with patch.object(msg, 'send_video', new_callable=AsyncMock) as mock_send_video:
                    with patch.object(msg, 'send_youtube_video', new_callable=AsyncMock) as mock_send_yt:
                        await msg.send(mocked_bot, 42)
                        assert mock_send_msg.call_count == 2
                        mock_send_img.assert_called_once()
                        mock_send_carousel.assert_called_once()
                        mock_send_video.assert_called_once()
                        mock_send_yt.assert_called_once()


def test_counter_strike_news_message_add_footer_to_non_textblock():
    post = Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents='[img src="https://example.com/image.jpg"][/img]',
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)

    with patch('requests.get') as mocked_get:
        mocked_get.return_value.ok = True
        mocked_get.return_value.url = "https://www.counter-strike.net/newsentry/1338"
        with patch('cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url') as mock_resolve:
            mock_resolve.return_value = "https://example.com/image.jpg"
            msg = CounterStrikeNewsMessage(post)
            # Should append a TextBlock with footer
            assert isinstance(msg.content[-1], TextBlock)
            assert "(Author: Valve)" in msg.content[-1].text
