from __future__ import annotations

from typing import Protocol


class Parser(Protocol):
    """A pure text transformation.

    Parsers are stateless: they take the text to transform as an argument and
    return a new string. An earlier version stored the text on the instance
    and wrote results back onto it, which made ``parse()`` non-idempotent --
    calling it twice re-escaped HTML the first call had produced.
    """

    def parse(self, text: str) -> str: ...
