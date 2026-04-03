from __future__ import annotations

import abc
from collections.abc import Sequence

from .content import Content


class Extractor(abc.ABC):

    def __init__(self, text: str) -> None:
        self.__text: str = text

    @property
    def text(self) -> str:
        return self.__text

    @abc.abstractmethod
    def extract(self) -> Sequence[Content]:
        pass
