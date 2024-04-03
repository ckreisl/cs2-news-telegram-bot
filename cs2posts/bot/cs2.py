from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatType
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import Application
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import filters
from telegram.ext import MessageHandler

import cs2posts.bot.constants as const
from cs2posts.bot import settings
from cs2posts.bot.chats import Chat
from cs2posts.bot.chats import Chats
from cs2posts.bot.message import TelegramMessage
from cs2posts.bot.message import TelegramMessageFactory
from cs2posts.bot.options import Options
from cs2posts.bot.spam import SpamProtector
from cs2posts.crawler import CounterStrike2NetCrawler
from cs2posts.cs2 import CounterStrikeNetPosts
from cs2posts.post import Post
from cs2posts.store import LocalChatStore
from cs2posts.store import LocalLatestPostStore


logger = logging.getLogger(__name__)


def admin(func):
    async def wrapper(self, update: Update, context: CallbackContext):
        chat = self.chats.get(update.message.chat_id)
        if chat is None:
            return
        if update.message.from_user.id != chat.chat_id_admin:
            logger.warning(
                f'Unauthorized access to {func.__name__} by {update.message.from_user.id}')
            return
        return await func(self, update, context)
    return wrapper


def spam_protected(func):
    async def wrapper(self, update: Update, context: CallbackContext):
        chat = self.chats.get(update.message.chat_id)
        await self.spam_protector.check(context.bot, chat)
        if chat is not None and chat.is_banned:
            return
        return await func(self, update, context)
    return wrapper


class CounterStrike2UpdateBot:

    def __init__(self, *args, **kwargs) -> None:
        self.app = (Application.builder()
                    .post_init(self.post_init)
                    .post_shutdown(self.post_shutdown)
                    .token(kwargs['token'])
                    .build())

        self.crawler = CounterStrike2NetCrawler()
        self.spam_protector = SpamProtector()
        self.local_post_store = LocalLatestPostStore(
            settings.LOCAL_LATEST_POST_STORE_FILEPATH)
        self.local_chat_store = LocalChatStore(
            settings.LOCAL_CHAT_STORE_FILEPATH)

        self.options = Options(app=self.app)

        self.app.add_handlers([
            CommandHandler('start', self.start),
            CommandHandler('stop', self.stop),
            CommandHandler('help', self.help),
            CommandHandler('news', self.news),
            CommandHandler('update', self.update),
            CommandHandler('latest', self.latest),
            MessageHandler(
                filters.StatusUpdate.NEW_CHAT_MEMBERS, self.new_chat_member),
            MessageHandler(
                filters.StatusUpdate.LEFT_CHAT_MEMBER, self.left_chat_member),
        ])

        # self.app.add_error_handler(self.error)
        self.is_running = False
        self.__init_data()

    def __init_data(self) -> None:
        if self.local_chat_store.is_empty():
            logger.info('No chat data found. Creating new chat data...')
            self.local_chat_store.save(Chats())

        if self.local_post_store.is_empty():
            # TODO: Maybe ensure that there is a latest update and news post
            # As of now we just fetch 100 items.
            logger.info('No post data found. Fetching latest posts...')
            data = self.crawler.crawl()
            posts = CounterStrikeNetPosts(data)
            self.local_post_store.save(posts.latest_update_post)
            self.local_post_store.save(posts.latest_news_post)

        self.latest_post: Post = self.local_post_store.get_latest_post()
        self.latest_news_post: Post = self.local_post_store.get_latest_news_post()
        self.latest_update_post: Post = self.local_post_store.get_latest_update_post()
        self.chats: Chats = self.local_chat_store.load()
        self.options.set_chats(self.chats)

    def update_posts(self, post: Post) -> None:
        self.latest_post = post
        # TODO: Handle different types!
        if post.is_news() or post.is_event() or post.is_special():
            self.latest_news_post = post
        else:
            self.latest_update_post = post

    async def post_init(self, application: Application) -> None:
        logger.info('Post init bot...')
        # Bot username is only available after initialization
        self.username = application.bot.username
        logger.info(f'Bot username: {self.username}. Bot is ready.')

    async def post_shutdown(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info('Shutting down bot...')
        logger.info('Saving posts ...')
        self.local_post_store.save(self.latest_news_post)
        self.local_post_store.save(self.latest_update_post)

        logger.info('Saving chats...')
        self.local_chat_store.save(self.chats)

    async def new_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(f'New chat member {update.message.new_chat_members} ...')
        logger.info(f"Username: {update.message.from_user.username}")

        for member in update.message.new_chat_members:
            if member.username != self.username:
                continue

            logger.info(f'Bot joined chat {update.message.chat_id} ...')

            chat = self.chats.get(update.message.chat_id)
            if chat is None:
                logger.info('Chat not found. Creating new chat...')
                chat = Chat(chat_id=update.message.chat_id)
                self.chats.add(chat)
                self.local_chat_store.save(self.chats)

            chat.chat_id_admin = update.message.from_user.id

    async def left_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(f'Left chat member {update.message.left_chat_member} ...')

        if update.message.left_chat_member.username != self.username:
            return

        logger.info(f'Bot left chat {update.message.chat_id} ...')

        chat = self.chats.get(update.message.chat_id)
        if chat is None:
            return

        logger.info('Removing chat from chat list...')
        self.chats.remove(chat)
        self.local_chat_store.save(self.chats)

    @spam_protected
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(f'Starting bot for chat_id={update.message.chat_id} ...')

        chat_id = update.message.chat_id
        chat = self.chats.get(chat_id=chat_id)

        if chat is None:
            chat = self.chats.create_and_add(chat_id=chat_id)
            chat.chat_id_admin = update.message.from_user.id
            self.local_chat_store.save(self.chats)

        if not chat.is_running:
            chat.is_running = True
            await update.message.reply_text(
                text=const.WELCOME_MESSAGE_ENGLISH,
                parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(
                'Bot is already running for your chat!')

        if chat.is_removed_while_banned:
            chat.is_removed_while_banned = False

        if self.is_running:
            return

        # Check for posts every X seconds
        context.job_queue.run_repeating(
            callback=self.post_checker,
            interval=settings.CS2_UPDATE_CHECK_INTERVAL)

        self.is_running = True

    @spam_protected
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(f'Stopping bot for chat_id={update.message.chat_id} ...')

        chat = self.chats.get(update.message.chat_id)
        if chat is None:
            logger.info('Chat not found. Nothing to do.')
            return

        if chat.is_banned:
            chat.is_removed_while_banned = True
            return

        chat_type = update.message.chat.type
        if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
            chat.is_running = False
            await update.message.reply_text(
                'Bot is stopped for this chat. You can start it again with /start')
            # We do not remove the chat here, because we want to keep the chat
            # and only remove it if the bot is removed from the group chat.
            return

        if chat_type == ChatType.PRIVATE:
            self.chats.remove(chat)
            self.local_chat_store.save(self.chats)
            return

    @spam_protected
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(
            f'Sending help message to chat_id={update.message.chat_id} ...')

        chat = self.chats.get(update.message.chat_id)
        if chat is None:
            logger.error('Chat not found. Not sending help message.')
            return

        msg = ("/start - Starts the bot\n"
               "/stop - Stops the bot for this chat\n"
               "/latest - Sends the latest post\n"
               "/news - Sends the latest news post\n"
               "/update - Sends the latest update post\n"
               "/help - Prints this help message\n"
               "/options - Configure Options <b>(only admins)</b>")

        await update.message.reply_text(text=msg, parse_mode=ParseMode.HTML)

    @spam_protected
    async def latest(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info('Sending latest saved post to chat ...')
        chat = self.chats.get(update.message.chat_id)
        msg = TelegramMessageFactory.create(self.latest_post)
        await self.send_message(context=context, msg=msg, chat=chat)

    @spam_protected
    async def news(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info('Sending latest news post to chat ...')
        chat = self.chats.get(update.message.chat_id)
        msg = TelegramMessageFactory.create(self.latest_news_post)
        await self.send_message(context=context, msg=msg, chat=chat)

    @spam_protected
    async def update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info('Sending latest update post to chats ...')
        chat = self.chats.get(update.message.chat_id)
        msg = TelegramMessageFactory.create(self.latest_update_post)
        await self.send_message(context=context, msg=msg, chat=chat)

    async def post_checker(self, context: CallbackContext) -> None:
        logger.info('Crawling latest post ...')
        try:
            data = self.crawler.crawl(count=1)
        except Exception as e:
            logger.exception(f'Could not fetch latest post: {e}')
            return

        posts = CounterStrikeNetPosts(data)

        if posts.latest.posttime == self.latest_post.posttime:
            logger.info(
                f'No new post found {posts.latest.posttime_as_datetime=}')
            return

        logger.info(f'New post! ({posts.latest.posttime_as_datetime=})')

        self.update_posts(posts.latest)
        self.local_post_store.save(self.latest_post)

        await self.send_post_to_chats(context, self.latest_post)

    async def send_post_to_chats(self, context: CallbackContext, post: Post) -> None:
        logger.info('Sending post to chats ...')

        msg = TelegramMessageFactory.create(post=post)

        # Send to all chats that are interested in the post type
        if post.is_news() or post.is_special() or post.is_event():
            chats = [chat for chat in self.chats.get_running_chats()
                     if chat.is_news_interested]
        elif post.is_update():
            chats = [chat for chat in self.chats.get_running_chats()
                     if chat.is_update_interested]
        else:
            logger.error(f'Unknown post type {post}. Not sending any message.')
            return

        for chat in chats:
            await self.send_message(context=context, msg=msg, chat=chat)

    async def send_message(self, context: CallbackContext, msg: TelegramMessage, chat: Chat) -> None:

        if chat is None:
            logger.error('Chat is None. Not sending any message.')
            return

        try:
            await msg.send(context.bot, chat_id=chat.chat_id)
        except Forbidden as e:
            logger.error(
                f'Bot is blocked by user we delete the chat {chat.chat_id=}')
            logger.error(f"Reason: {e}")
            self.chats.remove(chat)
        except Exception as e:
            logger.exception(f'Could not send message to chat {chat.chat_id=}')
            logger.exception(f"Reason: {e}")

    async def error(self, update: Update, context: CallbackContext) -> None:
        logger.error(f'Update {update} caused error {context.error}')
        # TODO: Implement clean error handling

    def run(self) -> None:
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
