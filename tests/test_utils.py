from __future__ import annotations

from unittest.mock import patch

import pytest

from cs2posts.utils import cache_clear
from cs2posts.utils import extract_url
from cs2posts.utils import get_redirected_url
from cs2posts.utils import is_valid_url
from cs2posts.utils import resolve_steam_clan_image_url


@pytest.fixture(autouse=True)
def clear_is_valid_url_cache():
    cache_clear()


def test_is_valid_url_valid():
    url = "https://example.com"
    with patch("requests.head") as mock_head:
        mock_head.return_value.ok = True
        is_valid = is_valid_url(url)
    assert is_valid


def test_is_valid_url_invalid_url_none():
    assert not is_valid_url(None)


def test_is_valid_url_invalid():
    url = "example.com"
    assert not is_valid_url(url)

    url = "https://www.google.com"
    with patch("requests.get") as mock_get, patch("requests.head") as mock_head:
        mock_get.side_effect = Exception
        mock_head.side_effect = Exception
        is_valid = is_valid_url(url)
    assert not is_valid


def test_is_valid_url_does_not_cache_transient_failure():
    url = "https://example.com/image.jpg"

    # First call fails (transient network error) and must NOT be cached.
    with patch("requests.head") as mock_head:
        mock_head.side_effect = Exception
        assert not is_valid_url(url)

    # A subsequent successful check must re-validate and succeed.
    with patch("requests.head") as mock_head:
        mock_head.return_value.ok = True
        assert is_valid_url(url)


def test_is_valid_url_caches_success():
    url = "https://example.com/cached.jpg"

    with patch("requests.head") as mock_head:
        mock_head.return_value.ok = True
        assert is_valid_url(url)

    # Cached: a second call must not hit the network at all.
    with patch("requests.head") as mock_head:
        mock_head.side_effect = AssertionError("network should not be called")
        assert is_valid_url(url)


def test_get_redirected_url_same_url():
    url = "https://example.com"
    with patch("requests.get") as mock_get, patch("requests.head") as mock_head:
        mock_get.return_value.url = url
        mock_head.return_value.url = url
        redirected_url = get_redirected_url(url)
    assert redirected_url == url


def test_get_redirected_url_redirected():
    url = "https://nonexistenturl.com"
    expected = "https://foobar.com"
    with patch("requests.get") as mock_get, patch("requests.head") as mock_head:
        mock_get.return_value.url = expected
        mock_head.return_value.url = expected
        redirected_url = get_redirected_url(url)
    assert redirected_url == expected


def test_get_redirected_url_exception():
    url = "https://example.com"
    with patch("requests.get") as mock_get, patch("requests.head") as mock_head:
        mock_get.side_effect = Exception
        mock_head.side_effect = Exception
        redirected_url = get_redirected_url(url)
    assert redirected_url == url


def test_resolve_steam_clan_image_url_valid_url():
    text = "{STEAM_CLAN_IMAGE}"
    expected = "https://clan.akamai.steamstatic.com/images"
    with patch("cs2posts.utils.is_valid_url") as mock_is_valid_url:
        mock_is_valid_url.return_value = True
        resolved_url = resolve_steam_clan_image_url(text)
    assert resolved_url == expected


def test_resolve_steam_clan_image_url_invalid_url():
    text = "{STEAM_CLAN_IMAGE}"
    with patch("cs2posts.utils.is_valid_url") as mock_is_valid_url:
        mock_is_valid_url.return_value = False
        resolved_url = resolve_steam_clan_image_url(text)
    assert resolved_url == text


def test_extract_url_valid_url():
    text = "https://example.com"
    expected = "https://example.com"
    extracted_url = extract_url(text)
    assert extracted_url == expected
