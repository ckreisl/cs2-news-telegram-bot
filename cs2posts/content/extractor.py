from __future__ import annotations

import abc
from collections.abc import Sequence

from .content import Content


class Extractor(abc.ABC):
    """Finds one kind of content inside a rendered post body."""

    def __init__(self, text: str) -> None:
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    @abc.abstractmethod
    def extract(self) -> Sequence[Content]: ...
