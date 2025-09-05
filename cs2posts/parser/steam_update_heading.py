from __future__ import annotations

import re

from cs2posts.parser.parser import Parser


class SteamUpdateHeadingParser(Parser):

    HEADING_REGEX = r'\[([a-zA-Z0-9&\s]+)\]'
    # Will be completed if needed
    HEADING_LIST = [
        "MAPS", "UI", "GAMEPLAY", "MISC", "ANIMATION", "ITEMS", "GAMEPLAY",
        "AUDIO", "GRAPHICS",
    ]

    def __init__(self, text: str):
        super().__init__(text)

    def is_heading_by_newlines(self, word: str) -> bool:
        pos = self.text.find(word)

        if len(word.strip('[]')) == 1:
            return False

        if pos == 0:
            return True

        is_left_newline = self.text[pos - 1] == '\n'
        is_right_newline = self.text[pos + len(word)] == '\n'
        return is_left_newline or is_right_newline

    def is_heading_by_identifier(self, word: str) -> bool:
        return word.strip('[]').strip().upper() in self.HEADING_LIST

    def is_heading(self, word: str) -> bool:
        return self.is_heading_by_newlines(word) or self.is_heading_by_identifier(word)

    def parse(self) -> str:
        headings = re.findall(re.compile(self.HEADING_REGEX), self.text)
        headings = [f"[{heading}]" for heading in headings]

        for heading in headings:
            if self.is_heading_by_newlines(heading):
                self.text = self.text.replace(heading, f"<b>{heading}</b>")
            elif self.is_heading_by_identifier(heading):
                self.text = self.text.replace(heading, f"<b>{heading}</b>\n")

        return self.text
