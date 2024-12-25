from __future__ import annotations

from .content import Content
from .extractor import Extractor
from .extractor_image import ImageExtractor
from .extractor_text import TextBlockExtractor
from .extractor_video import VideoExtractor
from .extractor_youtube import YoutubeExtractor


class ContentExtractor(Extractor):

    def extract(self) -> list[Content]:
        youtube = YoutubeExtractor(self.text).extract()
        videos = VideoExtractor(self.text).extract()
        images = ImageExtractor(self.text).extract()
        texts = TextBlockExtractor(self.text, videos, images, youtube).extract()

        content: list[Content] = sorted(
            [*youtube, *videos, *images, *texts],
            key=lambda content: content.text_pos_start)

        content[0].is_heading = True

        return content
