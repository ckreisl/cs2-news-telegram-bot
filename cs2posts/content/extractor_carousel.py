from __future__ import annotations

import re

from .content import Carousel
from .extractor import Extractor
from .extractor_image import ImageExtractor


class CarouselExtractor(Extractor):

    def extract(self) -> list[Carousel]:
        carousel_pattern = r"\[carousel\](.*?)\[/carousel\]"
        matches = re.finditer(carousel_pattern, self.text)

        carousel = []
        for result in matches:
            images = ImageExtractor(result.group(1)).extract()
            carousel.append(Carousel(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                images=images))

        return carousel
