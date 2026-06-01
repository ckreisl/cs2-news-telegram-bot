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


def test_steam_news_youtube_parser_is_case_insensitive(steam_parser):
    steam_parser.text = "[PREVIEWYOUTUBE=123][/PREVIEWYOUTUBE]"
    expected = '<a href="https://www.youtube.com/watch?v=123">YouTube Video</a>'
    assert steam_parser.parse() == expected


def test_steam_news_youtube_parser_replaces_all_occurrences(steam_parser):
    steam_parser.text = (
        "[previewyoutube=1][/previewyoutube]"
        "[previewyoutube=2][/previewyoutube]"
        "[previewyoutube=3][/previewyoutube]"
    )
    result = steam_parser.parse()
    # Regression: flags were previously passed as the `count` arg, capping
    # substitutions at 2 and disabling IGNORECASE.
    assert result.count("youtube.com/watch") == 3
