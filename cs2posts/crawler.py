from __future__ import annotations

import json
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


CRAWLER_REQUEST_TIMEOUT = 3


class WebCrawler:
    pass


class SteamAPICrawler(WebCrawler):
    pass


class CounterStrike2Crawler(SteamAPICrawler):

    def __init__(self) -> None:
        super().__init__()
        # https://developer.valvesoftware.com/wiki/Steam_Web_API
        # maxlength=0 to get whole content
        self.url = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/" \
            "?appid=730" \
            "&count=%s" \
            "&maxlength=0"

    def _validate_args(self, **kwargs: dict[str, Any]) -> None:
        if "count" in kwargs and kwargs["count"] < 0:
            raise ValueError('Count must be greater than 0!')

    async def crawl(self, *, count: int | None = None) -> dict[str, Any]:
        if count is None:
            count = 100

        self._validate_args(count=count)

        try:
            response = requests.get(
                self.url % count, timeout=CRAWLER_REQUEST_TIMEOUT)
        except Exception as e:
            logger.error(f'Could not fetch data due to {e}')
            raise

        if not response.ok:
            raise Exception(
                f'Could not fetch data received response code={response.status_code}')

        return json.loads(response.text)
