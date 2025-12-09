from __future__ import annotations

import logging
import re

from cs2posts.parser.parser import Parser


logger = logging.getLogger(__name__)


class SteamUpdateHeadingParser(Parser):

    HEADING_REGEX = r'\[([a-zA-Z0-9&\s]+)\]'
    # Will be completed if needed
    HEADING_LIST_IGNORE = ["CT"]
    MIN_HEADING_LENGTH = 2

    def __init__(self, text: str):
        super().__init__(text)

    def is_heading_by_newlines(self, word: str) -> bool:
        pos = self.text.find(word)

        if pos == 0:
            return True

        is_left_newline = self.text[pos - 1] == '\n'
        is_right_newline = self.text[pos + len(word)] == '\n'
        return is_left_newline or is_right_newline

    def is_heading(self, word: str) -> bool:
        return self.is_heading_by_newlines(word)

    def is_single_element_heading(self, word: str) -> bool:
        stripped = word.strip('[]').strip()
        return len(stripped) == 1

    def has_min_size(self, word: str) -> bool:
        stripped = word.strip('[]').strip()
        return len(stripped) >= self.MIN_HEADING_LENGTH

    def ignore(self, word: str) -> bool:
        stripped = word.strip('[]').strip().upper()
        return stripped in self.HEADING_LIST_IGNORE

    def remove_leading_backslash(self, word: str) -> str:
        pos = self.text.find(word)
        if pos != -1 and self.text[pos - 1] == '\\':
            return self.text[:pos - 1] + self.text[pos:]
        return self.text

    def parse(self) -> str:
        headings = re.findall(re.compile(self.HEADING_REGEX), self.text)
        headings = [f"[{heading}]" for heading in headings if self.has_min_size(heading)]

        for heading in headings:
            if self.is_single_element_heading(heading):
                continue

            self.text = self.remove_leading_backslash(heading)

            if self.is_heading_by_newlines(heading):
                self.text = self.text.replace(heading, f"<b>{heading}</b>")
            elif not self.ignore(heading):
                self.text = self.text.replace(heading, f"<b>{heading}</b>\n")
            else:
                logger.warning(f"Not handled heading: {heading}")

        return self.text
