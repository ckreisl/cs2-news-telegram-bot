from __future__ import annotations

from collections.abc import Sequence

from .content import Content
from .content import TextBlock
from .extractor import Extractor
from .extractor_carousel import CarouselExtractor
from .extractor_image import ImageExtractor
from .extractor_video import VideoExtractor
from .extractor_youtube import YoutubeExtractor

IMAGE_LINK_LABEL = "Image Link"


class TextBlockExtractor(Extractor):
    """The prose between the media blocks of a post.

    ``media`` is required rather than optional-and-recomputed: the only
    caller already has the extracted media, and taking it as an argument
    leaves this class with a single, testable code path.
    """

    def __init__(self, text: str, media: Sequence[Content]) -> None:
        super().__init__(text)
        self._media = sorted(media, key=lambda content: content.text_pos_start)

    @classmethod
    def from_text(cls, text: str) -> TextBlockExtractor:
        """Extract the media blocks first, then the text between them."""
        media: list[Content] = [
            *VideoExtractor(text).extract(),
            *YoutubeExtractor(text).extract(),
            *CarouselExtractor(text).extract(),
            *ImageExtractor(text).extract(),
        ]
        return cls(text, media)

    def extract(self) -> list[TextBlock]:
        if not self._media:
            return [TextBlock(0, len(self.text), False, self.text)]

        blocks: list[TextBlock] = []
        text_pos = 0

        for media in self._media:
            if media.text_pos_start <= text_pos:
                text_pos = media.text_pos_end
                continue

            text = self.text[text_pos : media.text_pos_start].strip()
            if text:
                blocks.append(
                    TextBlock(
                        text_pos_start=text_pos,
                        text_pos_end=media.text_pos_start,
                        is_heading=False,
                        text=text,
                    )
                )

            text_pos = media.text_pos_end

        blocks.append(
            TextBlock(
                text_pos_start=text_pos,
                text_pos_end=len(self.text),
                is_heading=False,
                text=self.text[text_pos:].strip(),
            )
        )

        return self._merge_split_anchors(blocks)

    def _merge_split_anchors(self, blocks: list[TextBlock]) -> list[TextBlock]:
        """Rejoin an anchor that an inline image split in two.

        A clickable image renders as ``<a href=...>[img]...[/img]</a>``; the
        image is extracted from the middle, leaving a dangling ``</a>`` as its
        own block.
        """
        merged: list[TextBlock] = []
        i = 0

        while i < len(blocks):
            left = blocks[i]
            right = blocks[i + 1] if i + 1 < len(blocks) else None

            if (
                right is not None
                and left.text.endswith(">")
                and right.text.startswith("</a>")
            ):
                merged.append(
                    TextBlock(
                        text_pos_start=left.text_pos_start,
                        text_pos_end=right.text_pos_end,
                        is_heading=left.is_heading,
                        text=f"{left.text}\n{IMAGE_LINK_LABEL}{right.text}",
                    )
                )
                i += 2
                continue

            merged.append(left)
            i += 1

        return merged
