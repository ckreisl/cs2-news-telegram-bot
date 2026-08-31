from __future__ import annotations

import pytest

from cs2posts.bot.messenger import ChatMessenger
from cs2posts.bot.notifier import PostNotifier
from cs2posts.dto.post import PostType
from cs2posts.exceptions import SteamApiUnavailable
from tests.fakes import FakeBot
from tests.fakes import InMemoryChatRepository
from tests.fakes import InMemoryPostRepository


class StubCrawler:
    """Answers with a queued payload, or raises a queued error."""

    def __init__(self, payload=None, error: Exception | None = None) -> None:
        self.payload = (
            payload if payload is not None else {"appnews": {"newsitems": []}}
        )
        self.error = error
        self.counts: list[int] = []

    async def crawl(self, *, count: int = 100):
        self.counts.append(count)
        if self.error is not None:
            raise self.error
        return self.payload


def newsitem(gid: str, date: int, **overrides) -> dict:
    item = {
        "gid": gid,
        "title": "A Post",
        "url": "https://example.com/post",
        "is_external_url": False,
        "author": "Valve",
        "contents": "Contents",
        "feedlabel": "label",
        "date": date,
        "feedname": "feed",
        "feed_type": 1,
        "appid": 730,
    }
    item.update(overrides)
    return item


def payload(*items: dict) -> dict:
    return {"appnews": {"appid": 730, "newsitems": list(items)}}


NEWS = newsitem("news-new", 1_800_000_000, title="Fresh News")
UPDATE = newsitem(
    "update-new", 1_800_000_100, title="Release Notes", tags=["patchnotes"]
)
EXTERNAL = newsitem("external-new", 1_800_000_200, title="Elsewhere", feed_type=0)


def build(crawler, chats=None, posts=None):
    chat_db = InMemoryChatRepository(chats or [])
    post_db = InMemoryPostRepository(posts or [])
    notifier = PostNotifier(
        crawler=crawler,
        post_db=post_db,
        chat_db=chat_db,
        messenger=ChatMessenger(chat_db),
    )
    return notifier, chat_db, post_db


@pytest.fixture(autouse=True)
def stub_http(http_response):
    """Message rendering resolves the post's source URL over HTTP."""
    http_response(url="https://example.com/resolved")


@pytest.fixture
def bot():
    return FakeBot()


@pytest.mark.asyncio
async def test_load_primes_the_latest_post_of_each_type(make_post):
    stored = [
        make_post(gid="n", date=10),
        make_post(gid="u", date=20, tags=["patchnotes"]),
        make_post(gid="e", date=30, feed_type=0),
    ]
    notifier, _, _ = build(StubCrawler(), posts=stored)

    await notifier.load()

    assert notifier.latest(PostType.NEWS).gid == "n"
    assert notifier.latest(PostType.UPDATE).gid == "u"
    assert notifier.latest(PostType.EXTERNAL).gid == "e"
    assert notifier.latest().gid == "e"


@pytest.mark.asyncio
async def test_seeding_stores_one_post_of_each_type_when_the_db_is_empty():
    notifier, _, post_db = build(StubCrawler(payload(NEWS, UPDATE, EXTERNAL)))

    await notifier.seed_if_empty()

    assert set(post_db.posts) == {"news-new", "update-new", "external-new"}


@pytest.mark.asyncio
async def test_seeding_is_skipped_when_posts_already_exist(make_post):
    crawler = StubCrawler(payload(NEWS))
    notifier, _, post_db = build(crawler, posts=[make_post(gid="existing")])

    await notifier.seed_if_empty()

    assert crawler.counts == []
    assert set(post_db.posts) == {"existing"}


@pytest.mark.asyncio
async def test_a_failed_seed_crawl_does_not_stop_startup(caplog):
    crawler = StubCrawler(error=SteamApiUnavailable("steam is down"))
    notifier, _, post_db = build(crawler)

    await notifier.seed_if_empty()

    assert post_db.posts == {}
    assert "Could not seed posts" in caplog.text


@pytest.mark.asyncio
async def test_a_failed_crawl_is_logged_and_swallowed(bot, caplog):
    crawler = StubCrawler(error=SteamApiUnavailable("steam is down"))
    notifier, _, _ = build(crawler)

    await notifier.check(bot)

    assert "Could not fetch latest posts" in caplog.text
    assert bot.messages == []


@pytest.mark.asyncio
async def test_an_empty_crawl_announces_nothing(bot, make_chat, caplog):
    notifier, _, _ = build(StubCrawler(payload()), chats=[make_chat()])

    await notifier.check(bot)

    assert "No post(s) found" in caplog.text
    assert bot.messages == []


@pytest.mark.asyncio
async def test_a_new_post_is_sent_to_an_interested_running_chat(bot, make_chat):
    notifier, _, post_db = build(StubCrawler(payload(NEWS)), chats=[make_chat()])
    await notifier.load()

    await notifier.check(bot)

    assert any("Fresh News" in text for text in bot.texts)
    assert "news-new" in post_db.posts


@pytest.mark.asyncio
async def test_a_post_older_than_the_stored_one_is_not_resent(
    bot, make_chat, make_post
):
    already_seen = make_post(gid="news-old", date=1_900_000_000, title="Old but newer")
    notifier, _, _ = build(
        StubCrawler(payload(NEWS)), chats=[make_chat()], posts=[already_seen]
    )
    await notifier.load()

    await notifier.check(bot)

    assert bot.messages == []


@pytest.mark.asyncio
async def test_the_same_post_is_announced_only_once(bot, make_chat):
    notifier, _, _ = build(StubCrawler(payload(NEWS)), chats=[make_chat()])
    await notifier.load()

    await notifier.check(bot)
    first_round = len(bot.messages)
    await notifier.check(bot)

    assert len(bot.messages) == first_round


@pytest.mark.asyncio
async def test_each_post_type_is_announced_independently(bot, make_chat):
    notifier, _, post_db = build(
        StubCrawler(payload(NEWS, UPDATE, EXTERNAL)), chats=[make_chat()]
    )
    await notifier.load()

    await notifier.check(bot)

    assert set(post_db.posts) == {"news-new", "update-new", "external-new"}


@pytest.mark.asyncio
async def test_a_stopped_chat_receives_nothing(bot, make_chat):
    notifier, _, _ = build(
        StubCrawler(payload(NEWS)), chats=[make_chat(is_running=False)]
    )
    await notifier.load()

    await notifier.check(bot)

    assert bot.messages == []


@pytest.mark.asyncio
async def test_an_uninterested_chat_receives_nothing(bot, make_chat):
    chat = make_chat()
    chat.set_interest(PostType.NEWS, False)
    notifier, _, _ = build(StubCrawler(payload(NEWS)), chats=[chat])
    await notifier.load()

    await notifier.check(bot)

    assert bot.messages == []


@pytest.mark.asyncio
async def test_only_chats_interested_in_that_type_are_reached(bot, make_chat):
    news_only = make_chat(1)
    news_only.set_interest(PostType.UPDATE, False)
    update_only = make_chat(2)
    update_only.set_interest(PostType.NEWS, False)

    notifier, _, _ = build(StubCrawler(payload(UPDATE)), chats=[news_only, update_only])
    await notifier.load()

    await notifier.check(bot)

    assert {message["chat_id"] for message in bot.messages} == {2}


@pytest.mark.asyncio
async def test_the_first_post_of_a_never_seen_type_is_announced(bot, make_chat):
    """With nothing stored for a type, its first sighting is news to everyone."""
    notifier, _, _ = build(StubCrawler(payload(EXTERNAL)), chats=[make_chat()])
    await notifier.load()

    await notifier.check(bot)

    assert any("Elsewhere" in text for text in bot.texts)


@pytest.mark.asyncio
async def test_check_asks_for_a_small_page_of_posts(bot):
    crawler = StubCrawler(payload(NEWS))
    notifier, _, _ = build(crawler)

    await notifier.check(bot)

    assert crawler.counts == [10]
