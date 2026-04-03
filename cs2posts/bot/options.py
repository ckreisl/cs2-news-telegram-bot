from __future__ import annotations

import logging
from enum import Enum
from typing import cast

from telegram import CallbackQuery
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes

from cs2posts.db import ChatDatabase
from cs2posts.dto.chats import Chat


logger = logging.getLogger(__name__)


class ButtonData(Enum):
    UPDATE = "UPDATE"
    NEWS = "NEWS"
    EXTERNAL_NEWS = "EXTERNAL_NEWS"
    CLOSE = "CLOSE"


class IconGenerator:

    @staticmethod
    def get_enabled_icon(enabled: bool) -> str:
        return "✅" if enabled else "⛔️"


class OptionsMessageFactory:

    @staticmethod
    def create(chat: Chat) -> tuple[str, InlineKeyboardMarkup]:
        text = OptionsMessageFactory.create_text(chat)
        reply_markup = OptionsMessageFactory.create_reply_markup(chat)
        return text, reply_markup

    @staticmethod
    def create_keyboard(chat: Chat) -> list[list[InlineKeyboardButton]]:

        btn_updates_text = "Disable" if chat.is_update_interested else "Enable"
        btn_news_text = "Disable" if chat.is_news_interested else "Enable"
        btn_external_news_text = "Disable" if chat.is_external_news_interested else "Enable"

        keyboard = [
            [
                InlineKeyboardButton(f"{btn_updates_text} Updates",
                                     callback_data=ButtonData.UPDATE.value),
                InlineKeyboardButton(f"{btn_news_text} News",
                                     callback_data=ButtonData.NEWS.value),
            ],
            [
                InlineKeyboardButton(f"{btn_external_news_text} External News",
                                     callback_data=ButtonData.EXTERNAL_NEWS.value),
            ],
            [
                InlineKeyboardButton("Close",
                                     callback_data=ButtonData.CLOSE.value)
            ],
        ]

        return keyboard

    @staticmethod
    def create_reply_markup(chat: Chat) -> InlineKeyboardMarkup:
        keyboard = OptionsMessageFactory.create_keyboard(chat)
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_text(chat: Chat) -> str:
        icon_is_update_interested = IconGenerator.get_enabled_icon(
            chat.is_update_interested)
        icon_is_news_interested = IconGenerator.get_enabled_icon(
            chat.is_news_interested)
        icon_is_external_news_interested = IconGenerator.get_enabled_icon(
            chat.is_external_news_interested)

        text_enabled_update = "enabled" if chat.is_update_interested else "disabled"
        text_enabled_news = "enabled" if chat.is_news_interested else "disabled"
        text_enabled_external_news = "enabled" if chat.is_external_news_interested else "disabled"

        return (f"<b>Options</b>\n\n"
                "Handle the automatically send Counter-Strike post notifications.\n\n"
                f"{icon_is_update_interested} - Send Update Posts ("
                f"{text_enabled_update})\n"
                f"{icon_is_news_interested} - Send News Posts ("
                f"{text_enabled_news})\n"
                f"{icon_is_external_news_interested} - Send External News Posts ("
                f"{text_enabled_external_news})\n\n"
                f"Select an option to change, or press 'Close' to keep everything as it is.")


class Options:

    def __init__(self, app: Application) -> None:
        self.__chats_db: ChatDatabase | None = None

        app.add_handler(CommandHandler("options", self.options))
        app.add_handler(CallbackQueryHandler(self.button))

    @property
    def chats_db(self) -> ChatDatabase:
        if self.__chats_db is None:
            raise RuntimeError("Chat database was not configured")
        return self.__chats_db

    def set_chat_db(self, db: ChatDatabase) -> None:
        self.__chats_db = db

    async def options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None or update.message.from_user is None:
            return

        message = update.message
        from_user = message.from_user
        assert from_user is not None

        chat = await self.chats_db.get(message.chat_id)
        if chat is None:
            return

        if chat.chat_id_admin != from_user.id:
            return

        text, reply_markup = OptionsMessageFactory.create(chat)

        logger.info(
            f'Sending options message to chat_id={message.chat_id} ...')

        await message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML)

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None or query.message is None or query.from_user is None:
            return
        from_user = query.from_user
        if not hasattr(query.message, "chat_id"):
            return

        await query.answer()

        chat = await self.chats_db.get(cast(int, query.message.chat_id))
        if chat is None:
            return

        if chat.chat_id_admin != from_user.id:
            return

        if query.data is None:
            return

        btn = ButtonData(query.data)
        if btn is ButtonData.CLOSE:
            await self.close(update, context)
            return

        if btn is ButtonData.UPDATE:
            chat.is_update_interested = not chat.is_update_interested
            await self.chats_db.update(chat)

        if btn is ButtonData.NEWS:
            chat.is_news_interested = not chat.is_news_interested
            await self.chats_db.update(chat)

        if btn is ButtonData.EXTERNAL_NEWS:
            chat.is_external_news_interested = not chat.is_external_news_interested
            await self.chats_db.update(chat)

        await self.update(context, query, chat)

    async def update(self, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, chat: Chat) -> None:
        if query.message is None or not hasattr(query.message, "message_id"):
            return

        text, reply_markup = OptionsMessageFactory.create(chat)
        await context.bot.edit_message_text(
            text=text,
            chat_id=chat.chat_id,
            message_id=cast(int, query.message.message_id),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML)

    async def close(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None or query.message is None:
            return
        if not hasattr(query.message, "chat_id") or not hasattr(query.message, "message_id"):
            return

        await query.answer()
        await context.bot.delete_message(
            chat_id=cast(int, query.message.chat_id),
            message_id=cast(int, query.message.message_id))
