from __future__ import annotations

import abc
import json
import logging
from pathlib import Path
from typing import Any

from cs2posts.bot.chats import Chat
from cs2posts.bot.chats import Chats
from cs2posts.post import Post


logger = logging.getLogger(__name__)


class Store(abc.ABC):

    @abc.abstractmethod
    def create(self) -> None:
        pass

    @abc.abstractmethod
    def load(self) -> Any:
        pass

    @abc.abstractmethod
    def save(self, data: Any) -> None:
        pass

    @abc.abstractmethod
    def is_empty(self) -> bool:
        pass


class LocalStore(Store):

    def __init__(self, filepath: Path) -> None:
        self.__filepath = filepath

        if not self.__filepath.exists():
            self.create()

    @property
    def filepath(self) -> Path:
        return self.__filepath

    def create(self) -> None:
        with open(self.filepath, "w") as fs:
            json.dump({}, fs)

    def load(self) -> dict[str, Any]:
        with open(self.filepath) as fs:
            return json.load(fs)

    def save(self, data: Any) -> None:
        with open(self.filepath, "w") as fs:
            json.dump(data, fs, indent=4)

    def is_empty(self) -> bool:
        if self.filepath.stat().st_size == 0:
            return True

        try:
            with open(self.filepath) as fs:
                data = json.load(fs)
            return data == {}
        except json.JSONDecodeError:
            return True


class LocalLatestPostStore(LocalStore):

    def __init__(self, filepath: Path | None = None) -> None:
        if filepath is None:
            filepath = Path(__file__).parent / "data" / "latest.json"

        super().__init__(filepath)

    def save(self, post: Post) -> None:
        content = self.load()

        if post.is_news():
            key = "news"
        elif post.is_update():
            key = "update"
        else:
            return

        content[key] = post.to_dict()

        with open(self.filepath, "w") as fs:
            json.dump(content, fs, indent=4)

    def get_latest_news_post(self) -> Post:
        return Post(**self.load()['news'])

    def get_latest_update_post(self) -> Post:
        return Post(**self.load()['update'])

    def get_latest_post(self) -> Post:
        news = self.get_latest_news_post()
        update = self.get_latest_update_post()
        return news if news.date > update.date else update


class LocalChatStore(LocalStore):

    def __init__(self, filepath: Path | None = None) -> None:
        if filepath is None:
            filepath = Path(__file__).parent / "data" / "chats.json"

        super().__init__(filepath)

    def load(self) -> Chats:
        if self.is_empty():
            return Chats()

        with open(self.filepath) as fs:
            data = json.load(fs)

        chats = Chats()
        for chat in data["chats"]:
            chat = Chat.from_json(chat)
            if chat.is_removed_while_banned:
                continue
            chats.add(chat=chat)

        return chats

    def save(self, chats: Chats) -> None:
        with open(self.filepath, "w") as fs:
            chats_json = [chat.to_json() for chat in chats]
            json.dump({"chats": chats_json}, fs, indent=4)
