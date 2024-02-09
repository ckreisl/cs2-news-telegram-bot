from __future__ import annotations

import abc


class Parser(abc.ABC):

    def __init__(self, text: str) -> None:
        self.__text = text

    @property
    def text(self) -> str:
        return self.__text

    @text.setter
    def text(self, text: str) -> None:
        self.__text = text

    @abc.abstractmethod
    def parse(self) -> str:
        pass
