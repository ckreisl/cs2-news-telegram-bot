from __future__ import annotations

import abc
import asyncio
import json
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


CRAWLER_REQUEST_TIMEOUT = 3


class WebCrawler(abc.ABC):
    """Base class for crawlers.

    This abstraction exists mostly for typing and future extensibility.
    """

    @abc.abstractmethod
    async def crawl(self, *args: Any, **kwargs: Any) -> Any:
        """Fetch data from the remote source."""


class SteamAPICrawler(WebCrawler):
    """Base Steam Web API crawler."""


class CounterStrike2Crawler(SteamAPICrawler):
    """Fetches latest CS2 news updates from the Steam API."""

    BASE_URL = (
        "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
        "?appid=730"
        "&count=%s"
        "&maxlength=0"
    )

    def __init__(self) -> None:
        super().__init__()
        self.url = self.BASE_URL

    def _validate_args(self, *, count: int) -> None:
        if count < 0:
            raise ValueError('count must be greater than or equal to 0')

    async def crawl(self, *, count: int | None = None) -> dict[str, Any]:
        """Fetch the latest CS2 news posts.

        This method is asynchronous for integration with the rest of the bot, but
        it uses a threadpool to keep the HTTP call non-blocking.
        """

        if count is None:
            count = 100

        self._validate_args(count=count)

        url = self.url % count
        try:
            response = await asyncio.to_thread(
                requests.get, url, timeout=CRAWLER_REQUEST_TIMEOUT)
        except Exception:
            logger.exception('Could not fetch data from Steam API')
            raise

        if not response.ok:
            raise RuntimeError(
                f'Could not fetch data, received response code={response.status_code}')

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as exc:
            logger.exception('Received invalid JSON from Steam API: %s', exc)
            raise
