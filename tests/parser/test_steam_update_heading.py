from __future__ import annotations

import pytest

from cs2posts.parser.steam_update_heading import SteamUpdateHeadingParser


@pytest.fixture
def steam_parser():
    return SteamUpdateHeadingParser("tests")


def test_steam_update_heading_parser_single_char(steam_parser):
    steam_parser.text = "\n[A]\n"
    assert steam_parser.parse() == "\n[A]\n"


def test_steam_update_heading_parser(steam_parser):
    steam_parser.text = "\n[HELLO WORLD]\n"
    assert steam_parser.parse() == "\n<b>[HELLO WORLD]</b>\n\n"


def test_steam_update_heading_beginning(steam_parser):
    steam_parser.text = "[HELLO WORLD]\n"
    assert steam_parser.parse() == "<b>[HELLO WORLD]</b>\n\n"


def test_stean_update_heading_numbers(steam_parser):
    steam_parser.text = "\n[123]\n"
    assert steam_parser.parse() == "\n<b>[123]</b>\n\n"


def test_steam_update_heading_parser_no_heading(steam_parser):
    expected = "This is just some text with [CT] in the middle."
    steam_parser.text = expected
    assert steam_parser.parse() == expected


def test_steam_update_heading_parser_multiple(steam_parser):
    steam_parser.text = "\n[INVENTORY & ITEMS]\n"
    assert steam_parser.parse() == "\n<b>[INVENTORY & ITEMS]</b>\n\n"


def test_steam_update_heading_parser_vacnet(steam_parser):
    steam_parser.text = "\n[ VacNet ]\n"
    assert steam_parser.parse() == "\n<b>[ VacNet ]</b>\n\n"


def test_steam_update_heading_parser_identifier(steam_parser):
    steam_parser.text = "start[MAPS]Some text"
    assert steam_parser.parse() == "start<b>[MAPS]</b>\nSome text"


def test_steam_update_heading_parser_leading_backslash(steam_parser):
    steam_parser.text = "\n\\[MAPS]\n"
    assert steam_parser.parse() == "\n<b>[MAPS]</b>\n\n"


def test_steam_update_heading_parser_leading_backslash_by_heading_item(steam_parser):
    steam_parser.text = "start\\[ITEMS]Some text"
    assert steam_parser.parse() == "start<b>[ITEMS]</b>\nSome text"


def test_steam_update_heading_parser_leading_backslash_hyphenated_heading(steam_parser):
    steam_parser.text = "\n\\[ X-Ray Scanner ]\n"
    assert steam_parser.parse() == "\n<b>[ X-Ray Scanner ]</b>\n\n"


def test_steam_update_heading_parser_keeps_existing_blank_line(steam_parser):
    steam_parser.text = "\n[MAP GUIDES]\n\n• test"
    assert steam_parser.parse() == "\n<b>[MAP GUIDES]</b>\n\n• test"
