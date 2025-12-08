from __future__ import annotations

from unittest.mock import patch

from cs2posts.content.content import Carousel
from cs2posts.content.content import Image
from cs2posts.content.content import TextBlock
from cs2posts.content.content import Video
from cs2posts.content.content import Youtube
from cs2posts.content.extractor_content import ContentExtractor


def test_content_extractor_extract_empty_string():
    text = ""
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = ""
        content = extractor.extract()
    # Should return at least one content item (text block)
    assert len(content) >= 1


def test_content_extractor_extract_plain_text():
    text = "This is plain text"
    extractor = ContentExtractor(text)
    content = extractor.extract()
    assert len(content) >= 1
    assert content[0].is_heading is True


def test_content_extractor_first_item_is_heading():
    text = "Some text"
    extractor = ContentExtractor(text)
    content = extractor.extract()
    assert content[0].is_heading is True


def test_content_extractor_extract_with_image():
    text = 'text [img src="https://example.com/image.png"][/img]'
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        content = extractor.extract()
    assert len(content) >= 1
    assert any(isinstance(c, Image) for c in content)


def test_content_extractor_extract_with_video():
    text = 'text [video mp4="https://example.com/video.mp4"][/video]'
    extractor = ContentExtractor(text)
    content = extractor.extract()
    assert len(content) >= 1
    assert any(isinstance(c, Video) for c in content)


def test_content_extractor_extract_with_youtube():
    text = 'text [previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]'
    extractor = ContentExtractor(text)
    content = extractor.extract()
    assert len(content) >= 1
    assert any(isinstance(c, Youtube) for c in content)


def test_content_extractor_extract_with_carousel():
    text = 'text [carousel][img src="https://example.com/image.png"][/img][/carousel]'
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        content = extractor.extract()
    assert len(content) >= 1
    assert any(isinstance(c, Carousel) for c in content)


def test_content_extractor_sorted_by_position():
    text = '[previewyoutube=abc;full][/previewyoutube] [video mp4="https://example.com/video.mp4"][/video]'
    extractor = ContentExtractor(text)
    content = extractor.extract()
    # Verify content is sorted by text_pos_start
    positions = [c.text_pos_start for c in content]
    assert positions == sorted(positions)


def test_content_extractor_removes_carousel_images():
    text = '[carousel][img src="https://example.com/image.png"][/img][/carousel] [img src="https://example.com/image.png"][/img]'
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        content = extractor.extract()
    # Images that are in carousel should be removed from standalone images
    standalone_images = [c for c in content if isinstance(c, Image)]
    carousel_items = [c for c in content if isinstance(c, Carousel)]
    if carousel_items:
        carousel_urls = {img.url for c in carousel_items for img in c.images}
        for img in standalone_images:
            assert img.url not in carousel_urls


def test_content_extractor_extract_mixed_content():
    text = 'header text [img src="https://example.com/image.png"][/img] middle [previewyoutube=abc;full][/previewyoutube] end'
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        content = extractor.extract()
    assert len(content) >= 3  # At least text, image, and youtube


def test_content_extractor_extract_all_types():
    text = '''start [img src="https://example.com/img.png"][/img]
    [video mp4="https://example.com/video.mp4"][/video]
    [carousel][img src="https://example.com/carousel.png"][/img][/carousel]
    [previewyoutube=vid123;full][/previewyoutube] end'''
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = lambda x: x
        content = extractor.extract()

    types_found = {type(c) for c in content}
    # Should have at least TextBlock and some media types
    assert TextBlock in types_found


def test_content_extractor_carousel_removes_duplicate_images():
    # Image inside carousel and same image outside should result in only carousel containing it
    carousel_img_url = "https://example.com/same_image.png"
    text = f'[carousel][img src="{carousel_img_url}"][/img][/carousel] [img src="{carousel_img_url}"][/img]'
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = carousel_img_url
        content = extractor.extract()

    standalone_images = [c for c in content if isinstance(c, Image)]
    # The standalone image should be filtered out since it's in the carousel
    assert len(standalone_images) == 0


def test_content_extractor_no_carousel_keeps_images():
    text = '[img src="https://example.com/image1.png"][/img] [img src="https://example.com/image2.png"][/img]'
    extractor = ContentExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = ["https://example.com/image1.png", "https://example.com/image2.png"]
        content = extractor.extract()

    images = [c for c in content if isinstance(c, Image)]
    assert len(images) == 2
