from __future__ import annotations

import httpx
import pytest

from cs2posts.crawler import COUNTER_STRIKE_APP_ID
from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.exceptions import InvalidSteamResponse
from cs2posts.exceptions import SteamApiUnavailable

PAYLOAD = {"appnews": {"newsitems": []}}


@pytest.fixture
def requests() -> list[httpx.Request]:
    return []


@pytest.fixture
def crawler(monkeypatch, requests):
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=PAYLOAD)

    return _install(monkeypatch, handler)


def _install(monkeypatch, handler) -> CounterStrike2Crawler:
    transport = httpx.MockTransport(handler)
    return CounterStrike2Crawler(
        client_factory=lambda: httpx.AsyncClient(transport=transport)
    )


@pytest.mark.asyncio
async def test_crawl_rejects_negative_count(crawler):
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        await crawler.crawl(count=-1)


@pytest.mark.asyncio
async def test_crawl_returns_the_parsed_payload(crawler):
    assert await crawler.crawl() == PAYLOAD


@pytest.mark.asyncio
async def test_crawl_asks_steam_for_the_requested_app_and_count(crawler, requests):
    await crawler.crawl(count=7)

    (request,) = requests
    assert request.url.params["appid"] == str(COUNTER_STRIKE_APP_ID)
    assert request.url.params["count"] == "7"
    assert request.url.params["maxlength"] == "0"


@pytest.mark.asyncio
async def test_crawl_reports_an_error_status_as_unavailable(monkeypatch):
    crawler = _install(monkeypatch, lambda request: httpx.Response(404))

    with pytest.raises(SteamApiUnavailable, match="404"):
        await crawler.crawl()


@pytest.mark.asyncio
async def test_crawl_reports_a_transport_failure_as_unavailable(monkeypatch):
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    crawler = _install(monkeypatch, boom)

    with pytest.raises(SteamApiUnavailable):
        await crawler.crawl()


@pytest.mark.asyncio
async def test_crawl_rejects_a_non_json_body(monkeypatch):
    crawler = _install(monkeypatch, lambda r: httpx.Response(200, text="not json"))

    with pytest.raises(InvalidSteamResponse):
        await crawler.crawl()


@pytest.mark.asyncio
async def test_crawl_rejects_a_json_array(monkeypatch):
    crawler = _install(monkeypatch, lambda r: httpx.Response(200, json=[1, 2]))

    with pytest.raises(InvalidSteamResponse, match="Expected a JSON object"):
        await crawler.crawl()


@pytest.mark.asyncio
async def test_crawler_errors_share_a_base_class(monkeypatch):
    from cs2posts.exceptions import CrawlerError

    crawler = _install(monkeypatch, lambda request: httpx.Response(500))

    with pytest.raises(CrawlerError):
        await crawler.crawl()
