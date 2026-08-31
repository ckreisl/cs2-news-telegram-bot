from __future__ import annotations

from .content import Content
from .extractor import Extractor
from .extractor_carousel import CarouselExtractor
from .extractor_image import ImageExtractor
from .extractor_text import TextBlockExtractor
from .extractor_video import VideoExtractor
from .extractor_youtube import YoutubeExtractor


class ContentExtractor(Extractor):
    """Every piece of a post, in the order it appears in the body."""

    def extract(self) -> list[Content]:
        youtube = YoutubeExtractor(self.text).extract()
        videos = VideoExtractor(self.text).extract()
        carousels = CarouselExtractor(self.text).extract()
        images = ImageExtractor(self.text).extract()

        if carousels:
            # A carousel's images are also matched standalone; keep only the
            # ones that are not already part of a carousel.
            in_carousel = {
                image.url for carousel in carousels for image in carousel.images
            }
            images = [image for image in images if image.url not in in_carousel]

        media: list[Content] = [*youtube, *videos, *carousels, *images]
        texts = TextBlockExtractor(self.text, media).extract()

        content = sorted([*media, *texts], key=lambda content: content.text_pos_start)

        if content:
            content[0].is_heading = True

        return content
