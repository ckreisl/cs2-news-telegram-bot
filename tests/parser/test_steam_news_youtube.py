from __future__ import annotations

import pytest

from cs2posts.parser.steam_news_youtube import SteamNewsYoutubeParser


@pytest.fixture
def steam_parser():
    return SteamNewsYoutubeParser("tests")


def test_steam_news_youtube_parser(steam_parser):
    steam_parser.text = "[previewyoutube=123][/previewyoutube]"
    expected = '<a href="https://www.youtube.com/watch?v=123">YouTube Video</a>'
    assert steam_parser.parse() == expected
