from __future__ import annotations

import logging
import re
from collections.abc import Iterator

from .content import Image
from .extractor import Extractor
from cs2posts.utils import Utils

logger = logging.getLogger(__name__)


def extract_images_deprecated(text: str) -> Iterator:
    pattern = r"\[img\](.*?)\[/img\]"
    matches = re.finditer(pattern, text)
    return matches


def extract_images(text: str) -> Iterator:
    # Handle both standard quotes and html-encoded quotes (&quot;)
    # Group 1: Content inside &quot;...&quot; (can contain quotes)
    # Group 2: Content inside "..." (standard)
    pattern = r'\[img src=(?:&quot;(.*?)&quot;|"([^"]+)")(?:[^\]]*)\]\[\/img\]'
    matches = re.finditer(pattern, text, re.I | re.S)
    return matches


class ImageExtractor(Extractor):

    def extract(self) -> list[Image]:
        matches = extract_images(self.text)
        matches_deprecated = extract_images_deprecated(self.text)

        # Merge both iterators
        all_matches = list(matches) + list(matches_deprecated)

        images = []
        for result in all_matches:

            # Get the URL from the correct capture group
            src_url = result.group(1) or result.group(2)
            if not src_url:
                continue

            html_encoded_quot = "&quot;"
            if html_encoded_quot in src_url:
                src_url = src_url.replace(html_encoded_quot, "")

            url = Utils.resolve_steam_clan_image_url(src_url)

            if url == "":
                logger.warning("Image URL is empty in text!")
                continue

            images.append(Image(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                url=url))

        return images
