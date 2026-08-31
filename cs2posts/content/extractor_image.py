from __future__ import annotations

import logging
import re
from collections.abc import Iterator

from cs2posts.utils import resolve_steam_clan_image_url
from .content import Image
from .extractor import Extractor

logger = logging.getLogger(__name__)

HTML_QUOT = "&quot;"

# Current Steam markup: [img src="..."] or [img src=&quot;...&quot;].
# Group 1 is the entity-quoted URL, group 2 the plainly quoted one.
IMAGE_RE = re.compile(
    r'\[img src=(?:&quot;(.*?)&quot;|"([^"]*)")(?:[^\]]*)\]\[\/img\]', re.I | re.S
)
# Legacy Steam markup, still present in older posts: [img]...[/img].
LEGACY_IMAGE_RE = re.compile(r"\[img\](.*?)\[/img\]")


def _matches(text: str) -> Iterator[re.Match[str]]:
    yield from IMAGE_RE.finditer(text)
    yield from LEGACY_IMAGE_RE.finditer(text)


class ImageExtractor(Extractor):
    def extract(self) -> list[Image]:
        images = []

        for match in _matches(self.text):
            src_url = match.group(1) or match.group(2)
            if not src_url:
                continue

            url = resolve_steam_clan_image_url(src_url.replace(HTML_QUOT, ""))
            if not url:
                logger.warning("Image URL is empty in text!")
                continue

            images.append(
                Image(
                    text_pos_start=match.start(),
                    text_pos_end=match.end(),
                    is_heading=False,
                    url=url,
                )
            )

        return images
