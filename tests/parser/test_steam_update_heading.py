from __future__ import annotations

import pytest

from cs2posts.parser.steam_update_heading import SteamUpdateHeadingParser


@pytest.fixture
def steam_parser():
    return SteamUpdateHeadingParser("tests")


def test_steam_update_heading_parser(steam_parser):
    steam_parser.text = "\n[HELLO WORLD]\n"
    assert steam_parser.parse() == "\n<b>[HELLO WORLD]</b>\n"


def test_steam_update_heading_beginning(steam_parser):
    steam_parser.text = "[HELLO WORLD]\n"
    assert steam_parser.parse() == "<b>[HELLO WORLD]</b>\n"


def test_stean_update_heading_numbers(steam_parser):
    steam_parser.text = "\n[123]\n"
    assert steam_parser.parse() == "\n<b>[123]</b>\n"


def test_steam_update_heading_parser_no_heading(steam_parser):
    expected = "This is just some text with [CT] in the middle."
    steam_parser.text = expected
    assert steam_parser.parse() == expected
