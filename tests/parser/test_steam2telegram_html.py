from __future__ import annotations

import pytest

from cs2posts.parser.steam2telegram_html import Steam2TelegramHTML


@pytest.fixture
def steam2telegram_html():
    return Steam2TelegramHTML()


def test_steam2telegram_html_sanitize_gt(steam2telegram_html):
    text = ">"
    expected = "&gt;"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_sanitize_lt(steam2telegram_html):
    text = "<"
    expected = "&lt;"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_sanitize_amp(steam2telegram_html):
    text = "&"
    expected = "&amp;"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_sanitize_multiple(steam2telegram_html):
    text = "&&<><><"
    expected = "&amp;&amp;&lt;&gt;&lt;&gt;&lt;"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_dash(steam2telegram_html):
    text = "--"
    expected = "—"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_sanitize_p_tag_empty(steam2telegram_html):
    text = "[p][/p]"
    expected = "\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_sanitize_p_tag(steam2telegram_html):
    text = "[p]foobar[/p]"
    expected = "foobar"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h2_tag(steam2telegram_html):
    text = "[h2]Heading 2[/h2]"
    expected = "\n\n<b>Heading 2</b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h2_tag_empty(steam2telegram_html):
    text = "[h2][/h2]"
    expected = "\n\n<b></b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h2_tag_with_content(steam2telegram_html):
    text = "before [h2]title[/h2] after"
    expected = "before\n\n<b>title</b>\n\n after"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h3_tag(steam2telegram_html):
    text = "[h3]Heading 3[/h3]"
    expected = "\n\n<b>Heading 3</b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h3_tag_empty(steam2telegram_html):
    text = "[h3][/h3]"
    expected = "\n\n<b></b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h3_tag_with_content(steam2telegram_html):
    text = "before [h3]subtitle[/h3] after"
    expected = "before\n\n<b>subtitle</b>\n\n after"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h2_case_insensitive(steam2telegram_html):
    text = "[H2]Upper Case[/H2]"
    expected = "\n\n<b>Upper Case</b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_h3_case_insensitive(steam2telegram_html):
    text = "[H3]Upper Case[/H3]"
    expected = "\n\n<b>Upper Case</b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_multiple_h2_tags(steam2telegram_html):
    text = "[h2]First[/h2][h2]Second[/h2]"
    expected = "\n\n<b>First</b>\n\n<b>Second</b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_mixed_h2_h3_tags(steam2telegram_html):
    text = "[h2]Main[/h2][h3]Sub[/h3]"
    expected = "\n\n<b>Main</b>\n\n<b>Sub</b>\n\n"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_strike_tag(steam2telegram_html):
    text = "[strike]some text[/strike]"
    expected = "some text"
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_strike_tag_empty(steam2telegram_html):
    text = "[strike][/strike]"
    expected = ""
    assert steam2telegram_html.parse(text) == expected


def test_steam2telegram_html_p_with_strike_tag(steam2telegram_html):
    text = "[p][strike]text[/strike][/p]"
    expected = "text"
    assert steam2telegram_html.parse(text) == expected


def test_parsing_twice_yields_the_same_result(steam2telegram_html):
    """Regression: parsers used to write results back onto themselves, so a
    second call re-escaped the HTML the first call had produced."""
    text = "[h2]Title[/h2][list][*]one[*]two[/list]"

    first = steam2telegram_html.parse(text)
    second = steam2telegram_html.parse(text)

    assert first == second


def test_a_parser_instance_is_reusable_across_posts(steam2telegram_html):
    assert steam2telegram_html.parse("[h2]A[/h2]") != steam2telegram_html.parse(
        "[h2]B[/h2]"
    )
    assert steam2telegram_html.parse("[h2]A[/h2]") == "\n\n<b>A</b>\n\n"


def test_sub_parsers_run_in_priority_order():
    from cs2posts.parser import Steam2TelegramHTML

    order = []

    class Recorder:
        def __init__(self, name: str) -> None:
            self.name = name

        def parse(self, text: str) -> str:
            order.append(self.name)
            return text

    parser = Steam2TelegramHTML()
    parser.add_parser(Recorder("third"), priority=3)
    parser.add_parser(Recorder("first"), priority=1)
    parser.add_parser(Recorder("second"), priority=2)

    parser.parse("text")

    assert order == ["first", "second", "third"]
