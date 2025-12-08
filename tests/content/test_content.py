from __future__ import annotations

from cs2posts.content.content import Carousel
from cs2posts.content.content import Content
from cs2posts.content.content import Image
from cs2posts.content.content import TextBlock
from cs2posts.content.content import Video
from cs2posts.content.content import Youtube


# Tests for Content dataclass
def test_content_creation():
    content = Content(text_pos_start=0, text_pos_end=10, is_heading=True)
    assert content.text_pos_start == 0
    assert content.text_pos_end == 10
    assert content.is_heading is True


def test_content_is_heading_false():
    content = Content(text_pos_start=0, text_pos_end=10, is_heading=False)
    assert content.is_heading is False


# Tests for Video dataclass
def test_video_creation():
    video = Video(
        text_pos_start=0,
        text_pos_end=100,
        is_heading=False,
        webm="https://example.com/video.webm",
        mp4="https://example.com/video.mp4",
        poster="https://example.com/poster.jpg",
        autoplay=True,
        controls=False
    )
    assert video.text_pos_start == 0
    assert video.text_pos_end == 100
    assert video.is_heading is False
    assert video.webm == "https://example.com/video.webm"
    assert video.mp4 == "https://example.com/video.mp4"
    assert video.poster == "https://example.com/poster.jpg"
    assert video.autoplay is True
    assert video.controls is False


def test_video_is_empty_with_no_urls():
    video = Video(
        text_pos_start=0,
        text_pos_end=100,
        is_heading=False,
        webm="",
        mp4="",
        poster="",
        autoplay=False,
        controls=False
    )
    assert video.is_empty() is True


def test_video_is_empty_with_webm_only():
    video = Video(
        text_pos_start=0,
        text_pos_end=100,
        is_heading=False,
        webm="https://example.com/video.webm",
        mp4="",
        poster="",
        autoplay=False,
        controls=False
    )
    assert video.is_empty() is False


def test_video_is_empty_with_mp4_only():
    video = Video(
        text_pos_start=0,
        text_pos_end=100,
        is_heading=False,
        webm="",
        mp4="https://example.com/video.mp4",
        poster="",
        autoplay=False,
        controls=False
    )
    assert video.is_empty() is False


def test_video_is_empty_with_both_urls():
    video = Video(
        text_pos_start=0,
        text_pos_end=100,
        is_heading=False,
        webm="https://example.com/video.webm",
        mp4="https://example.com/video.mp4",
        poster="",
        autoplay=False,
        controls=False
    )
    assert video.is_empty() is False


# Tests for Image dataclass
def test_image_creation():
    image = Image(
        text_pos_start=0,
        text_pos_end=50,
        is_heading=False,
        url="https://example.com/image.png"
    )
    assert image.text_pos_start == 0
    assert image.text_pos_end == 50
    assert image.is_heading is False
    assert image.url == "https://example.com/image.png"


# Tests for Carousel dataclass
def test_carousel_creation():
    images = [
        Image(text_pos_start=10, text_pos_end=20, is_heading=False, url="https://example.com/image1.png"),
        Image(text_pos_start=30, text_pos_end=40, is_heading=False, url="https://example.com/image2.png"),
    ]
    carousel = Carousel(
        text_pos_start=0,
        text_pos_end=100,
        is_heading=False,
        images=images
    )
    assert carousel.text_pos_start == 0
    assert carousel.text_pos_end == 100
    assert carousel.is_heading is False
    assert len(carousel.images) == 2
    assert carousel.images[0].url == "https://example.com/image1.png"
    assert carousel.images[1].url == "https://example.com/image2.png"


def test_carousel_empty_images():
    carousel = Carousel(
        text_pos_start=0,
        text_pos_end=100,
        is_heading=False,
        images=[]
    )
    assert len(carousel.images) == 0


# Tests for TextBlock dataclass
def test_textblock_creation():
    textblock = TextBlock(
        text_pos_start=0,
        text_pos_end=50,
        is_heading=True,
        text="Hello World"
    )
    assert textblock.text_pos_start == 0
    assert textblock.text_pos_end == 50
    assert textblock.is_heading is True
    assert textblock.text == "Hello World"


def test_textblock_empty_text():
    textblock = TextBlock(
        text_pos_start=0,
        text_pos_end=0,
        is_heading=False,
        text=""
    )
    assert textblock.text == ""


# Tests for Youtube dataclass
def test_youtube_creation():
    youtube = Youtube(
        text_pos_start=0,
        text_pos_end=50,
        is_heading=False,
        url="dQw4w9WgXcQ"
    )
    assert youtube.text_pos_start == 0
    assert youtube.text_pos_end == 50
    assert youtube.is_heading is False
    assert youtube.url == "dQw4w9WgXcQ"


def test_youtube_get_url():
    youtube = Youtube(
        text_pos_start=0,
        text_pos_end=50,
        is_heading=False,
        url="dQw4w9WgXcQ"
    )
    assert youtube.get_url() == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_youtube_get_url_with_different_id():
    youtube = Youtube(
        text_pos_start=0,
        text_pos_end=50,
        is_heading=False,
        url="abc123XYZ"
    )
    assert youtube.get_url() == "https://www.youtube.com/watch?v=abc123XYZ"
