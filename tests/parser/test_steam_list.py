from __future__ import annotations

import pytest

from cs2posts.parser.steam_list import SteamListParser


@pytest.fixture
def steam_list_parser():
    return SteamListParser("tests")


def test_steam_list_parser_list_item(steam_list_parser):
    steam_list_parser.text = '<ul><li>Hello World</li></ul>'
    expected = f'\n{steam_list_parser.LIST_ITEM_ICON} Hello World\n\n'
    assert steam_list_parser.parse() == expected


def test_steam_list_parser_list_item_entry(steam_list_parser):
    steam_list_parser.text = '<li>Hello World</li>'
    expected = f'{steam_list_parser.LIST_ITEM_ICON} Hello World\n'
    assert steam_list_parser.parse() == expected


def test_steam_list_parser_nested_list(steam_list_parser):
    steam_list_parser.text = """<ul><li>Foo</li><ul><li>Bar</li></ul><li>Hello World</li></ul>"""
    expected = '\n• Foo\n    ◦ Bar\n• Hello World\n\n'
    assert steam_list_parser.parse() == expected
