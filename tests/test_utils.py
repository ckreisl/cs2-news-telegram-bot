from __future__ import annotations

import httpx
import pytest

from cs2posts import http
from cs2posts.utils import extract_url
from cs2posts.utils import get_redirected_url
from cs2posts.utils import is_url
from cs2posts.utils import is_valid_url
from cs2posts.utils import resolve_steam_clan_image_url


class Responder:
    """Answers head_or_get with a queued sequence of results."""

    def __init__(self, *results) -> None:
        self.results = list(results)
        self.urls: list[str] = []

    def __call__(self, url: str) -> httpx.Response:
        self.urls.append(url)
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, BaseException):
            raise result
        return httpx.Response(result, request=httpx.Request("HEAD", url))


@pytest.fixture
def responder(monkeypatch):
    def install(*results) -> Responder:
        responder = Responder(*results)
        monkeypatch.setattr("cs2posts.http.head_or_get", responder)
        return responder

    return install


def test_a_reachable_url_is_valid(responder):
    responder(200)

    assert is_valid_url("https://example.com")


def test_a_url_answering_with_an_error_is_not_valid(responder):
    responder(404)

    assert not is_valid_url("https://example.com")


def test_a_missing_url_is_not_valid():
    assert not is_valid_url(None)
    assert not is_valid_url("")


def test_a_url_without_a_scheme_is_not_valid():
    assert not is_valid_url("example.com")


def test_a_network_failure_makes_a_url_invalid(responder, caplog):
    responder(httpx.ConnectError("no route"))

    assert not is_valid_url("https://example.com")
    assert "Could not reach" in caplog.text


def test_a_successful_check_is_cached(responder):
    calls = responder(200)

    assert is_valid_url("https://example.com/image.jpg")
    assert is_valid_url("https://example.com/image.jpg")

    assert len(calls.urls) == 1


def test_a_transient_failure_is_not_cached(responder):
    """A single network blip must not mark a valid URL bad for the whole run."""
    failing = responder(httpx.ConnectError("blip"))
    assert not is_valid_url("https://example.com/image.jpg")

    recovered = responder(200)
    assert is_valid_url("https://example.com/image.jpg")

    assert failing.urls
    assert recovered.urls


def test_get_redirected_url_returns_the_final_location(monkeypatch):
    def handler(url: str) -> httpx.Response:
        return httpx.Response(
            200, request=httpx.Request("HEAD", "https://example.com/final")
        )

    monkeypatch.setattr("cs2posts.http.head_or_get", handler)

    assert (
        get_redirected_url("https://example.com/start") == "https://example.com/final"
    )


def test_get_redirected_url_falls_back_to_the_input(responder, caplog):
    responder(httpx.ConnectError("no route"))

    assert get_redirected_url("https://example.com") == "https://example.com"
    assert "Could not resolve" in caplog.text


def test_the_first_reachable_cdn_resolves_the_placeholder(responder):
    responder(200)

    assert resolve_steam_clan_image_url("{STEAM_CLAN_IMAGE}/a.png") == (
        "https://clan.akamai.steamstatic.com/images/a.png"
    )


def test_the_second_cdn_is_tried_when_the_first_fails(responder):
    responder(404, 200)

    assert resolve_steam_clan_image_url("{STEAM_CLAN_IMAGE}/a.png") == (
        "https://clan.fastly.steamstatic.com/images/a.png"
    )


def test_the_placeholder_survives_when_no_cdn_answers(responder):
    responder(500)

    assert (
        resolve_steam_clan_image_url("{STEAM_CLAN_IMAGE}/a.png")
        == "{STEAM_CLAN_IMAGE}/a.png"
    )


def test_text_without_the_placeholder_is_untouched():
    assert resolve_steam_clan_image_url("https://example.com/a.png") == (
        "https://example.com/a.png"
    )


@pytest.mark.parametrize(
    "text",
    [
        "https://example.com",
        "http://example.com/path?query=1",
        "https://www.example.com/a/b",
    ],
)
def test_is_url_accepts_urls(text):
    assert is_url(text)


@pytest.mark.parametrize("text", ["example", "not a url", "", "ftp://example.com"])
def test_is_url_rejects_non_urls(text):
    assert not is_url(text)


def test_extract_url_passes_a_bare_url_through():
    assert extract_url("https://example.com/a.png") == "https://example.com/a.png"


def test_extract_url_reads_an_href():
    assert extract_url('<a href="https://example.com/a.png">x</a>') == (
        "https://example.com/a.png"
    )


def test_extract_url_returns_none_when_there_is_nothing_to_find():
    assert extract_url("no url here") is None


def test_the_shared_client_is_reused():
    first = http.client()
    second = http.client()

    assert first is second

    http.close_client()
    assert http.client() is not first
    http.close_client()
