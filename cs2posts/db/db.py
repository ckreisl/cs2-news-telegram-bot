from __future__ import annotations

import abc
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class Database(abc.ABC):
    """Storage-backend contract.

    Only the operations shared by every backend live here. Table-specific
    operations such as ``save``/``import_from_json`` (whose signatures differ
    per stored type) belong on the concrete subclasses.
    """

    def __init__(self, filepath: Path) -> None:
        self.__filepath = filepath

    @property
    def filepath(self) -> Path:
        return self.__filepath

    @abc.abstractmethod
    async def create(self, *, overwrite: bool = False) -> None:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def is_empty(self, table_name: str) -> bool:
        ...  # pragma: no cover

    @abc.abstractmethod
    async def backup(self, filepath: Path) -> None:
        ...  # pragma: no cover
