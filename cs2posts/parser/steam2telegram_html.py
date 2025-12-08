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

STEAM_FORMAT = {
    "h3": {
        'pattern': r'\[h3\](.*?)\[/h3\]',
        'replace': r'\n\n<b>\1</b>\n\n',
    },
    "dash": {
        'pattern': r'&ndash;',
        'replace': r'—',
    },
    "p": {
        'pattern': r'\[p\](.*?)\[/p\]',
        # For now remove, later on it should rather be r'\1\n'
        'replace': r'\1',
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

        parser_by_priority = sorted(self.__parser, key=lambda x: x[1])
        for parser, _ in parser_by_priority:
            self.text = parser(self.text).parse()

        for value in STEAM_FORMAT.values():
            pattern = value['pattern']
            replace = value['replace']
            self.text = re.sub(
                pattern, replace, self.text,
                flags=re.IGNORECASE | re.DOTALL)

        return self.text
