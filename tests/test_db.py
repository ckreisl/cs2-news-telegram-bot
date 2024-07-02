from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import pytest_asyncio

from cs2posts.bot.chats import Chat
from cs2posts.db import ChatDatabase
from cs2posts.db import PostDatabase
from cs2posts.db import SQLite
from cs2posts.post import Post


@pytest.fixture
def data_latest():
    return {
        "update": {
            "gid": "5762994032385146001",
            "title": "Release Notes for 4/16/2024",
            "url": "https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5762994032385146001",
            "is_external_url": True,
            "author": "Vitaliy",
            "contents": "[ MISC ]\n[list]\n[*] Fixed a bug where bomb can sometimes disappear from the radar\n[*] Allow scraping or removing stickers by selecting the sticker icons under the weapon\n[*] Allow deleting empty storage units that have an assigned label\n[*] Fixed Workshop tools from crashing when compiling maps that contain instances\n[/list]",
            "feedlabel": "Community Announcements",
            "date": 1713310428,
            "feedname": "steam_community_announcements",
            "feed_type": 1,
            "appid": 730,
            "tags": [
                "patchnotes"
            ]
        },
        "news": {
            "gid": "5756237364302520223",
            "title": "Copenhagen Major Champions",
            "url": "https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5756237364302520223",
            "is_external_url": True,
            "author": "Piggles ULTRAPRO",
            "contents": "[img]https://clan.akamai.steamstatic.com/images/3381077/75c3204fcb2874385f7c3e1dafeb00003b76502e.png[/img]\nCongratulations to Natus Vincere, the first CS2 Major Champions!\n\nPlaying in front of a sold-out arena and with over 1.8 million viewers watching around the world, NAVI and FaZe met in the Grand Final of one of the most hotly-contested Counter-Strike Majors of all time. Trading map wins in Ancient and Mirage, the teams moved to Inferno for the decider. There, b1t, jL, Aleksib, iM, and w0nderful put on a dominating performance to earn the trophy and title of Major Champions.\n\nTo celebrate their achievement, the Copenhagen 2024 Major Champions Capsule is now available for purchase. The capsule features autographs for each member of the winning team in paper, glitter, holo, and gold. 50% of the proceeds go to the players and organizations.\n\nAnd with that, the Copenhagen Major has come to a close. See you next time in Shanghai!",
            "feedlabel": "Community Announcements",
            "date": 1712103491,
            "feedname": "steam_community_announcements",
            "feed_type": 1,
            "appid": 730,
            "tags": []
        },
        "external": {
            "gid": "5759616966667952408",
            "title": "Lefties unite! Counter-Strike 2 now lets you swap hands",
            "url": "https://steamstore-a.akamaihd.net/news/externalpost/GamingOnLinux/5759616966667952408",
            "is_external_url": True,
            "author": "",
            "contents": "<p><p>All you Lefties out there can finally get properly represented, in Counter-Strike 2 that is, as there's now the ability to swap your weapons into the other hand.</p><p><img src=\"https://www.gamingonlinux.com/uploads/articles/tagline_images/350555862id24405gol.jpg\" alt /></p><p>Read the full article here: https://www.gamingonlinux.com/2024/04/lefties-unite-counter-strike-2-now-lets-you-swap-hands</p></p>",
            "feedlabel": "GamingOnLinux",
            "date": 1714131032,
            "feedname": "GamingOnLinux",
            "feed_type": 0,
            "appid": 730,
            "tags": []
        }
    }


@pytest_asyncio.fixture
async def post_empty_database(tmp_path):
    filepath = tmp_path / "test_posts.db"
    db = PostDatabase(filepath)
    await db.create_table()
    yield db


@pytest_asyncio.fixture
async def post_database(post_empty_database, data_latest):
    await post_empty_database.save(Post(**data_latest["update"]))
    await post_empty_database.save(Post(**data_latest["news"]))
    await post_empty_database.save(Post(**data_latest["external"]))

    yield post_empty_database


@pytest.fixture
def data_chats():
    return {"chats": [Chat(1337), Chat(42)]}


@pytest_asyncio.fixture
async def chats_empty_database(tmp_path):
    filepath = tmp_path / "test_chats.db"
    db = ChatDatabase(filepath)
    await db.create_table()
    yield db


@pytest_asyncio.fixture
async def chats_database(chats_empty_database, data_chats):
    for chat in data_chats["chats"]:
        await chats_empty_database.save(chat)

    yield chats_empty_database


@pytest.mark.asyncio
async def test_database_is_empty(post_empty_database, chats_empty_database):
    is_empty_post = await post_empty_database.is_empty()
    assert is_empty_post
    is_empty_chat = await chats_empty_database.is_empty()
    assert is_empty_chat


@pytest.mark.asyncio
async def test_database_is_not_empty(post_database, chats_database):
    post_db_empty = await post_database.is_empty()
    assert not post_db_empty
    chat_db_empty = await chats_database.is_empty()
    assert not chat_db_empty


@pytest.mark.asyncio
async def test_post_database_get_latest_post_empty_db(post_empty_database):
    assert await post_empty_database.get_latest_post() is None


@pytest.mark.asyncio
async def test_post_database_get_latest_post(post_database):
    actual_latest_post = await post_database.get_latest_post()
    expected_latest_post = await post_database.get_latest_external_post()
    assert actual_latest_post == expected_latest_post


@pytest.mark.asyncio
async def test_post_database_save_with_none(post_empty_database):
    await post_empty_database.save(None)
    assert await post_empty_database.load() == []
    assert await post_empty_database.get_latest_news_post() is None
    assert await post_empty_database.get_latest_update_post() is None
    assert await post_empty_database.get_latest_external_post() is None


@pytest.mark.asyncio
async def test_post_database_save(post_database, data_latest):
    expected_temp_update_title = data_latest["news"]["title"]

    data_latest["update"]["title"] = "New Update headline"
    data_latest["news"]["title"] = "New News headline"
    data_latest["external"]["title"] = "New External headline"

    actual_post_update = Post(**data_latest["update"])
    actual_post_news = Post(**data_latest["news"])
    actual_post_external = Post(**data_latest["external"])

    await post_database.save(actual_post_update)
    latest_update_post = await post_database.get_latest_update_post()
    latest_news_post = await post_database.get_latest_news_post()

    # News headline should not be changed
    assert latest_news_post.title == expected_temp_update_title
    assert latest_update_post.title == "New Update headline"

    await post_database.save(actual_post_news)

    latest_news_post = await post_database.get_latest_news_post()
    assert latest_news_post.title == "New News headline"

    await post_database.save(actual_post_external)
    actual_latest_external_post_db = await post_database.get_latest_external_post()
    assert actual_latest_external_post_db.title == "New External headline"


@pytest.mark.asyncio
async def test_post_database_get_latest_news_post(post_database, data_latest):
    actual_post = await post_database.get_latest_news_post()
    expected_post = Post(**data_latest["news"])
    assert actual_post == expected_post


@pytest.mark.asyncio
async def test_post_database_get_latest_update_post(post_database, data_latest):
    actual_post = await post_database.get_latest_update_post()
    expected_post = Post(**data_latest["update"])
    assert actual_post == expected_post


@pytest.mark.asyncio
async def test_post_database_load(post_database, data_latest):
    actual_posts = await post_database.load()
    assert isinstance(actual_posts, list)
    assert len(actual_posts) == 3
    expected_posts = [
        Post(**data_latest["update"]),
        Post(**data_latest["news"]),
        Post(**data_latest["external"]),
    ]
    assert actual_posts == expected_posts


@pytest.mark.asyncio
async def test_chats_database_load(chats_database):
    chats = await chats_database.load()
    assert isinstance(chats, list)
    assert len(chats) == 2
    assert Chat(1337) in chats
    assert Chat(42) in chats


@pytest.mark.asyncio
async def test_chats_database_get(chats_database):
    chat = await chats_database.get(1337)
    assert chat.chat_id == 1337
    assert chat.strikes == 0
    assert not chat.is_banned
    chat = await chats_database.get(43)
    assert chat is None


@pytest.mark.asyncio
async def test_chats_database_add(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    actual_chat = await chats_empty_database.get(1337)
    assert actual_chat == chat


@pytest.mark.asyncio
async def test_chats_database_remove(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    assert await chats_empty_database.get(1337) == chat
    await chats_empty_database.remove(chat)
    assert await chats_empty_database.get(1337) is None


@pytest.mark.asyncio
async def test_chats_database_update(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    assert chat.strikes == 0
    chat.strikes = 3
    await chats_empty_database.update(chat)
    actual_chat = await chats_empty_database.get(1337)
    assert actual_chat.strikes == 3


@pytest.mark.asyncio
async def test_chats_database_migrate(chats_empty_database):
    chat = Chat(1337)
    await chats_empty_database.add(chat)
    assert await chats_empty_database.get(1337) == chat
    chat = await chats_empty_database.migrate(chat, 42)
    assert await chats_empty_database.get(1337) is None
    assert await chats_empty_database.get(42) == chat


@pytest.mark.asyncio
async def test_chats_database_save(chats_empty_database):
    assert await chats_empty_database.load() == []
    await chats_empty_database.save(None)
    assert await chats_empty_database.load() == []

    expected_chats = [Chat(41), Chat(1338)]
    for chat in expected_chats:
        await chats_empty_database.save(chat=chat)
    actual_chats = await chats_empty_database.load()

    assert len(expected_chats) == len(actual_chats)
    assert actual_chats == expected_chats


@pytest.mark.asyncio
async def test_chats_database_get_running_chats(chats_database):
    chat = await chats_database.get(1337)
    assert not chat.is_running
    chat.is_running = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_chats()) == 1
    acutal_running_chats = await chats_database.get_running_chats()
    assert acutal_running_chats[0] == chat


@pytest.mark.asyncio
async def test_chats_database_interested_in_news(chats_database):
    assert len(await chats_database.get_interested_in_news_chats()) == 2
    chat = await chats_database.get(1337)
    chat.is_news_interested = False
    await chats_database.update(chat)
    assert len(await chats_database.get_interested_in_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_interested_in_updates(chats_database):
    assert len(await chats_database.get_interested_in_updates_chats()) == 2
    chat = await chats_database.get(1337)
    chat.is_update_interested = False
    await chats_database.update(chat)
    assert len(await chats_database.get_interested_in_updates_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_interested_in_external_news(chats_database):
    assert len(await chats_database.get_interested_in_external_news_chats()) == 2
    chat = await chats_database.get(1337)
    chat.is_external_news_interested = False
    await chats_database.update(chat)
    assert len(await chats_database.get_interested_in_external_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_get_running_and_interested_in_news_chats(chats_database):
    assert len(await chats_database.get_running_and_interested_in_news_chats()) == 0
    chat = await chats_database.get(1337)
    chat.is_running = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_and_interested_in_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_get_running_and_interested_in_updates_chats(chats_database):
    assert len(await chats_database.get_running_and_interested_in_updates_chats()) == 0
    chat = await chats_database.get(1337)
    chat.is_running = True
    chat.is_update_interested = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_and_interested_in_updates_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_get_running_and_interested_in_external_news_chats(chats_database):
    assert len(await chats_database.get_running_and_interested_in_external_news_chats()) == 0
    chat = await chats_database.get(1337)
    chat.is_running = True
    chat.is_external_news_interested = True
    await chats_database.update(chat)
    assert len(await chats_database.get_running_and_interested_in_external_news_chats()) == 1


@pytest.mark.asyncio
async def test_chats_database_contains(chats_database):
    assert await chats_database.contains(Chat(1337))
    assert not await chats_database.contains(Chat(43))
    assert await chats_database.contains(Chat(42))


@pytest.mark.asyncio
async def test_chat_database_len(chats_database):
    assert await chats_database.size() == 2
    chat = Chat(43)
    await chats_database.add(chat)
    assert await chats_database.size() == 3
    await chats_database.remove(chat)
    assert await chats_database.size() == 2


@pytest.mark.asyncio
@patch('aiosqlite.connect')
async def test_sqlite_class_create_db_exists(sqlite_mock):
    mocked_path = Mock()
    mocked_path.exists.return_value = True
    db = SQLite(mocked_path)
    sqlite_mock.assert_not_called()
    await db.create()
    sqlite_mock.assert_not_called()


@pytest.mark.asyncio
@patch('aiosqlite.connect')
async def test_sqlite_class_create_db_exists_overwrite(sqlite_mock):
    mocked_path = Mock()
    mocked_path.exists.side_effect = [True, False]
    db = SQLite(mocked_path)

    sqlite_mock.__aenter__.return_value.execute = AsyncMock()
    sqlite_mock.__aexit__ = AsyncMock()

    await db.create(overwrite=True)
    mocked_path.unlink.assert_called_once()
    sqlite_mock.assert_called_once_with(mocked_path)
