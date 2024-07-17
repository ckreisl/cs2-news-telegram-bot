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
    steam2telegram_html.parse() == expected
