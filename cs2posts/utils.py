from __future__ import annotations

import logging
import re

import httpx

from cs2posts import http

logger = logging.getLogger(__name__)

URL_RE = re.compile(
    r"https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b"
    r"([-a-zA-Z0-9()@:%_+.~#?&/=]*)"
)
HREF_RE = re.compile(r'href="([^"]+)"')

STEAM_CLAN_IMAGE = "{STEAM_CLAN_IMAGE}"
STEAM_CLAN_IMAGE_HOSTS = (
    "https://clan.akamai.steamstatic.com/images",
    "https://clan.fastly.steamstatic.com/images",
)

# Only successful validations are cached. Transient failures must not be
# remembered, otherwise a single network blip would permanently mark a valid
# URL as invalid for the lifetime of the process.
_MAX_VALID_URL_CACHE = 1024
_valid_url_cache: set[str] = set()


def cache_clear() -> None:
    _valid_url_cache.clear()


def _remember_valid(url: str) -> None:
    if len(_valid_url_cache) >= _MAX_VALID_URL_CACHE:
        _valid_url_cache.clear()
    _valid_url_cache.add(url)


def is_valid_url(url: str | None) -> bool:
    """Whether ``url`` is fetchable. Network failures answer ``False``."""
    if not url or not url.startswith("http"):
        return False

    if url in _valid_url_cache:
        return True

    try:
        response = http.head_or_get(url)
    except httpx.HTTPError as exc:
        logger.error("Could not reach %s: %s", url, exc)
        return False

    if response.is_error:
        return False

    _remember_valid(url)
    return True


def get_redirected_url(url: str) -> str:
    """The final URL after redirects, or ``url`` itself if it cannot be reached."""
    try:
        return str(http.head_or_get(url).url)
    except httpx.HTTPError as exc:
        logger.error("Could not resolve %s: %s", url, exc)
        return url


def resolve_steam_clan_image_url(text: str) -> str:
    """Substitute Steam's ``{STEAM_CLAN_IMAGE}`` placeholder with a live CDN host."""
    if STEAM_CLAN_IMAGE not in text:
        return text

    for host in STEAM_CLAN_IMAGE_HOSTS:
        resolved = text.replace(STEAM_CLAN_IMAGE, host)
        if is_valid_url(resolved):
            return resolved

    return text


def is_url(text: str) -> bool:
    return URL_RE.match(text) is not None


def extract_url(text: str) -> str | None:
    if is_url(text):
        return text
    match = HREF_RE.search(text)
    return match.group(1) if match else None
