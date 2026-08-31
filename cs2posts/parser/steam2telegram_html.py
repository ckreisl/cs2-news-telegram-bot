from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field

import bbcode

from cs2posts.parser.parser import Parser


@dataclass(frozen=True)
class SubstitutionRule:
    """One regex substitution applied to the whole document."""

    pattern: re.Pattern[str]
    replacement: str

    def apply(self, text: str) -> str:
        return self.pattern.sub(self.replacement, text)


def _rule(pattern: str, replacement: str, flags: int = 0) -> SubstitutionRule:
    return SubstitutionRule(re.compile(pattern, flags), replacement)


DOTALL_I = re.IGNORECASE | re.DOTALL

# Steam emits <br /> and <hr /> where Telegram wants plain newlines. Applied
# before the sub-parsers, which reason about line boundaries.
NEWLINE_RULES = (
    _rule(r"<br />", "\n"),
    _rule(r"<hr />", "\n"),
)

# Resolved before sub-parsers run, so that SteamUpdateHeadingParser does not
# mistake a leftover [/p] for a section heading.
PRE_PARSER_RULES = (
    _rule(r"\[strike\](.*?)\[/strike\]", r"\1", DOTALL_I),
    _rule(r"\[p\]\[/p\]", "\n", re.IGNORECASE),
    _rule(r"\[p\](.*?)\[/p\]", r"\1", DOTALL_I),
)

HEADING_RULES = tuple(
    _rule(rf"\[{tag}\](.*?)\[/{tag}\]", r"\n\n<b>\1</b>\n\n", DOTALL_I)
    for tag in ("h2", "h3", "h4", "h5")
)

ENTITY_RULES = (_rule(r"&ndash;", "—", re.IGNORECASE),)

# Strip trailing whitespace on each line, then collapse runs of blank lines.
WHITESPACE_RULES = (
    _rule(r"[^\S\n]+\n", "\n"),
    _rule(r"\n{3,}", "\n\n"),
)

# Non-breaking spaces would keep headings like "[ SOUND\xa0]" from matching.
NBSP = "\xa0"


@dataclass
class Steam2TelegramHTML:
    """Converts Steam's bbcode/HTML post bodies into Telegram-flavoured HTML.

    Sub-parsers are supplied as instances and run in priority order between
    the pre- and post-processing rule sets.
    """

    sub_parsers: list[tuple[Parser, int]] = field(default_factory=list)

    def add_parser(self, parser: Parser, priority: int) -> Steam2TelegramHTML:
        self.sub_parsers.append((parser, priority))
        return self

    def parse(self, text: str) -> str:
        text = bbcode.render_html(text)

        for rule in NEWLINE_RULES:
            text = rule.apply(text)

        for rule in PRE_PARSER_RULES:
            text = rule.apply(text)

        text = text.replace(NBSP, " ")

        for parser, _ in sorted(self.sub_parsers, key=lambda item: item[1]):
            text = parser.parse(text)

        for rule in (*HEADING_RULES, *ENTITY_RULES, *WHITESPACE_RULES):
            text = rule.apply(text)

        return text
