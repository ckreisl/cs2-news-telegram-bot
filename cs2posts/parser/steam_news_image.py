from __future__ import annotations

import logging
import re

from cs2posts.parser.parser import Parser


logger = logging.getLogger(__name__)


class SteamNewsImageParser(Parser):

    URL_REGEX = r'<a .*?>.*?</a>'
    IMG_REGEX = r'\[img\].*?\[/img\]'

    def __init__(self, text: str) -> None:
        super().__init__(text)

    def parse(self) -> str:
        # As of now every news post has a image at the top
        # so we can remove the first (count=1) url and including image tag
        url_pattern = re.compile(self.URL_REGEX, re.IGNORECASE)
        self.text = re.sub(url_pattern, r'', self.text, count=1)

        img_pattern = re.compile(self.IMG_REGEX, re.IGNORECASE)
        self.text = re.sub(img_pattern, r'', self.text, count=1)

        return self.text
