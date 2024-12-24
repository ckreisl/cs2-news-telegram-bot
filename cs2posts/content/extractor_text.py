from __future__ import annotations

from .content import Content
from .content import TextBlock
from .extractor import Extractor
from .extractor_image import ImageExtractor
from .extractor_video import VideoExtractor
from .extractor_youtube import YoutubeExtractor


class TextBlockExtractor(Extractor):

    def __init__(self, text: str,
                 videos: list[Content] | None = None,
                 images: list[Content] | None = None,
                 youtube: list[Content] | None = None) -> None:
        super().__init__(text)

        videos = videos or VideoExtractor(self.text).extract()
        images = images or ImageExtractor(self.text).extract()
        youtube = youtube or YoutubeExtractor(self.text).extract()

        self.__content = sorted([
            *videos,
            *youtube,
            *images
        ], key=lambda content: content.text_pos_start)

    def _combine(self, text_blocks: list[TextBlock]) -> list[TextBlock]:
        if len(text_blocks) == 0:
            return text_blocks

        if len(text_blocks) == 1:
            return text_blocks

        blocks = []

        i = 0
        while i < len(text_blocks):
            left = text_blocks[i]
            idx_right = i + 1
            if idx_right >= len(text_blocks):
                blocks.append(left)
                break
            right = text_blocks[idx_right]

            if left.text.endswith('>') and right.text.startswith('</a>'):
                blocks.append(TextBlock(
                    text_pos_start=left.text_pos_start,
                    text_pos_end=right.text_pos_end,
                    is_heading=left.is_heading,
                    text=left.text + "\nImage Link" + right.text))
                i += 2
                continue

            blocks.append(left)
            i += 1

        return blocks

    def extract(self) -> list[TextBlock]:

        if len(self.__content) == 0:
            return [TextBlock(0, len(self.text), False, self.text)]

        blocks = []
        text_pos = 0

        for c in self.__content:
            if c.text_pos_start == 0:
                text_pos = c.text_pos_end
                continue

            blocks.append(TextBlock(
                text_pos_start=text_pos,
                text_pos_end=c.text_pos_start,
                is_heading=False,
                text=self.text[text_pos:c.text_pos_start].strip()))

            text_pos = c.text_pos_end

        blocks.append(TextBlock(
            text_pos_start=text_pos,
            text_pos_end=len(self.text),
            is_heading=False,
            text=self.text[text_pos:len(self.text)].strip()))

        # New news post if image is clickable and the link contains an image
        # We end up with a </a> tag as own TextBlock
        return self._combine(blocks)
