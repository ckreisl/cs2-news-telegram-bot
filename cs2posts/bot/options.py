from __future__ import annotations

import logging
from typing import ClassVar

from telegram import CallbackQuery
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes

from cs2posts.db import ChatRepository
from cs2posts.dto.chats import Chat
from cs2posts.dto.post import PostType

logger = logging.getLogger(__name__)

CLOSE = "close"

# One row per line; the labels and the toggles are both derived from PostType
# so a new post type needs no new button, branch, or sentence here.
POST_TYPE_LABELS: dict[PostType, str] = {
    PostType.UPDATE: "Updates",
    PostType.NEWS: "News",
    PostType.EXTERNAL: "External News",
}
KEYBOARD_ROWS: tuple[tuple[PostType, ...], ...] = (
    (PostType.UPDATE, PostType.NEWS),
    (PostType.EXTERNAL,),
)

ENABLED_ICON = "✅"
DISABLED_ICON = "⛔️"


def enabled_icon(enabled: bool) -> str:
    return ENABLED_ICON if enabled else DISABLED_ICON


def create_options_keyboard(chat: Chat) -> list[list[InlineKeyboardButton]]:
    rows = [
        [
            InlineKeyboardButton(
                f"{'Disable' if chat.is_interested_in(post_type) else 'Enable'}"
                f" {POST_TYPE_LABELS[post_type]}",
                callback_data=post_type.value,
            )
            for post_type in row
        ]
        for row in KEYBOARD_ROWS
    ]
    rows.append([InlineKeyboardButton("Close", callback_data=CLOSE)])
    return rows


def create_options_reply_markup(chat: Chat) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(create_options_keyboard(chat))


def create_options_text(chat: Chat) -> str:
    lines = "\n".join(
        f"{enabled_icon(chat.is_interested_in(post_type))} - Send"
        f" {POST_TYPE_LABELS[post_type]} Posts"
        f" ({'enabled' if chat.is_interested_in(post_type) else 'disabled'})"
        for post_type in POST_TYPE_LABELS
    )
    return (
        "<b>Options</b>\n\n"
        "Handle the automatically send Counter-Strike post notifications.\n\n"
        f"{lines}\n\n"
        "Select an option to change, or press 'Close' to keep everything as it is."
    )


def create_options_message(chat: Chat) -> tuple[str, InlineKeyboardMarkup]:
    return create_options_text(chat), create_options_reply_markup(chat)


class Options:
    """The ``/options`` command and its inline keyboard.

    Both dependencies arrive through the constructor; the previous two-phase
    ``set_chat_db`` existed only because the wiring order was inverted, and it
    left every instance briefly unusable.
    """

    COMMAND: ClassVar[str] = "options"

    def __init__(self, app: Application, chat_db: ChatRepository) -> None:
        self._chat_db = chat_db
        app.add_handler(CommandHandler(self.COMMAND, self.options))
        app.add_handler(CallbackQueryHandler(self.button))

    async def _admin_chat(self, chat_id: int, user_id: int) -> Chat | None:
        chat = await self._chat_db.get(chat_id)
        if chat is None or chat.chat_id_admin != user_id:
            return None
        return chat

    async def options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        if message is None or message.from_user is None:
            return

        chat = await self._admin_chat(message.chat_id, message.from_user.id)
        if chat is None:
            return

        logger.info("Sending options message to chat_id=%s ...", message.chat_id)
        text, reply_markup = create_options_message(chat)
        await message.reply_text(
            text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None or query.message is None or query.data is None:
            return
        if not hasattr(query.message, "chat_id"):
            return

        await query.answer()

        chat = await self._admin_chat(query.message.chat_id, query.from_user.id)
        if chat is None:
            return

        if query.data == CLOSE:
            await self.close(context, query)
            return

        try:
            post_type = PostType(query.data)
        except ValueError:
            # A button from a message rendered by an older version.
            logger.warning("Ignoring unknown option %r", query.data)
            return

        chat.toggle_interest(post_type)
        await self._chat_db.update(chat)
        await self.refresh(context, query, chat)

    async def refresh(
        self, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, chat: Chat
    ) -> None:
        if query.message is None or not hasattr(query.message, "message_id"):
            return

        text, reply_markup = create_options_message(chat)
        await context.bot.edit_message_text(
            text=text,
            chat_id=chat.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

    async def close(
        self, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery
    ) -> None:
        if query.message is None:
            return
        if not hasattr(query.message, "chat_id") or not hasattr(
            query.message, "message_id"
        ):
            return

        # The hasattr guards above narrow away InaccessibleMessage, which
        # carries no chat_id.
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
