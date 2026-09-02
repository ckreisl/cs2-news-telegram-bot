from __future__ import annotations

import logging
from typing import Any

from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.db import ChatRepository
from cs2posts.db import PostRepository
from cs2posts.dto.post import Post
from cs2posts.dto.post import PostType
from cs2posts.exceptions import CrawlerError
from cs2posts.feed import PostFeed
from cs2posts.msg import create_message
from .messenger import ChatMessenger

logger = logging.getLogger(__name__)

CRAWL_COUNT = 10
SEED_CRAWL_COUNT = 100


class PostNotifier:
    """Finds newly published posts and fans them out to interested chats.

    Holds no Telegram application state, so the whole crawl-diff-dispatch
    cycle can be exercised with an in-memory repository and a fake bot.
    """

    def __init__(
        self,
        crawler: CounterStrike2Crawler,
        post_db: PostRepository,
        chat_db: ChatRepository,
        messenger: ChatMessenger,
    ) -> None:
        self._crawler = crawler
        self._post_db = post_db
        self._chat_db = chat_db
        self._messenger = messenger
        self._latest: dict[PostType, Post | None] = dict.fromkeys(PostType)
        self._latest_post: Post | None = None

    def latest(self, post_type: PostType | None = None) -> Post | None:
        """The newest post the bot has seen, optionally of one kind."""
        if post_type is None:
            return self._latest_post
        return self._latest[post_type]

    async def load(self) -> None:
        """Prime the in-memory view of what has already been announced."""
        for post_type in PostType:
            self._latest[post_type] = await self._post_db.latest(post_type)
        self._latest_post = await self._post_db.latest()

    async def seed_if_empty(self) -> None:
        """On a fresh install, record today's posts so they are not re-announced."""
        if not await self._post_db.is_empty():
            return

        logger.info("No post data found. Fetching latest posts...")
        try:
            payload = await self._crawler.crawl(count=SEED_CRAWL_COUNT)
        except CrawlerError as exc:
            # Not fatal: the next scheduled crawl seeds instead, and until then
            # the bot still serves commands.
            logger.error("Could not seed posts: %s", exc)
            return

        feed = PostFeed.from_api_response(payload)
        for post_type in PostType:
            post = feed.latest(post_type)
            if post is not None:
                await self._post_db.save(post)

    async def check(self, bot: Any) -> None:
        """One crawl cycle: announce whatever is newer than what we stored."""
        logger.info("Crawling latest posts ...")
        try:
            payload = await self._crawler.crawl(count=CRAWL_COUNT)
        except CrawlerError as exc:
            logger.error("Could not fetch latest posts: %s", exc)
            return

        feed = PostFeed.from_api_response(payload)
        if feed.is_empty():
            logger.info("No post(s) found in latest crawl.")
            return

        for post_type in PostType:
            await self._announce_if_new(bot, feed.latest(post_type))

        self._latest_post = await self._post_db.latest()

    def _is_new(self, post: Post) -> bool:
        last_seen = self._latest[post.type]
        # Never having seen this kind of post means the first one we find is
        # news to every subscriber; only a stored post can rule one out.
        return last_seen is None or post.is_newer_than(last_seen)

    async def _announce_if_new(self, bot: Any, post: Post | None) -> None:
        if post is None:
            return

        if not self._is_new(post):
            logger.info("No new %s post found; latest is %r", post.type, post.title)
            return

        logger.info("New %s post found: %r", post.type, post.title)
        self._latest[post.type] = post
        await self.broadcast(bot, post)
        await self._post_db.save(post)

    async def broadcast(self, bot: Any, post: Post) -> None:
        chats = await self._chat_db.running_chats_interested_in(post.type)
        logger.info("Sending %s post to %s chat(s) ...", post.type, len(chats))

        message = await create_message(post)
        for chat in chats:
            await self._messenger.send(bot, message, chat)
