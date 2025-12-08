from __future__ import annotations

from unittest.mock import patch

from cs2posts.content.content import Carousel
from cs2posts.content.extractor_carousel import CarouselExtractor


def test_carousel_extractor_extract_single_carousel():
    text = '[carousel][img src="https://example.com/image1.png"][/img][img src="https://example.com/image2.png"][/img][/carousel]'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = lambda x: x
        carousels = extractor.extract()
    assert len(carousels) == 1
    assert isinstance(carousels[0], Carousel)


def test_carousel_extractor_extract_multiple_carousels():
    text = '[carousel][img src="https://example.com/image1.png"][/img][/carousel] text [carousel][img src="https://example.com/image2.png"][/img][/carousel]'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = lambda x: x
        carousels = extractor.extract()
    assert len(carousels) == 2


def test_carousel_extractor_extract_no_carousels():
    text = "no carousels here"
    extractor = CarouselExtractor(text)
    carousels = extractor.extract()
    assert len(carousels) == 0


def test_carousel_extractor_extract_empty_string():
    text = ""
    extractor = CarouselExtractor(text)
    carousels = extractor.extract()
    assert len(carousels) == 0


def test_carousel_extractor_extract_carousel_with_images():
    text = '[carousel][img src="https://example.com/image1.png"][/img][img src="https://example.com/image2.png"][/img][/carousel]'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = ["https://example.com/image1.png", "https://example.com/image2.png"]
        carousels = extractor.extract()
    assert len(carousels[0].images) == 2


def test_carousel_extractor_extract_carousel_positions():
    text = '[carousel][img src="https://example.com/image.png"][/img][/carousel]'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        carousels = extractor.extract()
    assert carousels[0].text_pos_start == 0
    assert carousels[0].text_pos_end == len(text)


def test_carousel_extractor_extract_is_heading_false():
    text = '[carousel][img src="https://example.com/image.png"][/img][/carousel]'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        carousels = extractor.extract()
    assert carousels[0].is_heading is False


def test_carousel_extractor_extract_empty_carousel():
    text = '[carousel][/carousel]'
    extractor = CarouselExtractor(text)
    carousels = extractor.extract()
    assert len(carousels) == 1
    assert len(carousels[0].images) == 0


def test_carousel_extractor_extract_carousel_with_text_between():
    text = 'before [carousel][img src="https://example.com/image.png"][/img][/carousel] after'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        carousels = extractor.extract()
    assert len(carousels) == 1
    assert carousels[0].text_pos_start == 7
    assert carousels[0].text_pos_end == len(text) - 6


def test_carousel_extractor_extract_nested_content():
    text = '[carousel][img src="https://example.com/img1.png"][/img] some text [img src="https://example.com/img2.png"][/img][/carousel]'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = ["https://example.com/img1.png", "https://example.com/img2.png"]
        carousels = extractor.extract()
    assert len(carousels) == 1
    assert len(carousels[0].images) == 2


def test_carousel_extractor_extract_deprecated_image_format():
    text = '[carousel][img]https://example.com/image.png[/img][/carousel]'
    extractor = CarouselExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        carousels = extractor.extract()
    assert len(carousels) == 1
    assert len(carousels[0].images) == 1
