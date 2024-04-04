from __future__ import annotations

import logging
from enum import Enum

from telegram import CallbackQuery
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes

from cs2posts.bot.chats import Chat
from cs2posts.bot.chats import Chats
from cs2posts.store import Store


logger = logging.getLogger(__name__)


class ButtonData(Enum):
    UPDATE = "UPDATE"
    NEWS = "NEWS"
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
    def create_keyboard(chat: Chat) -> list[InlineKeyboardButton]:

        btn_updates_text = "Disable" if chat.is_update_interested else "Enable"
        btn_news_text = "Disable" if chat.is_news_interested else "Enable"

        keyboard = [
            [
                InlineKeyboardButton(f"{btn_updates_text} Updates",
                                     callback_data=ButtonData.UPDATE.value),
                InlineKeyboardButton(f"{btn_news_text} News",
                                     callback_data=ButtonData.NEWS.value),
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

        text_enabled_update = "enabled" if chat.is_update_interested else "disabled"
        text_enabled_news = "enabled" if chat.is_news_interested else "disabled"

        return (f"<b>Options</b>\n\n"
                "Handle the automatically send Counter-Strike post notifications.\n\n"
                f"{icon_is_update_interested} - Send Update Posts ({text_enabled_update})\n"
                f"{icon_is_news_interested} - Send News Posts ({text_enabled_news})\n\n"
                f"Select an option to change, or press 'Close' to keep everything as it is.")


class Options:

    def __init__(self, app: Application) -> None:
        self.__chats = None
        self.__store = None

        app.add_handler(CommandHandler("options", self.options))
        app.add_handler(CallbackQueryHandler(self.button))

    @property
    def chats(self) -> Chats:
        return self.__chats

    def set_chats(self, chats: Chats) -> None:
        self.__chats = chats

    def set_chats_store(self, store: Store) -> None:
        self.__store = store

    async def options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

        chat = self.chats.get(update.message.chat_id)
        if chat is None:
            return

        if chat.chat_id_admin != update.message.from_user.id:
            return

        text, reply_markup = OptionsMessageFactory.create(chat)

        logger.info(
            f'Sending options message to chat_id={update.message.chat_id} ...')

        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML)

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        chat = self.chats.get(query.message.chat_id)
        if chat is None:
            return

        if chat.chat_id_admin != query.from_user.id:
            return

        btn = ButtonData(query.data)
        if btn is ButtonData.CLOSE:
            await self.close(update, context)
            return

        if btn is ButtonData.UPDATE:
            chat.is_update_interested = not chat.is_update_interested
            self.__store.save(self.chats)

        if btn is ButtonData.NEWS:
            chat.is_news_interested = not chat.is_news_interested
            self.__store.save(self.chats)

        await self.update(context, query, chat)

    async def update(self, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, chat: Chat) -> None:
        text, reply_markup = OptionsMessageFactory.create(chat)
        await context.bot.edit_message_text(
            text=text,
            chat_id=chat.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML)

    async def close(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id)
