from __future__ import annotations

from unittest.mock import patch

from cs2posts.utils import Utils


def test_is_valid_url_valid():
    url = "https://example.com"
    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = True
        is_valid = Utils.is_valid_url(url)
    assert is_valid


def test_is_valid_url_invalid_url_none():
    assert not Utils.is_valid_url(None)


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


def test_resolve_steam_clan_image_url_valid_url():
    text = "{STEAM_CLAN_IMAGE}"
    expected = "https://clan.akamai.steamstatic.com/images"
    with patch("cs2posts.utils.Utils.is_valid_url") as mock_is_valid_url:
        mock_is_valid_url.return_value = True
        resolved_url = Utils.resolve_steam_clan_image_url(text)
    assert resolved_url == expected


def test_resolve_steam_clan_image_url_invalid_url():
    text = "{STEAM_CLAN_IMAGE}"
    with patch("cs2posts.utils.Utils.is_valid_url") as mock_is_valid_url:
        mock_is_valid_url.return_value = False
        resolved_url = Utils.resolve_steam_clan_image_url(text)
    assert resolved_url == text


def test_extract_url_valid_url():
    text = "https://example.com"
    expected = "https://example.com"
    extracted_url = Utils.extract_url(text)
    assert extracted_url == expected
