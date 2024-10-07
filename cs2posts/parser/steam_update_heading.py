from __future__ import annotations

import re

from cs2posts.parser.parser import Parser


class SteamUpdateHeadingParser(Parser):

    HEADING_REGEX = r'\[([A-Z0-9&\s]+)\]'

    def __init__(self, text: str):
        super().__init__(text)

    def is_heading(self, word: str) -> bool:
        pos = self.text.find(word)

        if pos == 0:
            return True

        is_left_newline = self.text[pos - 1] == '\n'
        is_right_newline = self.text[pos + len(word)] == '\n'

        return is_left_newline and is_right_newline

    def parse(self) -> str:
        headings = re.findall(re.compile(self.HEADING_REGEX), self.text)
        headings = [f"[{heading}]" for heading in headings]

        for heading in headings:
            if self.is_heading(heading):
                self.text = self.text.replace(heading, f"<b>{heading}</b>")

        return self.text
