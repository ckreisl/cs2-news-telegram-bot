from __future__ import annotations

import pytest

from cs2posts.parser.steam2telegram_html import Steam2TelegramHTML


@pytest.fixture
def steam2telegram_html():
    return Steam2TelegramHTML("tests")


def test_steam2telegram_html_sanitize_gt(steam2telegram_html):
    steam2telegram_html.text = '>'
    expected = '&gt;'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_sanitize_lt(steam2telegram_html):
    steam2telegram_html.text = '<'
    expected = '&lt;'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_sanitize_amp(steam2telegram_html):
    steam2telegram_html.text = '&'
    expected = '&amp;'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_sanitize_multiple(steam2telegram_html):
    steam2telegram_html.text = '&&<><><'
    expected = '&amp;&amp;&lt;&gt;&lt;&gt;&lt;'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_dash(steam2telegram_html):
    steam2telegram_html.text = '--'
    expected = '—'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_sanitize_p_tag_empty(steam2telegram_html):
    steam2telegram_html.text = '[p][/p]'
    expected = '\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_sanitize_p_tag(steam2telegram_html):
    steam2telegram_html.text = '[p]foobar[/p]'
    expected = 'foobar'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h2_tag(steam2telegram_html):
    steam2telegram_html.text = '[h2]Heading 2[/h2]'
    expected = '\n\n<b>Heading 2</b>\n\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h2_tag_empty(steam2telegram_html):
    steam2telegram_html.text = '[h2][/h2]'
    expected = '\n\n<b></b>\n\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h2_tag_with_content(steam2telegram_html):
    steam2telegram_html.text = 'before [h2]title[/h2] after'
    expected = 'before \n\n<b>title</b>\n\n after'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h3_tag(steam2telegram_html):
    steam2telegram_html.text = '[h3]Heading 3[/h3]'
    expected = '\n\n<b>Heading 3</b>\n\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h3_tag_empty(steam2telegram_html):
    steam2telegram_html.text = '[h3][/h3]'
    expected = '\n\n<b></b>\n\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h3_tag_with_content(steam2telegram_html):
    steam2telegram_html.text = 'before [h3]subtitle[/h3] after'
    expected = 'before \n\n<b>subtitle</b>\n\n after'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h2_case_insensitive(steam2telegram_html):
    steam2telegram_html.text = '[H2]Upper Case[/H2]'
    expected = '\n\n<b>Upper Case</b>\n\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_h3_case_insensitive(steam2telegram_html):
    steam2telegram_html.text = '[H3]Upper Case[/H3]'
    expected = '\n\n<b>Upper Case</b>\n\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_multiple_h2_tags(steam2telegram_html):
    steam2telegram_html.text = '[h2]First[/h2][h2]Second[/h2]'
    expected = '\n\n<b>First</b>\n\n<b>Second</b>\n\n'
    assert steam2telegram_html.parse() == expected


def test_steam2telegram_html_mixed_h2_h3_tags(steam2telegram_html):
    steam2telegram_html.text = '[h2]Main[/h2][h3]Sub[/h3]'
    expected = '\n\n<b>Main</b>\n\n<b>Sub</b>\n\n'
    assert steam2telegram_html.parse() == expected
