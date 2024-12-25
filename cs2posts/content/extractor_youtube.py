from __future__ import annotations

import re

from .content import Youtube
from .extractor import Extractor


class YoutubeExtractor(Extractor):

    def extract(self) -> list[Youtube]:
        videos = []

        youtube_pattern = r"\[previewyoutube=([^;]+);.*?\]\[/previewyoutube\]"
        matches = re.finditer(youtube_pattern, self.text)

        for result in matches:
            videos.append(Youtube(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                url=result.group(1)))

        return videos
