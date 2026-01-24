from __future__ import annotations

from unittest.mock import patch

import pytest

from cs2posts.content.content import Image
from cs2posts.content.extractor_image import extract_images
from cs2posts.content.extractor_image import extract_images_deprecated
from cs2posts.content.extractor_image import ImageExtractor


# Tests for extract_images_deprecated function
def test_extract_images_deprecated_single_image():
    text = "[img]https://example.com/image.png[/img]"
    matches = list(extract_images_deprecated(text))
    assert len(matches) == 1
    assert matches[0].group(1) == "https://example.com/image.png"


def test_extract_images_deprecated_multiple_images():
    text = "[img]https://example.com/image1.png[/img] some text [img]https://example.com/image2.png[/img]"
    matches = list(extract_images_deprecated(text))
    assert len(matches) == 2
    assert matches[0].group(1) == "https://example.com/image1.png"
    assert matches[1].group(1) == "https://example.com/image2.png"


def test_extract_images_deprecated_no_images():
    text = "no images here"
    matches = list(extract_images_deprecated(text))
    assert len(matches) == 0


def test_extract_images_deprecated_empty_string():
    text = ""
    matches = list(extract_images_deprecated(text))
    assert len(matches) == 0


# Tests for extract_images function
def test_extract_images_single_image():
    text = '[img src="https://example.com/image.png"][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 1
    # Group 2 is for standard double quotes
    assert matches[0].group(2) == "https://example.com/image.png"


def test_extract_images_html_encoded_quotes():
    text = '[img src=&quot;https://example.com/image.png&quot;][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 1
    # Group 1 is for html encoded quotes
    assert matches[0].group(1) == "https://example.com/image.png"


def test_extract_images_multiple_images():
    text = '[img src="https://example.com/image1.png"][/img] text [img src="https://example.com/image2.png"][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 2
    assert matches[0].group(2) == "https://example.com/image1.png"
    assert matches[1].group(2) == "https://example.com/image2.png"


def test_extract_images_no_images():
    text = "no images here"
    matches = list(extract_images(text))
    assert len(matches) == 0


def test_extract_images_empty_string():
    text = ""
    matches = list(extract_images(text))
    assert len(matches) == 0


def test_extract_images_with_additional_attributes():
    text = '[img src="https://example.com/image.png" width="100" height="200"][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 1
    assert matches[0].group(2) == "https://example.com/image.png"


def test_extract_images_mixed_quote_types():
    text = '[img src="https://example.com/1.png"][/img] [img src=&quot;https://example.com/2.png&quot;][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 2
    assert matches[0].group(2) == "https://example.com/1.png"
    assert matches[1].group(1) == "https://example.com/2.png"


def test_extract_images_html_encoded_quotes_containing_quotes():
    url = 'https://example.com/image_with_"quote".png'
    text = f'[img src=&quot;{url}&quot;][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 1
    assert matches[0].group(1) == url


def test_extract_images_empty_src_quoted():
    text = '[img src=""][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 1
    assert matches[0].group(2) == ""


def test_extract_images_empty_src_html_encoded():
    text = '[img src=&quot;&quot;][/img]'
    matches = list(extract_images(text))
    assert len(matches) == 1
    assert matches[0].group(1) == ""


# Tests for ImageExtractor class
@pytest.fixture
def image_extractor():
    text = '[img src="https://example.com/image.png"][/img]'
    return ImageExtractor(text)


def test_image_extractor_extract_single_image():
    text = '[img src="https://example.com/image.png"][/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        images = extractor.extract()
    assert len(images) == 1
    assert isinstance(images[0], Image)
    assert images[0].url == "https://example.com/image.png"


def test_image_extractor_extract_multiple_images():
    text = '[img src="https://example.com/image1.png"][/img] [img src="https://example.com/image2.png"][/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = ["https://example.com/image1.png", "https://example.com/image2.png"]
        images = extractor.extract()
    assert len(images) == 2
    assert images[0].url == "https://example.com/image1.png"
    assert images[1].url == "https://example.com/image2.png"


def test_image_extractor_extract_no_images():
    text = "no images here"
    extractor = ImageExtractor(text)
    images = extractor.extract()
    assert len(images) == 0


def test_image_extractor_extract_empty_string():
    text = ""
    extractor = ImageExtractor(text)
    images = extractor.extract()
    assert len(images) == 0


def test_image_extractor_extract_deprecated_format():
    text = "[img]https://example.com/image.png[/img]"
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        images = extractor.extract()
    assert len(images) == 1
    assert images[0].url == "https://example.com/image.png"


def test_image_extractor_extract_mixed_formats():
    text = '[img src="https://example.com/image1.png"][/img] [img]https://example.com/image2.png[/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.side_effect = ["https://example.com/image1.png", "https://example.com/image2.png"]
        images = extractor.extract()
    assert len(images) == 2


def test_image_extractor_extract_with_html_encoded_quot():
    text = '[img src="https://example.com/image.png&quot;"][/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        images = extractor.extract()
    assert len(images) == 1


def test_image_extractor_extract_skips_empty_url():
    text = '[img src="https://example.com/image.png"][/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = ""
        images = extractor.extract()
    assert len(images) == 0


def test_image_extractor_extract_image_positions():
    text = '[img src="https://example.com/image.png"][/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        images = extractor.extract()
    assert images[0].text_pos_start == 0
    assert images[0].text_pos_end == len(text)


def test_image_extractor_extract_is_heading_false():
    text = '[img src="https://example.com/image.png"][/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://example.com/image.png"
        images = extractor.extract()
    assert images[0].is_heading is False


def test_image_extractor_extract_steam_clan_image():
    text = '[img src="{STEAM_CLAN_IMAGE}/foo/bar.png"][/img]'
    extractor = ImageExtractor(text)
    with patch("cs2posts.content.extractor_image.Utils.resolve_steam_clan_image_url") as mock_resolve:
        mock_resolve.return_value = "https://clan.akamai.steamstatic.com/images/foo/bar.png"
        images = extractor.extract()
    assert len(images) == 1
    assert images[0].url == "https://clan.akamai.steamstatic.com/images/foo/bar.png"
