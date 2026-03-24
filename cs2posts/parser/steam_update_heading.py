from __future__ import annotations

import logging
import re

from cs2posts.parser.parser import Parser


logger = logging.getLogger(__name__)


class SteamUpdateHeadingParser(Parser):

    HEADING_REGEX = re.compile(r"(?P<escape>\\)?\[(?P<heading>[a-zA-Z0-9&/'\-\s]+)\]")
    # Will be completed if needed
    HEADING_LIST_IGNORE = ["CT"]
    MIN_HEADING_LENGTH = 2

    def __init__(self, text: str):
        super().__init__(text)

    def is_heading_by_newlines(self, start: int, end: int) -> bool:
        is_left_newline = start == 0 or self.text[start - 1] == '\n'
        is_right_newline = end == len(self.text) or self.text[end] == '\n'
        return is_left_newline or is_right_newline

    def is_heading(self, start: int, end: int) -> bool:
        return self.is_heading_by_newlines(start, end)

    def count_trailing_newlines(self, end: int) -> int:
        count = 0
        i = end
        while i < len(self.text) and self.text[i] == '\n':
            count += 1
            i += 1
        return count

    def is_single_element_heading(self, word: str) -> bool:
        stripped = word.strip()
        return len(stripped) == 1

    def has_min_size(self, word: str) -> bool:
        stripped = word.strip()
        return len(stripped) >= self.MIN_HEADING_LENGTH

    def ignore(self, word: str) -> bool:
        stripped = word.strip().upper()
        return stripped in self.HEADING_LIST_IGNORE

    def format_heading(self, match: re.Match[str]) -> str:
        heading = match.group("heading")
        bracketed_heading = f"[{heading}]"

        if not self.has_min_size(heading) or self.is_single_element_heading(heading):
            return match.group(0)

        if self.ignore(heading):
            logger.warning(f"Not handled heading: {bracketed_heading}")
            return match.group(0)

        start, end = match.span()
        formatted_heading = f"<b>{bracketed_heading}</b>"

        if self.is_heading(start, end):
            trailing_newlines = self.count_trailing_newlines(end)

            if trailing_newlines == 0:
                return f"{formatted_heading}\n\n"
            if trailing_newlines == 1:
                return f"{formatted_heading}\n"
            return formatted_heading

        return f"{formatted_heading}\n"

    def parse(self) -> str:
        self.text = self.HEADING_REGEX.sub(self.format_heading, self.text)
        return self.text
