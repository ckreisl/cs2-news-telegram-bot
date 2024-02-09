from __future__ import annotations

import json
import logging
from typing import Any

import requests

from cs2posts.post import EventType

logger = logging.getLogger(__name__)


class CounterStrike2NetCrawler:

    def __init__(self) -> None:
        self.url = "https://store.steampowered.com/" \
            "events/ajaxgetpartnereventspageable/" \
            "?clan_accountid=0" \
            "&appid=730" \
            "&offset=0" \
            "&count=%s" \
            "&l=english" \
            "&origin=https://www.counter-strike.net"

    def _validate_args(self, **kwargs: dict[str, Any]) -> None:
        if "limit" in kwargs and "count" in kwargs:
            if kwargs["limit"] > kwargs["count"]:
                raise ValueError('Count must be greater or equal to limit!')

        if "count" in kwargs and kwargs["count"] < 0:
            raise ValueError('Count must be greater than 0!')

        if "limit" in kwargs and kwargs["limit"] < 0:
            raise ValueError('Limit must be greater than 0!')

    def crawl(self, *, count: int | None = None) -> dict[str, Any]:
        if count is None:
            count = 100

        self._validate_args(count=count)

        response = requests.get(self.url % count)

        if not response.ok:
            raise Exception(
                f'Could not fetch data received response code={response.status_code}')

        return json.loads(response.text)

    def crawl_by_event_type(self, event_type: EventType, *,
                            limit: int | None = None,
                            count: int | None = None):
        if count is None:
            count = 100

        if limit is None:
            limit = 1

        self._validate_args(count=count, limit=limit)

        json_dict = self.crawl(count=count)

        data = {'events': []}
        for event in json_dict['events']:
            if EventType(event['event_type']) != event_type:
                continue

            if len(data['events']) >= limit:
                return data

            data['events'].append(event)

    def crawl_latest_update_post(self) -> dict[str, Any]:
        return self.crawl_by_event_type(EventType.UPDATE, limit=1)

    def crawl_latest_news_post(self) -> dict[str, Any]:
        return self.crawl_by_event_type(EventType.NEWS, limit=1)


if __name__ == '__main__':
    crawler = CounterStrike2NetCrawler()
    data = crawler.crawl_latest_news_post()
    print(data)
