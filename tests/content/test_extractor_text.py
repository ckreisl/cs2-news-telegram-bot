from __future__ import annotations

from cs2posts.content.content import Carousel
from cs2posts.content.content import Image
from cs2posts.content.content import TextBlock
from cs2posts.content.content import Video
from cs2posts.content.content import Youtube
from cs2posts.content.extractor_text import TextBlockExtractor


def test_textblock_extractor_extract_plain_text():
    text = "This is plain text without any special content"
    extractor = TextBlockExtractor(text)
    blocks = extractor.extract()
    assert len(blocks) == 1
    assert blocks[0].text == text


def test_textblock_extractor_extract_empty_string():
    text = ""
    extractor = TextBlockExtractor(text)
    blocks = extractor.extract()
    assert len(blocks) == 1
    assert blocks[0].text == ""


def test_textblock_extractor_extract_with_provided_images():
    text = "before image after"
    images = [Image(text_pos_start=7, text_pos_end=12, is_heading=False, url="https://example.com/image.png")]
    extractor = TextBlockExtractor(text, images=images)
    blocks = extractor.extract()
    assert len(blocks) == 2


def test_textblock_extractor_extract_with_provided_videos():
    text = "before video after"
    videos = [Video(text_pos_start=7, text_pos_end=12, is_heading=False, webm="", mp4="https://example.com/video.mp4", poster="", autoplay=False, controls=False)]
    extractor = TextBlockExtractor(text, videos=videos)
    blocks = extractor.extract()
    assert len(blocks) == 2


def test_textblock_extractor_extract_with_provided_carousel():
    text = "before carousel after"
    carousel = [Carousel(text_pos_start=7, text_pos_end=15, is_heading=False, images=[])]
    extractor = TextBlockExtractor(text, carousel=carousel)
    blocks = extractor.extract()
    assert len(blocks) == 2


def test_textblock_extractor_extract_with_provided_youtube():
    text = "before youtube after"
    youtube = [Youtube(text_pos_start=7, text_pos_end=14, is_heading=False, url="dQw4w9WgXcQ")]
    extractor = TextBlockExtractor(text, youtube=youtube)
    blocks = extractor.extract()
    assert len(blocks) == 2


def test_textblock_extractor_extract_text_before_content():
    text = "text before [img]https://example.com/image.png[/img]"
    images = [Image(text_pos_start=12, text_pos_end=52, is_heading=False, url="https://example.com/image.png")]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    assert len(blocks) == 2
    assert blocks[0].text == "text before"


def test_textblock_extractor_extract_text_after_content():
    text = "[img]https://example.com/image.png[/img] text after"
    images = [Image(text_pos_start=0, text_pos_end=40, is_heading=False, url="https://example.com/image.png")]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    assert len(blocks) == 1
    assert blocks[0].text == "text after"


def test_textblock_extractor_extract_text_between_content():
    text = "[img]url1[/img] text between [img]url2[/img]"
    images = [
        Image(text_pos_start=0, text_pos_end=15, is_heading=False, url="url1"),
        Image(text_pos_start=29, text_pos_end=44, is_heading=False, url="url2"),
    ]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    assert len(blocks) == 2
    assert blocks[0].text == "text between"


def test_textblock_extractor_extract_is_heading_false():
    text = "plain text"
    extractor = TextBlockExtractor(text)
    blocks = extractor.extract()
    assert blocks[0].is_heading is False


def test_textblock_extractor_extract_strips_whitespace():
    # Only text blocks extracted from between content are stripped
    # Full text without content is returned as-is
    text = "[img]url[/img]   trimmed text   "
    images = [Image(text_pos_start=0, text_pos_end=14, is_heading=False, url="url")]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    assert blocks[0].text == "trimmed text"


def test_textblock_extractor_extract_skips_empty_blocks():
    text = "[img]url[/img]    [img]url2[/img]"
    images = [
        Image(text_pos_start=0, text_pos_end=14, is_heading=False, url="url"),
        Image(text_pos_start=18, text_pos_end=33, is_heading=False, url="url2"),
    ]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    # Should not include empty blocks between images
    assert all(len(b.text.strip()) > 0 or b == blocks[-1] for b in blocks)


def test_textblock_extractor_extract_positions():
    text = "text before [img]url[/img] text after"
    images = [Image(text_pos_start=12, text_pos_end=26, is_heading=False, url="url")]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    assert blocks[0].text_pos_start == 0
    assert blocks[0].text_pos_end == 12


def test_textblock_extractor_combine_empty_list():
    text = ""
    extractor = TextBlockExtractor(text)
    result = extractor._combine([])
    assert result == []


def test_textblock_extractor_combine_single_block():
    text = ""
    extractor = TextBlockExtractor(text)
    block = TextBlock(0, 10, False, "text")
    result = extractor._combine([block])
    assert len(result) == 1
    assert result[0] == block


def test_textblock_extractor_combine_link_blocks():
    text = ""
    extractor = TextBlockExtractor(text)
    left = TextBlock(0, 10, False, "text>")
    right = TextBlock(10, 20, False, "</a> more")
    result = extractor._combine([left, right])
    assert len(result) == 1
    assert "Image Link" in result[0].text


def test_textblock_extractor_combine_no_link_blocks():
    text = ""
    extractor = TextBlockExtractor(text)
    left = TextBlock(0, 10, False, "text")
    right = TextBlock(10, 20, False, "more")
    result = extractor._combine([left, right])
    assert len(result) == 2


def test_textblock_extractor_with_all_none_content():
    text = "plain text"
    extractor = TextBlockExtractor(text, videos=None, carousel=None, images=None, youtube=None)
    blocks = extractor.extract()
    assert len(blocks) >= 1


def test_textblock_extractor_content_at_start():
    text = "[img]url[/img] after"
    images = [Image(text_pos_start=0, text_pos_end=14, is_heading=False, url="url")]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    # Should handle content at position 0
    assert any(b.text == "after" for b in blocks)


def test_textblock_extractor_consecutive_content():
    text = "[img]url1[/img][img]url2[/img] after"
    images = [
        Image(text_pos_start=0, text_pos_end=15, is_heading=False, url="url1"),
        Image(text_pos_start=15, text_pos_end=30, is_heading=False, url="url2"),
    ]
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=images, youtube=[])
    blocks = extractor.extract()
    assert any(b.text == "after" for b in blocks)


def test_textblock_extractor_empty_list_not_treated_as_none():
    # An explicitly passed empty list [] must be respected as "no items",
    # not silently replaced by a fresh extractor run (the `x or Extractor()`
    # pattern would treat [] as falsy and re-extract, causing position bugs).
    text = "[img]https://example.com/image.png[/img] after"
    # Pass images=[] explicitly — no images should be registered as content,
    # so the whole text (including the raw [img] tag) becomes one TextBlock.
    extractor = TextBlockExtractor(text, videos=[], carousel=[], images=[], youtube=[])
    blocks = extractor.extract()
    # With images=[] respected, __content is empty → single block covering full text.
    assert len(blocks) == 1
    assert blocks[0].text == text.strip()


def test_textblock_extractor_empty_images_with_carousel_no_stray_closing_tag():
    # Regression test: when ContentExtractor deduplicates images inside a
    # carousel to an empty list and passes images=[] to TextBlockExtractor,
    # the text between two carousels must NOT start with [/carousel].
    #
    # The buggy `images = images or ImageExtractor(...)` call would discard
    # the empty list, re-extract all images (including those inside the
    # carousel), and corrupt text_pos so a TextBlock was created starting at
    # the end of the last [img] inside carousel — right before [/carousel].
    inner = "[img]https://example.com/1.png[/img][img]https://example.com/2.png[/img]"
    text = f"intro [carousel]{inner}[/carousel] middle [carousel]{inner}[/carousel] end"

    c1_start = text.index("[carousel]")
    c1_end = text.index("[/carousel]") + len("[/carousel]")
    c2_start = text.rindex("[carousel]")
    c2_end = text.rindex("[/carousel]") + len("[/carousel]")

    carousel = [
        Carousel(text_pos_start=c1_start, text_pos_end=c1_end, is_heading=False, images=[]),
        Carousel(text_pos_start=c2_start, text_pos_end=c2_end, is_heading=False, images=[]),
    ]

    extractor = TextBlockExtractor(text, videos=[], carousel=carousel, images=[], youtube=[])
    blocks = extractor.extract()

    for block in blocks:
        assert "[/carousel]" not in block.text, (
            f"Stray [/carousel] found in TextBlock: {block.text!r}"
        )
        assert "[carousel]" not in block.text, (
            f"Stray [carousel] found in TextBlock: {block.text!r}"
        )
