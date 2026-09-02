from __future__ import annotations

import logging
import re
from typing import ClassVar

logger = logging.getLogger(__name__)


class SteamUpdateHeadingParser:
    """Bolds bracketed section headings such as ``[ MAPS ]`` in patch notes."""

    HEADING_REGEX = re.compile(r"(?P<escape>\\)?\[(?P<heading>[a-zA-Z0-9&/'\-\s]+)\]")
    # Will be completed if needed
    HEADING_LIST_IGNORE: ClassVar[frozenset[str]] = frozenset({"CT"})
    # bbcode tags (opening and closing, e.g. [img]...[/img]) that are
    # consumed by the content extractors and must survive this parser.
    BBCODE_TAGS_IGNORE: ClassVar[frozenset[str]] = frozenset(
        {"IMG", "VIDEO", "CAROUSEL"}
    )
    MIN_HEADING_LENGTH = 2
    BLANK_LINES_AROUND_HEADING = 2

    def parse(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            return self._format_heading(text, match)

        return self.HEADING_REGEX.sub(replace, text)

    def _is_bbcode_tag(self, word: str) -> bool:
        return word.strip().upper().removeprefix("/") in self.BBCODE_TAGS_IGNORE

    def _is_ignored(self, word: str) -> bool:
        return word.strip().upper() in self.HEADING_LIST_IGNORE

    def _is_heading_candidate(self, word: str) -> bool:
        return len(word.strip()) >= self.MIN_HEADING_LENGTH

    def _starts_or_ends_a_line(self, text: str, start: int, end: int) -> bool:
        at_line_start = start == 0 or text[start - 1] == "\n"
        at_line_end = end == len(text) or text[end] == "\n"
        return at_line_start or at_line_end

    def _count_newlines(self, text: str, index: int, step: int) -> int:
        count = 0
        while 0 <= index < len(text) and text[index] == "\n":
            count += 1
            index += step
        return count

    def _format_heading(self, text: str, match: re.Match[str]) -> str:
        heading = match.group("heading")

        if self._is_bbcode_tag(heading):
            return match.group(0)

        if not self._is_heading_candidate(heading):
            return match.group(0)

        if self._is_ignored(heading):
            logger.warning("Not handled heading: [%s]", heading)
            return match.group(0)

        formatted = f"<b>[{heading}]</b>"
        start, end = match.span()

        if not self._starts_or_ends_a_line(text, start, end):
            return f"{formatted}\n"

        wanted = self.BLANK_LINES_AROUND_HEADING
        leading = self._count_newlines(text, start - 1, -1)
        trailing = self._count_newlines(text, end, 1)

        prefix = "\n" * (wanted - leading) if start > 0 and leading < wanted else ""
        suffix = "\n" * (wanted - trailing) if trailing < wanted else ""

        return f"{prefix}{formatted}{suffix}"
