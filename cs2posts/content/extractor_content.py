from __future__ import annotations

from .content import Content
from .extractor import Extractor
from .extractor_carousel import CarouselExtractor
from .extractor_image import ImageExtractor
from .extractor_text import TextBlockExtractor
from .extractor_video import VideoExtractor
from .extractor_youtube import YoutubeExtractor


class ContentExtractor(Extractor):

    def extract(self) -> list[Content]:
        youtube = YoutubeExtractor(self.text).extract()
        videos = VideoExtractor(self.text).extract()
        carousel = CarouselExtractor(self.text).extract()
        images = ImageExtractor(self.text).extract()

        if len(carousel) > 0:
            # Remove images that are already in the carousel
            all_img_urls = {img.url for c in carousel for img in c.images}
            images = list(filter(lambda img: img.url not in all_img_urls, images))

        texts = TextBlockExtractor(self.text, videos, carousel, images, youtube).extract()

        content: list[Content] = sorted(
            [*youtube, *videos, *carousel, *images, *texts],
            key=lambda content: content.text_pos_start)

        content[0].is_heading = True

        return content
