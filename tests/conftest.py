from __future__ import annotations

from datetime import datetime
from datetime import timedelta

import httpx
import pytest

from cs2posts.clock import UTC
from cs2posts.clock import FrozenClock
from cs2posts.dto.chats import Chat
from cs2posts.dto.post import Post
from cs2posts.settings import Settings
from cs2posts.utils import cache_clear

NOW = datetime(2024, 5, 23, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(NOW)


@pytest.fixture
def settings() -> Settings:
    """Explicit test configuration, independent of the developer's .env."""
    return Settings(
        telegram_token="test-token",
        crawl_interval_seconds=900,
        spam_interval_ms=750,
        ban_timeout_seconds=600,
        max_strikes=3,
        strike_recovery_minutes=60,
    )


@pytest.fixture
def make_post():
    def factory(**overrides) -> Post:
        defaults = {
            "gid": "1337",
            "title": "A Post",
            "url": "https://example.com/post",
            "is_external_url": False,
            "author": "Valve",
            "contents": "Some contents",
            "feedlabel": "feedlabel",
            "feedname": "feedname",
            "date": 1700000000,
            "feed_type": 1,
            "appid": 730,
            "tags": [],
        }
        return Post(**{**defaults, **overrides})

    return factory


@pytest.fixture
def make_chat():
    def factory(chat_id: int = 1337, **overrides) -> Chat:
        defaults = {"is_running": True, "last_activity": NOW - timedelta(days=1)}
        return Chat(chat_id=chat_id, **{**defaults, **overrides})

    return factory


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail loudly if a unit test reaches for the network.

    Tests that need HTTP opt in via the ``http_response`` fixture, so an
    accidental real request cannot make the suite slow or flaky.
    """

    def forbidden(url: str):
        raise AssertionError(
            f"Unexpected HTTP request to {url}. Use the http_response fixture."
        )

    def blocked(self, request, *args, **kwargs):
        raise AssertionError(
            f"Unexpected HTTP request to {request.url}."
            " Install an httpx.MockTransport for this test."
        )

    monkeypatch.setattr("cs2posts.http.head_or_get", forbidden)
    # Block the real transports too, so a code path that builds its own client
    # (the crawler) cannot reach the internet. httpx.MockTransport is a
    # separate class and still works.
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked)
    cache_clear()
    yield
    cache_clear()


@pytest.fixture
def http_response(monkeypatch):
    """Answer every outbound HEAD/GET with a canned response.

    Returns a setter so a test can choose the status and final URL, e.g.
    ``http_response(status_code=404)``.
    """
    import httpx

    def configure(status_code: int = 200, url: str = "https://example.com/final"):
        def handler(requested: str) -> httpx.Response:
            return httpx.Response(
                status_code, request=httpx.Request("HEAD", url or requested)
            )

        monkeypatch.setattr("cs2posts.http.head_or_get", handler)

    configure()
    return configure


@pytest.fixture
def fast_sleep(monkeypatch):
    """Collapse the inter-send pauses and retry backoff so tests stay quick."""
    import asyncio

    async def instant(delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", instant)
