from __future__ import annotations

import logging
import re

from cs2posts.parser.parser import Parser


logger = logging.getLogger(__name__)


class SteamNewsYoutubeParser(Parser):

    YOUTUBE_REGEX = r'\[previewyoutube=(.*?)\]\[/previewyoutube\]'
    YOUTUBE_REPLACE = r'<a href="https://www.youtube.com/watch?v=\1">YouTube Video</a>'

    def __init__(self, text: str) -> None:
        super().__init__(text)

    def parse(self) -> str:
        return re.sub(self.YOUTUBE_REGEX,
                      self.YOUTUBE_REPLACE,
                      self.text,
                      re.IGNORECASE)
