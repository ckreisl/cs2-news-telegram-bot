from __future__ import annotations

import pytest

from cs2posts.content.content import Image
from cs2posts.content.extractor_image import ImageExtractor


def urls_in(text: str) -> list[str]:
    return [image.url for image in ImageExtractor(text).extract()]


def test_extracts_a_quoted_src():
    assert urls_in('[img src="https://example.com/image.png"][/img]') == [
        "https://example.com/image.png"
    ]


def test_extracts_an_entity_quoted_src():
    assert urls_in("[img src=&quot;https://example.com/image.png&quot;][/img]") == [
        "https://example.com/image.png"
    ]


def test_extracts_the_legacy_bare_form():
    assert urls_in("[img]https://example.com/image.png[/img]") == [
        "https://example.com/image.png"
    ]


def test_extracts_several_images_in_order():
    text = (
        '[img src="https://example.com/1.png"][/img] text'
        ' [img src="https://example.com/2.png"][/img]'
    )

    assert urls_in(text) == ["https://example.com/1.png", "https://example.com/2.png"]


def test_extracts_both_markup_forms_from_one_body():
    text = (
        '[img src="https://example.com/1.png"][/img]'
        " [img]https://example.com/2.png[/img]"
    )

    assert sorted(urls_in(text)) == [
        "https://example.com/1.png",
        "https://example.com/2.png",
    ]


def test_extracts_mixed_quote_styles():
    text = (
        '[img src="https://example.com/1.png"][/img]'
        " [img src=&quot;https://example.com/2.png&quot;][/img]"
    )

    assert urls_in(text) == ["https://example.com/1.png", "https://example.com/2.png"]


def test_ignores_extra_attributes():
    text = '[img src="https://example.com/image.png" width="100" height="200"][/img]'

    assert urls_in(text) == ["https://example.com/image.png"]


def test_strips_stray_entity_quotes_from_the_url():
    text = '[img src="https://example.com/image.png&quot;"][/img]'

    assert urls_in(text) == ["https://example.com/image.png"]


@pytest.mark.parametrize(
    "text",
    ["", "no images here", '[img src=""][/img]', "[img src=&quot;&quot;][/img]"],
)
def test_yields_nothing_without_a_usable_image(text):
    assert urls_in(text) == []


def test_records_the_span_and_defaults_to_not_a_heading():
    text = '[img src="https://example.com/image.png"][/img]'

    (image,) = ImageExtractor(text).extract()

    assert isinstance(image, Image)
    assert (image.text_pos_start, image.text_pos_end) == (0, len(text))
    assert image.is_heading is False


def test_resolves_the_steam_clan_image_placeholder(http_response):
    http_response(status_code=200)
    text = '[img src="{STEAM_CLAN_IMAGE}/foo/bar.png"][/img]'

    assert urls_in(text) == ["https://clan.akamai.steamstatic.com/images/foo/bar.png"]


def test_falls_back_to_the_placeholder_when_no_cdn_answers(http_response):
    http_response(status_code=500)
    text = '[img src="{STEAM_CLAN_IMAGE}/foo/bar.png"][/img]'

    assert urls_in(text) == ["{STEAM_CLAN_IMAGE}/foo/bar.png"]
