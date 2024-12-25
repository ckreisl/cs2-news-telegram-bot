from __future__ import annotations

import re

from .content import Image
from .extractor import Extractor
from cs2posts.utils import Utils


class ImageExtractor(Extractor):

    def extract(self) -> list[Image]:
        pattern = r"\[img\](.*?)\[/img\]"
        matches = re.finditer(pattern, self.text)
        images = []
        for result in matches:
            url = Utils.resolve_steam_clan_image_url(result.group(1))
            images.append(Image(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                url=url))

        return images
