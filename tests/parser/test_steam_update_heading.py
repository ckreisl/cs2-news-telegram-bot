from __future__ import annotations

import pytest

from cs2posts.parser.steam_update_heading import SteamUpdateHeadingParser


@pytest.fixture
def steam_parser():
    return SteamUpdateHeadingParser()


def test_steam_update_heading_parser_single_char(steam_parser):
    text = "\n[A]\n"
    assert steam_parser.parse(text) == "\n[A]\n"


def test_steam_update_heading_parser(steam_parser):
    text = "\n[HELLO WORLD]\n"
    assert steam_parser.parse(text) == "\n\n<b>[HELLO WORLD]</b>\n\n"


def test_steam_update_heading_beginning(steam_parser):
    text = "[HELLO WORLD]\n"
    assert steam_parser.parse(text) == "<b>[HELLO WORLD]</b>\n\n"


def test_stean_update_heading_numbers(steam_parser):
    text = "\n[123]\n"
    assert steam_parser.parse(text) == "\n\n<b>[123]</b>\n\n"


def test_steam_update_heading_parser_no_heading(steam_parser):
    expected = "This is just some text with [CT] in the middle."
    text = expected
    assert steam_parser.parse(text) == expected


def test_steam_update_heading_parser_multiple(steam_parser):
    text = "\n[INVENTORY & ITEMS]\n"
    assert steam_parser.parse(text) == "\n\n<b>[INVENTORY & ITEMS]</b>\n\n"


def test_steam_update_heading_parser_vacnet(steam_parser):
    text = "\n[ VacNet ]\n"
    assert steam_parser.parse(text) == "\n\n<b>[ VacNet ]</b>\n\n"


def test_steam_update_heading_parser_identifier(steam_parser):
    text = "start[MAPS]Some text"
    assert steam_parser.parse(text) == "start<b>[MAPS]</b>\nSome text"


def test_steam_update_heading_parser_leading_backslash(steam_parser):
    text = "\n\\[MAPS]\n"
    assert steam_parser.parse(text) == "\n\n<b>[MAPS]</b>\n\n"


def test_steam_update_heading_parser_leading_backslash_by_heading_item(steam_parser):
    text = "start\\[ITEMS]Some text"
    assert steam_parser.parse(text) == "start<b>[ITEMS]</b>\nSome text"


def test_steam_update_heading_parser_leading_backslash_hyphenated_heading(steam_parser):
    text = "\n\\[ X-Ray Scanner ]\n"
    assert steam_parser.parse(text) == "\n\n<b>[ X-Ray Scanner ]</b>\n\n"


def test_steam_update_heading_parser_keeps_existing_blank_line(steam_parser):
    text = "\n[MAP GUIDES]\n\n• test"
    assert steam_parser.parse(text) == "\n\n<b>[MAP GUIDES]</b>\n\n• test"


def test_steam_update_heading_parser_ignores_img_tags(steam_parser):
    expected = "Some text:\n\n[img]https://example.com/image.png[/img]\nMore text."
    text = expected
    assert steam_parser.parse(text) == expected


@pytest.mark.parametrize(
    "tag", ["img", "/img", "video", "/video", "carousel", "/carousel", "IMG", "/IMG"]
)
def test_steam_update_heading_parser_ignores_bbcode_tags(steam_parser, tag):
    expected = f"\n[{tag}]\n"
    text = expected
    assert steam_parser.parse(text) == expected
