from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from cs2posts.exceptions import InvalidSteamResponse
from cs2posts.exceptions import SteamApiUnavailable
from cs2posts.http import HTTP_TIMEOUT_SECONDS
from cs2posts.http import USER_AGENT

logger = logging.getLogger(__name__)

ClientFactory = Callable[[], httpx.AsyncClient]

STEAM_NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
COUNTER_STRIKE_APP_ID = 730
DEFAULT_POST_COUNT = 100


class CounterStrike2Crawler:
    """Fetches CS2 news posts from the Steam Web API."""

    def __init__(
        self,
        *,
        app_id: int = COUNTER_STRIKE_APP_ID,
        url: str = STEAM_NEWS_URL,
        timeout: float = HTTP_TIMEOUT_SECONDS,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._app_id = app_id
        self._url = url
        self._timeout = timeout
        # Injectable so tests can supply an httpx.MockTransport instead of
        # monkeypatching httpx globally, which would also intercept the
        # Telegram client.
        self._client_factory = client_factory or self._default_client

    def _default_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self._timeout, headers={"User-Agent": USER_AGENT}
        )

    async def crawl(self, *, count: int = DEFAULT_POST_COUNT) -> dict[str, Any]:
        """Fetch the latest posts.

        Raises :class:`SteamApiUnavailable` if Steam cannot be reached or
        answers with an error, and :class:`InvalidSteamResponse` if the body
        is not the JSON object the caller expects.
        """
        if count < 0:
            raise ValueError(f"count must be greater than or equal to 0, got {count}")

        params = {
            "appid": self._app_id,
            "count": count,
            "maxlength": 0,
        }

        try:
            async with self._client_factory() as client:
                response = await client.get(self._url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise SteamApiUnavailable(
                f"Steam answered {exc.response.status_code} for {self._url}"
            ) from exc
        except httpx.HTTPError as exc:
            raise SteamApiUnavailable(f"Could not reach {self._url}: {exc}") from exc
        except ValueError as exc:
            raise InvalidSteamResponse(f"Steam returned invalid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise InvalidSteamResponse(
                f"Expected a JSON object, got {type(payload).__name__}"
            )

        return payload
