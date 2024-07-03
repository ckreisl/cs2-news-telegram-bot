from __future__ import annotations

from unittest.mock import patch

from cs2posts.bot.utils import Utils


def test_is_valid_url_valid():
    url = "https://example.com"
    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = True
        is_valid = Utils.is_valid_url(url)
    assert is_valid


def test_is_valid_url_invalid():
    url = "example.com"
    assert not Utils.is_valid_url(url)

    url = "https://www.google.com"
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception
        is_valid = Utils.is_valid_url(url)
    assert not is_valid


def test_get_redirected_url_same_url():
    url = "https://example.com"
    with patch("requests.get") as mock_get:
        mock_get.return_value.url = url
        redirected_url = Utils.get_redirected_url(url)
    assert redirected_url == url


def test_get_redirected_url_redirected():
    url = "https://nonexistenturl.com"
    expected = "https://foobar.com"
    with patch("requests.get") as mock_get:
        mock_get.return_value.url = expected
        redirected_url = Utils.get_redirected_url(url)
    assert redirected_url == expected


def test_get_redirected_url_exception():
    url = "https://example.com"
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception
        redirected_url = Utils.get_redirected_url(url)
    assert redirected_url == url
