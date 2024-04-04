from __future__ import annotations

import pytest

from cs2posts.parser.steam_news_image import SteamNewsImageParser


@pytest.fixture
def steam_parser():
    return SteamNewsImageParser("tests")


def test_steam_news_image_parser_empty(steam_parser):
    steam_parser.text = '<a href="https://example.com"><img src="https://example.com/image.jpg" alt="Hello World">Image</a>[img]https://example.com/image.jpg[/img]'
    assert steam_parser.parse() == ""


def test_steam_news_image_parser_text(steam_parser):
    steam_parser.text = '<a href="https://example.com"><img src="https://example.com/image.jpg" alt="Hello World">Image</a>[img]https://example.com/image.jpg[/img]Text'
    assert steam_parser.parse() == "Text"


def test_steam_news_image_parser_removes_only_first_image(steam_parser):
    first_image = '<a href="https://example.com"><img src="https://example.com/image.jpg" alt="Hello">Image1</a>'
    second_image = '<a href="https://example2.com"><img src="https://example.com/image2.jpg" alt="World">Image2</a>'
    steam_parser.text = first_image + second_image
    assert steam_parser.parse() == second_image
