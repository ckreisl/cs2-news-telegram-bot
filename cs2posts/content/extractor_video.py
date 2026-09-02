from __future__ import annotations

import html
import re
from typing import ClassVar

from cs2posts.utils import resolve_steam_clan_image_url
from .content import Video
from .extractor import Extractor


class VideoExtractor(Extractor):
    """Reads ``[video ...]`` bbcode, whose attributes Steam quotes
    inconsistently (plain, single, or HTML-entity quotes, sometimes wrapping a
    whole anchor element)."""

    BOOL_TRUE: ClassVar[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
    BOOL_FALSE: ClassVar[frozenset[str]] = frozenset({"0", "false", "no", "off"})
    URL_ATTRIBUTES: ClassVar[tuple[str, ...]] = ("webm", "mp4", "poster")

    VIDEO_RE = re.compile(
        r"\[video\b(?P<attrs>.*?)\](?P<inner>.*?)\[/video\]", re.I | re.S
    )
    URL_IN_TEXT_RE = re.compile(r'(https?://[^\s"<>\]]+)', re.I)
    HREF_RE = re.compile(r'href=[\'"]([^\'"]+)[\'"]', re.I)
    ATTRS_RE = re.compile(
        r"""
        (\w+)                                 # key
        \s*=\s*
        (?:&quot;(.*?)&quot;                  # 1: entity-quoted
        |"(.*?)"                              # 2: double-quoted
        |'(.*?)'                              # 3: single-quoted
        |(<a\b.*?</a>)                        # 4: anchor element
        |([^\s\]]+)                           # 5: bare token up to whitespace or ]
        )
    """,
        re.I | re.S | re.X,
    )

    def _to_bool(self, value: str | None) -> bool | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized in self.BOOL_TRUE:
            return True
        if normalized in self.BOOL_FALSE:
            return False
        return None

    def _to_url(self, value: str | None) -> str | None:
        """The URL inside an attribute value, which may be bare or an anchor."""
        if value is None:
            return None

        href = self.HREF_RE.search(value)
        if href:
            return href.group(1).strip()

        in_text = self.URL_IN_TEXT_RE.search(value)
        if in_text:
            return in_text.group(1).strip()

        # Keep a bare path such as {STEAM_CLAN_IMAGE}/... as-is.
        stripped = value.strip()
        if not stripped or " " in stripped:
            return None
        return stripped

    def _parse_attrs(self, attrs_raw: str) -> dict[str, str]:
        attrs: dict[str, str] = {}
        for match in self.ATTRS_RE.finditer(attrs_raw):
            key = match.group(1).strip().lower()
            # The first non-None alternative group holds the value.
            value = next(group for group in match.groups()[1:] if group is not None)
            attrs[key] = html.unescape(value.strip())
        return attrs

    def _resolved_url(self, attrs: dict[str, str], name: str) -> str | None:
        """An absent attribute yields ``None``, never an empty string.

        Callers distinguish "no mp4 source" from "an mp4 source we could not
        parse"; conflating the two used to hide webm-only videos.
        """
        url = self._to_url(attrs.get(name))
        return resolve_steam_clan_image_url(url) if url else None

    def extract(self) -> list[Video]:
        videos = []

        for match in self.VIDEO_RE.finditer(self.text):
            attrs = self._parse_attrs(match.group("attrs") or "")
            urls = {
                name: self._resolved_url(attrs, name) for name in self.URL_ATTRIBUTES
            }

            videos.append(
                Video(
                    text_pos_start=match.start(),
                    text_pos_end=match.end(),
                    is_heading=False,
                    webm=urls["webm"],
                    mp4=urls["mp4"],
                    poster=urls["poster"],
                    autoplay=self._to_bool(attrs.get("autoplay")),
                    controls=self._to_bool(attrs.get("controls")),
                )
            )

        return videos
