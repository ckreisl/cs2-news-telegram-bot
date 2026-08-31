from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from collections.abc import Coroutine
from typing import Any

from telegram import Update
from telegram.constants import ChatType
from telegram.constants import ParseMode
from telegram.ext import Application
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import filters
from telegram.request import HTTPXRequest

from cs2posts.bot import constants as const
from cs2posts.bot.backup import ChatDatabaseBackupManager
from cs2posts.bot.bootstrap import bootstrap
from cs2posts.bot.heartbeat import write_heartbeat
from cs2posts.bot.messenger import ChatMessenger
from cs2posts.bot.notifier import PostNotifier
from cs2posts.bot.options import Options
from cs2posts.bot.spam import SpamProtector
from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.db import ChatRepository
from cs2posts.db import PostRepository
from cs2posts.dto.chats import Chat
from cs2posts.dto.post import PostType
from cs2posts.msg import create_message
from cs2posts.settings import Settings

logger = logging.getLogger(__name__)

Handler = Callable[
    ["CounterStrike2UpdateBot", Update, CallbackContext], Coroutine[Any, Any, None]
]

READ_TIMEOUT = 30
WRITE_TIMEOUT = 30
CONNECT_TIMEOUT = 15
POOL_TIMEOUT = 15

GROUP_CHAT_TYPES = (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL)

HELP_MESSAGE = (
    "/start - Starts the bot\n"
    "/stop - Stops the bot for this chat\n"
    "/latest - Sends the latest post\n"
    "/news - Sends the latest news post\n"
    "/update - Sends the latest update post\n"
    "/external - Sends the latest external post\n"
    "/help - Prints this help message\n"
    "/options - Configure Options <b>(only admins)</b>"
)
STOPPED_MESSAGE = (
    "Bot has been stopped for this chat. You can start it again with /start"
)
ALREADY_RUNNING_MESSAGE = "Bot is already running for your chat!"


def spam_protected(func: Handler) -> Handler:
    """Run the spam check before ``func``, and drop the update if banned."""

    @functools.wraps(func)
    async def wrapper(
        self: CounterStrike2UpdateBot, update: Update, context: CallbackContext
    ) -> None:
        if update.message is None:
            return

        chat = await self.chat_db.get(update.message.chat_id)
        await self.spam_protector.check(context.bot, chat)

        if chat is not None:
            # Persist any state mutated by the spam check (strikes, ban,
            # last activity) before deciding whether to drop the message.
            await self.chat_db.update(chat)
            if chat.is_banned:
                return

        await func(self, update, context)

    return wrapper


class CounterStrike2UpdateBot:
    """Wires the Telegram application to the chat and post services.

    Crawl-and-dispatch lives in :class:`PostNotifier`, chat lifecycle in
    :class:`ChatMessenger`, and startup in :func:`bootstrap`; what remains
    here is handler registration and the command handlers themselves.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        crawler: CounterStrike2Crawler,
        spam_protector: SpamProtector,
        post_db: PostRepository,
        chat_db: ChatRepository,
        application: Application | None = None,
    ) -> None:
        self.settings = settings
        self.crawler = crawler
        self.spam_protector = spam_protector
        self.post_db = post_db
        self.chat_db = chat_db

        self.app = application if application is not None else self._build_app()

        self.messenger = ChatMessenger(chat_db)
        self.notifier = PostNotifier(
            crawler=crawler,
            post_db=post_db,
            chat_db=chat_db,
            messenger=self.messenger,
        )

        self.username: str | None = None
        self.options = Options(app=self.app, chat_db=chat_db)
        self._register_handlers()

    def _build_app(self) -> Application:
        request = HTTPXRequest(
            read_timeout=READ_TIMEOUT,
            write_timeout=WRITE_TIMEOUT,
            connect_timeout=CONNECT_TIMEOUT,
            pool_timeout=POOL_TIMEOUT,
        )
        return (
            Application.builder()
            .post_init(self.post_init)
            .post_shutdown(self.post_shutdown)
            .token(self.settings.telegram_token)
            .request(request)
            .build()
        )

    def _register_handlers(self) -> None:
        self.app.add_handlers(
            [
                CommandHandler("start", self.start),
                CommandHandler("stop", self.stop),
                CommandHandler("help", self.help),
                CommandHandler("latest", self.send_latest(None)),
                *(
                    CommandHandler(command, self.send_latest(post_type))
                    for command, post_type in (
                        ("news", PostType.NEWS),
                        ("update", PostType.UPDATE),
                        ("external", PostType.EXTERNAL),
                    )
                ),
                MessageHandler(
                    filters.StatusUpdate.NEW_CHAT_MEMBERS, self.new_chat_member
                ),
                MessageHandler(
                    filters.StatusUpdate.LEFT_CHAT_MEMBER, self.left_chat_member
                ),
                MessageHandler(filters.StatusUpdate.MIGRATE, self.migrate_chat),
            ]
        )

    async def async_init(self) -> None:
        await bootstrap(
            chat_db=self.chat_db,
            post_db=self.post_db,
            notifier=self.notifier,
            import_chats_from=self.settings.import_chats_from_json,
            import_posts_from=self.settings.import_posts_from_json,
        )

    async def post_init(self, application: Application) -> None:
        """Prepare storage and schedule the jobs, inside the loop PTB owns.

        Startup is async, but ``run_polling`` is not: it creates and manages
        the event loop itself. Doing the async setup here rather than in a
        loop of our own is what python-telegram-bot's post_init hook is for,
        and it keeps ``main`` free of event-loop bookkeeping.
        """
        logger.info("Post init bot...")
        await self.async_init()

        # Bot username is only available after initialization.
        self.username = application.bot.username
        logger.info("Bot username: %s. Bot is ready.", self.username)

        # Seed the heartbeat immediately so the healthcheck passes before the
        # first crawl cycle (which only runs after the crawl interval).
        write_heartbeat(self.settings.heartbeat_filepath)

        # Schedule the recurring jobs up-front so crawling and backups run
        # regardless of whether any chat has issued /start yet.
        if application.job_queue is None:
            logger.error("Job queue is not available. Periodic jobs not scheduled.")
            return

        application.job_queue.run_repeating(
            callback=self.post_checker, interval=self.settings.crawl_interval_seconds
        )
        application.job_queue.run_repeating(
            callback=self.backup_chats_db,
            interval=self.settings.chat_db_backup_interval_seconds,
        )

    async def post_shutdown(self, application: Application) -> None:
        logger.info("Shutting down bot...")

    async def post_checker(self, context: CallbackContext) -> None:
        # Refresh liveness before crawling so a flaky crawl still proves the
        # job queue is alive; the healthcheck only cares that this loop runs.
        write_heartbeat(self.settings.heartbeat_filepath)
        await self.notifier.check(context.bot)

    async def backup_chats_db(self, context: CallbackContext) -> None:
        logger.info("Backing up chat database ...")
        await ChatDatabaseBackupManager(
            chat_db=self.chat_db,
            backup_filepath=self.settings.chat_db_backup_filepath,
            max_backups=self.settings.chat_db_backup_count,
        ).run()

    def send_latest(
        self, post_type: PostType | None
    ) -> Callable[[Update, CallbackContext], Coroutine[Any, Any, None]]:
        """Build the handler for ``/latest``, ``/news``, ``/update``, ``/external``.

        One parameterised factory replaces four handlers that differed only in
        which cached post they read.
        """

        @spam_protected
        async def handler(
            bot: CounterStrike2UpdateBot, update: Update, context: CallbackContext
        ) -> None:
            if update.message is None:
                return

            post = bot.notifier.latest(post_type)
            if post is None:
                logger.info("No latest %s post available.", post_type or "")
                return

            logger.info("Sending latest %s post to chat ...", post_type or "")
            chat = await bot.chat_db.get(update.message.chat_id)
            message = await create_message(post)
            await bot.messenger.send(context.bot, message, chat)

        return functools.partial(handler, self)

    @spam_protected
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None or update.message.from_user is None:
            return

        chat_id = update.message.chat_id
        logger.info("Starting bot for chat_id=%s ...", chat_id)

        chat = await self.chat_db.get(chat_id)
        if chat is None:
            chat = Chat(chat_id)
            chat.chat_id_admin = update.message.from_user.id
            self.spam_protector.update_chat_activity(chat)
            await self.chat_db.add(chat)

        if chat.is_running:
            await update.message.reply_text(ALREADY_RUNNING_MESSAGE)
        else:
            chat.is_running = True
            await update.message.reply_text(
                text=const.WELCOME_MESSAGE_ENGLISH, parse_mode=ParseMode.HTML
            )
            await self.chat_db.update(chat)

        if chat.is_removed_while_banned:
            chat.is_removed_while_banned = False
            await self.chat_db.update(chat)

    @spam_protected
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return

        logger.info("Stopping bot for chat_id=%s ...", update.message.chat_id)

        chat = await self.chat_db.get(update.message.chat_id)
        if chat is None:
            logger.info("Chat not found. Nothing to do.")
            return

        chat_type = update.message.chat.type
        if chat_type in GROUP_CHAT_TYPES:
            # Keep the chat: it is only removed once the bot leaves the group.
            chat.is_running = False
            await self.chat_db.update(chat)
            await update.message.reply_text(STOPPED_MESSAGE)
        elif chat_type == ChatType.PRIVATE:
            await update.message.reply_text(STOPPED_MESSAGE)
            await self.chat_db.remove(chat)
        else:
            logger.error("Unknown chat type %s for chat_id=%s", chat_type, chat.chat_id)

    @spam_protected
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None:
            return

        logger.info("Sending help message to chat_id=%s ...", update.message.chat_id)

        chat = await self.chat_db.get(update.message.chat_id)
        if chat is None:
            logger.error("Chat not found. Not sending help message.")
            return

        await update.message.reply_text(text=HELP_MESSAGE, parse_mode=ParseMode.HTML)

    async def new_chat_member(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message is None or update.message.from_user is None:
            return

        for member in update.message.new_chat_members:
            if member.username != self.username:
                continue

            logger.info("Bot joined chat %s ...", update.message.chat_id)

            chat = await self.chat_db.get(update.message.chat_id)
            if chat is None:
                logger.info("Chat not found. Creating new chat...")
                chat = Chat(update.message.chat_id)

            chat.chat_id_admin = update.message.from_user.id
            await self.chat_db.add(chat)

    async def left_chat_member(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message is None or update.message.left_chat_member is None:
            return

        if update.message.left_chat_member.username != self.username:
            return

        logger.info("Bot left chat %s ...", update.message.chat_id)

        chat = await self.chat_db.get(update.message.chat_id)
        if chat is None:
            return

        logger.info("Removing chat from chat list...")
        await self.chat_db.remove(chat)

    async def migrate_chat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message is None:
            return

        if update.message.migrate_from_chat_id is None:
            # Two events fire for one migration; the second carries no origin.
            return

        logger.info(
            "Migrating chat from %s to %s ...",
            update.message.migrate_from_chat_id,
            update.message.chat_id,
        )

        chat = await self.chat_db.get(update.message.migrate_from_chat_id)
        if chat is None:
            logger.info("Chat already migrated or unknown. Nothing to do.")
            return

        await self.chat_db.migrate(chat, update.message.chat_id)
        logger.info("Chat migrated successfully.")

    def run(self) -> None:
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
