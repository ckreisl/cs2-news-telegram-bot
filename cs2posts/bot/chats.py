from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Chat:
    chat_id: int
    chat_id_admin: int = 0
    strikes: int = 0
    is_running: bool = False
    is_banned: bool = False
    is_removed_while_banned: bool = False
    is_news_interested: bool = True
    is_update_interested: bool = True
    is_external_news_interested: bool = True
    last_activity: datetime = datetime(1970, 1, 1)

    @classmethod
    def from_json(cls, data: dict[str, str]) -> Chat:
        last_activity = datetime.fromisoformat(data.pop('last_activity'))
        return cls(**data, last_activity=last_activity)

    def to_json(self) -> dict[str, str]:
        return {
            "chat_id": self.chat_id,
            "chat_id_admin": self.chat_id_admin,
            "strikes": self.strikes,
            "is_running": self.is_running,
            "is_banned": self.is_banned,
            "is_removed_while_banned": self.is_removed_while_banned,
            "is_news_interested": self.is_news_interested,
            "is_update_interested": self.is_update_interested,
            "is_external_news_interested": self.is_external_news_interested,
            "last_activity": self.last_activity.isoformat()
        }


class Chats:

    def __init__(self, chats: list[Chat] = None) -> None:
        if chats is None:
            chats = []
        self.__chats: dict[int, Chat] = {}
        for chat in chats:
            self.__chats[chat.chat_id] = chat

    @property
    def chats(self) -> list[Chat]:
        return list(self.__chats.values())

    def get(self, chat_id: int) -> Chat | None:
        return self.__chats.get(chat_id)

    def add(self, chat: Chat) -> None:
        self.__chats[chat.chat_id] = chat

    def create(self, chat_id: int) -> Chat:
        return Chat(chat_id=chat_id)

    def remove(self, chat: Chat) -> None:
        self.__chats.pop(chat.chat_id, None)

    def update(self, chat: Chat) -> None:
        self.__chats[chat.chat_id] = chat

    def contains(self, chat_id: int) -> bool:
        return chat_id in self.__chats

    def create_and_add(self, chat_id: int) -> Chat:
        chat = self.create(chat_id)
        self.add(chat)
        return chat

    def migrate(self, chat: Chat, new_chat_id: int) -> Chat:
        self.remove(chat)
        chat.chat_id = new_chat_id
        self.add(chat)
        return chat

    def get_running_chats(self) -> list[Chat]:
        return [chat for chat in self.__chats.values() if chat.is_running]

    def get_interested_in_news(self) -> list[Chat]:
        return [chat for chat in self.__chats.values() if chat.is_news_interested]

    def get_interested_in_updates(self) -> list[Chat]:
        return [chat for chat in self.__chats.values() if chat.is_update_interested]

    def get_running_and_interested_in_news(self) -> list[Chat]:
        return [chat for chat in self.__chats.values() if chat.is_running and chat.is_news_interested]

    def get_running_and_interested_in_updates(self) -> list[Chat]:
        return [chat for chat in self.__chats.values() if chat.is_running and chat.is_update_interested]

    def get_running_and_interested_in_external_news(self) -> list[Chat]:
        return [chat for chat in self.__chats.values() if chat.is_running and chat.is_external_news_interested]

    def __contains__(self, chat: Chat) -> bool:
        return chat.chat_id in self.__chats

    def __iter__(self):
        return iter(self.__chats.values())

    def __len__(self) -> int:
        return len(self.__chats)
