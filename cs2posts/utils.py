from __future__ import annotations

import logging
import re

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

    @staticmethod
    def resolve_steam_clan_image_url(text: str) -> str:
        STEAM_CLAN_IMAGE = "{STEAM_CLAN_IMAGE}"
        if STEAM_CLAN_IMAGE not in text:
            return text

        urls = [
            "https://clan.akamai.steamstatic.com/images",
            "https://clan.fastly.steamstatic.com/images",
        ]

        for url in urls:
            resolved_url = text.replace(STEAM_CLAN_IMAGE, url)
            if Utils.is_valid_url(resolved_url):
                return resolved_url

        return text

    @staticmethod
    def is_url(text: str) -> bool:
        url_regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        url_pattern = re.compile(url_regex)
        return re.match(url_pattern, text) is not None

    @staticmethod
    def extract_url(text: str) -> str | None:
        if Utils.is_url(text):
            return text
        m = re.search(r'href="([^"]+)"', text)
        return m.group(1) if m else None
