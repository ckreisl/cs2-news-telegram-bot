from __future__ import annotations

from cs2posts.parser.steam_news_table import SteamNewsTableParser


def test_steam_news_table_parser_extracts_table_to_pre() -> None:
    text = (
        '[table]\n'
        '[tr][th]Position[/th][th]Royalty[/th][/tr]\n'
        '[tr][td]Tournament Organizer[/td][td]5.0%[/td][/tr]\n'
        '[tr][td]1[/td][td]2.85%[/td][/tr]\n'
        '[/table]'
    )

    result = SteamNewsTableParser(text).parse()

    expected = (
        '<pre>Position             | Royalty\n'
        'Tournament Organizer | 5.0%\n'
        '1                    | 2.85%</pre>'
    )

    assert result == expected


def test_steam_news_table_parser_leaves_non_table_text_untouched() -> None:
    text = (
        'Intro text\n'
        '[table]\n'
        '[tr][td]A[/td][td]B[/td][/tr]\n'
        '[/table]\n'
        'Outro text'
    )

    result = SteamNewsTableParser(text).parse()

    expected = (
        'Intro text\n'
        '<pre>A | B</pre>\n'
        'Outro text'
    )

    assert result == expected
