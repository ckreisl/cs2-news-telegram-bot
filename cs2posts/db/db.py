from __future__ import annotations

import abc
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class Database:

    def __init__(self, filepath: Path | None) -> None:
        self.__filepath = filepath

    @property
    def filepath(self) -> Path:
        return self.__filepath

    @abc.abstractmethod
    async def create(self, *, overwrite=False) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    async def save(self, data: Any) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    async def is_empty(self, table_name: str) -> bool:
        pass  # pragma: no cover

    @abc.abstractmethod
    async def import_from_json(self, filepath: Path) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    async def backup(self, filepath: Path) -> bool:
        pass  # pragma: no cover
