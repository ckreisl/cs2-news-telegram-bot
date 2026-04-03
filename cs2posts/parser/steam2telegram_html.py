from __future__ import annotations

import re
import sys

import bbcode

from cs2posts.parser.parser import Parser


NEWLINE_FORMAT = {
    'br': {
        'pattern': '<br />',
        'replace': '\n',
    },
    'hr': {
        'pattern': '<hr />',
        'replace': '\n',
    },
}

# Patterns that must be resolved before sub-parsers run (e.g. before
# SteamUpdateHeadingParser, which would otherwise match [/p] as a heading).
PRE_PARSER_FORMAT = {
    "strike": {
        'pattern': re.compile(r'\[strike\](.*?)\[/strike\]', re.IGNORECASE | re.DOTALL),
        'replace': r'<s>\1</s>',
    },
    "p_empty": {
        'pattern': re.compile(r'\[p\]\[/p\]', re.IGNORECASE),
        'replace': '\n',
    },
    "p": {
        'pattern': re.compile(r'\[p\](.*?)\[/p\]', re.IGNORECASE | re.DOTALL),
        'replace': r'\1',
    },
}

STEAM_FORMAT = {
    "h2": {
        'pattern': r'\[h2\](.*?)\[/h2\]',
        'replace': r'\n\n<b>\1</b>\n\n',
    },
    "h3": {
        'pattern': r'\[h3\](.*?)\[/h3\]',
        'replace': r'\n\n<b>\1</b>\n\n',
    },
    "dash": {
        'pattern': r'&ndash;',
        'replace': r'—',
    },
}


class Steam2TelegramHTML(Parser):

    def __init__(self, text: str):
        super().__init__(text)
        self.__parser: list[tuple[type[Parser], int]] = []

    def add_parser(self, parser: type[Parser], priority: int = sys.maxsize) -> None:
        self.__parser.append((parser, priority))

    def parse(self) -> str:
        self.text = bbcode.render_html(self.text)

        # TODO: Must be placed here now before parsers due to HeadingParser
        for value in NEWLINE_FORMAT.values():
            pattern = value['pattern']
            replace = value['replace']
            self.text = self.text.replace(pattern, replace)

        for value in PRE_PARSER_FORMAT.values():
            self.text = value['pattern'].sub(value['replace'], self.text)

        parser_by_priority = sorted(self.__parser, key=lambda x: x[1])
        for parser, _ in parser_by_priority:
            self.text = parser(self.text).parse()

        for value in STEAM_FORMAT.values():
            pattern = value['pattern']
            replace = value['replace']
            self.text = re.sub(
                pattern, replace, self.text,
                flags=re.IGNORECASE | re.DOTALL)

        # Collapse runs of 3+ newlines down to 2 (one blank line).
        self.text = re.sub(r'\n{3,}', '\n\n', self.text)

        return self.text
