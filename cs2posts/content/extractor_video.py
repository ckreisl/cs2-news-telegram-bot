from __future__ import annotations

import html
import re

from .content import Video
from .extractor import Extractor
from cs2posts.utils import Utils


class VideoExtractor(Extractor):

    _BOOL_TRUE = {"1", "true", "yes", "on"}
    _BOOL_FALSE = {"0", "false", "no", "off"}
    _VIDEO_RE = re.compile(r"\[video\b(?P<attrs>.*?)\](?P<inner>.*?)\[/video\]", re.I | re.S)
    _URL_IN_TEXT_RE = re.compile(r'(https?://[^\s"<>\]]+)', re.I)
    _ATTRS_MIXED_RE = re.compile(r"""
        (\w+)                                 # key
        \s*=\s*
        (?:&quot;(.*?)&quot;                  # 1: entity-quoted
        |"(.*?)"                              # 2: double-quoted
        |'(.*?)'                              # 3: single-quoted
        |(<a\b.*?</a>)                        # 4: anchor element
        |([^\s\]]+)                           # 5: bare token up to whitespace or ]
        )
    """, re.I | re.S | re.X)

    def _to_bool(self, s: str | None) -> bool | None:
        if s is None:
            return None
        v = s.strip().lower()
        if v in self._BOOL_TRUE:
            return True
        if v in self._BOOL_FALSE:
            return False
        return None

    def _extract_url(self, val: str) -> str | None:
        href = re.search(r'href=[\'"]([^\'"]+)[\'"]', val, re.I)
        if href:
            return href.group(1).strip()
        m = self._URL_IN_TEXT_RE.search(val)
        if m:
            return m.group(1).strip()
        # Return raw value if it's a non-empty path (e.g., {STEAM_CLAN_IMAGE}/...)
        stripped = val.strip()
        if not stripped or " " in stripped:
            return None
        return stripped

    def _parse_attrs(self, attrs_raw: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for m in self._ATTRS_MIXED_RE.finditer(attrs_raw):
            key = m.group(1).strip().lower()
            # pick the first non-None alternative group (2..6)
            val = next(g for g in m.groups()[1:] if g is not None)
            out[key] = html.unescape(val.strip())
        return out

    def extract(self) -> list[Video]:
        videos = []

        for m in re.finditer(self._VIDEO_RE, self.text):
            attrs_raw = m.group("attrs") or ""
            attrs = self._parse_attrs(attrs_raw)

            # Pull urls (handles raw url or <a href="...">)
            webm_url = self._extract_url(attrs.get("webm", "")) if "webm" in attrs else ""
            mp4_url = self._extract_url(attrs.get("mp4", "")) if "mp4" in attrs else ""
            poster_url = self._extract_url(attrs.get("poster", "")) if "poster" in attrs else ""

            if webm_url:
                webm_url = Utils.resolve_steam_clan_image_url(webm_url)
            if mp4_url:
                mp4_url = Utils.resolve_steam_clan_image_url(mp4_url)
            if poster_url:
                poster_url = Utils.resolve_steam_clan_image_url(poster_url)

            videos.append(Video(
                text_pos_start=m.start(),
                text_pos_end=m.end(),
                webm=webm_url,
                mp4=mp4_url,
                poster=poster_url,
                autoplay=self._to_bool(attrs.get("autoplay")),
                controls=self._to_bool(attrs.get("controls")),
                is_heading=False,
            ))

        return videos
