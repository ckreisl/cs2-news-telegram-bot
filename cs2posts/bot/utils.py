from __future__ import annotations

import logging

import requests

from cs2posts.bot.constants import REQUESTS_TIMEOUT

logger = logging.getLogger(__name__)


class Utils:

    @staticmethod
    def is_valid_url(url: str | None, timeout: int = REQUESTS_TIMEOUT) -> bool:
        if not url:
            return False

        if not url.startswith("http"):
            return False

        try:
            response = requests.get(url, timeout=timeout)
        except Exception as e:
            logger.error(f"Failed to get image from {url}: {e}")
            return False

        return response.ok

    @staticmethod
    def get_redirected_url(url: str, timeout: int = REQUESTS_TIMEOUT) -> str:
        try:
            response = requests.get(url, timeout=timeout)
        except Exception as e:
            logger.error(f"Could not fetch data due to {e}")
            return url
        return response.url
