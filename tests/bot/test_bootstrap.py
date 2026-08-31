from __future__ import annotations

import pytest

from cs2posts.bot.bootstrap import bootstrap
from cs2posts.bot.bootstrap import import_json
from cs2posts.bot.messenger import ChatMessenger
from cs2posts.bot.notifier import PostNotifier
from tests.fakes import InMemoryChatRepository
from tests.fakes import InMemoryPostRepository


class StubCrawler:
    def __init__(self) -> None:
        self.calls = 0

    async def crawl(self, *, count: int = 100):
        self.calls += 1
        return {"appnews": {"newsitems": []}}


class ExplodingImporter:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def import_from_json(self, filepath) -> None:
        raise self.error


@pytest.fixture
def repositories():
    return InMemoryChatRepository(), InMemoryPostRepository()


@pytest.fixture
def notifier(repositories):
    chat_db, post_db = repositories
    return PostNotifier(
        crawler=StubCrawler(),
        post_db=post_db,
        chat_db=chat_db,
        messenger=ChatMessenger(chat_db),
    )


@pytest.mark.asyncio
async def test_bootstrap_prepares_both_repositories(repositories, notifier):
    chat_db, post_db = repositories

    await bootstrap(chat_db=chat_db, post_db=post_db, notifier=notifier)

    assert chat_db.is_setup
    assert post_db.is_setup


@pytest.mark.asyncio
async def test_bootstrap_imports_json_when_configured(repositories, notifier, tmp_path):
    chat_db, post_db = repositories
    chats_json = tmp_path / "chats.json"
    posts_json = tmp_path / "posts.json"

    await bootstrap(
        chat_db=chat_db,
        post_db=post_db,
        notifier=notifier,
        import_chats_from=chats_json,
        import_posts_from=posts_json,
    )

    assert chat_db.imported == [chats_json]
    assert post_db.imported == [posts_json]


@pytest.mark.asyncio
async def test_bootstrap_skips_import_when_not_configured(repositories, notifier):
    chat_db, post_db = repositories

    await bootstrap(chat_db=chat_db, post_db=post_db, notifier=notifier)

    assert chat_db.imported == []
    assert post_db.imported == []


@pytest.mark.asyncio
async def test_import_json_does_nothing_without_a_path():
    await import_json(ExplodingImporter(OSError("boom")), None, "chats")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error", [OSError("missing"), ValueError("bad json"), KeyError("field")]
)
async def test_a_broken_import_is_logged_not_raised(tmp_path, caplog, error):
    await import_json(ExplodingImporter(error), tmp_path / "x.json", "chats")

    assert "Could not import chats" in caplog.text


@pytest.mark.asyncio
async def test_bootstrap_leaves_the_notifier_primed(repositories, notifier, make_post):
    chat_db, post_db = repositories
    await post_db.save(make_post(gid="seen", date=42))

    await bootstrap(chat_db=chat_db, post_db=post_db, notifier=notifier)

    assert notifier.latest().gid == "seen"
