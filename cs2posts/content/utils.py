from __future__ import annotations

import re

from cs2posts.utils import Utils
# TODO: Refactor this because it's not a good practice to import from bot


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


def is_url(text: str) -> bool:
    url_regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
    url_pattern = re.compile(url_regex)
    return re.match(url_pattern, text) is not None


def extract_url(text: str) -> str | None:
    if is_url(text):
        return text
    m = re.search(r'href="([^"]+)"', text)
    return m.group(1) if m else None
