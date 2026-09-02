from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from telegram.constants import ChatType

from cs2posts.bot.cs2 import ALREADY_RUNNING_MESSAGE
from cs2posts.bot.cs2 import HELP_MESSAGE
from cs2posts.bot.cs2 import STOPPED_MESSAGE
from cs2posts.bot.cs2 import CounterStrike2UpdateBot
from cs2posts.bot.spam import SpamProtector
from cs2posts.dto.chats import Chat
from cs2posts.dto.post import PostType
from tests.conftest import NOW
from tests.fakes import FakeBot
from tests.fakes import InMemoryChatRepository
from tests.fakes import InMemoryPostRepository

CHAT_ID = 1337
USER_ID = 99


class StubCrawler:
    async def crawl(self, *, count: int = 100):
        return {"appnews": {"newsitems": []}}


class Replies:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    @property
    def texts(self) -> list[str]:
        return [call["text"] for call in self.calls]

    async def __call__(self, text: str | None = None, **kwargs) -> None:
        self.calls.append({"text": text, **kwargs})


@pytest.fixture
def chat_db():
    return InMemoryChatRepository()


@pytest.fixture
def post_db():
    return InMemoryPostRepository()


@pytest.fixture
def bot(settings, clock, chat_db, post_db):
    """A bot wired to in-memory repositories and a stub Telegram application."""
    return CounterStrike2UpdateBot(
        settings=settings,
        crawler=StubCrawler(),
        spam_protector=SpamProtector(settings, clock),
        post_db=post_db,
        chat_db=chat_db,
        application=Mock(),
    )


@pytest.fixture
def telegram_bot():
    return FakeBot()


@pytest.fixture
def context(telegram_bot):
    context = Mock()
    context.bot = telegram_bot
    return context


def make_update(
    *,
    chat_id: int = CHAT_ID,
    user_id: int = USER_ID,
    chat_type: str = ChatType.PRIVATE,
) -> Mock:
    update = Mock()
    update.message.chat_id = chat_id
    update.message.chat.type = chat_type
    update.message.from_user.id = user_id
    update.message.reply_text = Replies()
    return update


# --- construction and wiring -------------------------------------------------


def test_the_application_is_built_with_generous_timeouts(settings, clock):
    with (
        patch("cs2posts.bot.cs2.Application.builder") as builder,
        patch("cs2posts.bot.cs2.HTTPXRequest") as request,
    ):
        chained = builder.return_value
        for method in ("post_init", "post_shutdown", "token", "request"):
            getattr(chained, method).return_value = chained
        chained.build.return_value = Mock()

        CounterStrike2UpdateBot(
            settings=settings,
            crawler=StubCrawler(),
            spam_protector=SpamProtector(settings, clock),
            post_db=InMemoryPostRepository(),
            chat_db=InMemoryChatRepository(),
        )

    request.assert_called_once_with(
        read_timeout=30, write_timeout=30, connect_timeout=15, pool_timeout=15
    )
    chained.token.assert_called_once_with(settings.telegram_token)


def test_every_command_is_registered(bot):
    (handlers,), _ = bot.app.add_handlers.call_args
    commands = {
        command for handler in handlers for command in getattr(handler, "commands", ())
    }

    assert commands == {"start", "stop", "help", "latest", "news", "update", "external"}


@pytest.mark.asyncio
async def test_post_init_records_the_username_and_schedules_the_jobs(bot, tmp_path):
    from dataclasses import replace

    bot.settings = replace(bot.settings, heartbeat_filepath=tmp_path / "beat")
    app = Mock()
    app.bot.username = "test_bot"

    await bot.post_init(app)

    assert bot.username == "test_bot"
    assert app.job_queue.run_repeating.call_count == 2
    assert (tmp_path / "beat").exists()


@pytest.mark.asyncio
async def test_post_init_prepares_storage(bot, tmp_path, chat_db, post_db):
    """Startup is async but run_polling is not, so bootstrap happens in the
    post_init hook -- inside the event loop python-telegram-bot owns."""
    from dataclasses import replace

    bot.settings = replace(bot.settings, heartbeat_filepath=tmp_path / "beat")
    app = Mock()
    app.bot.username = "test_bot"

    await bot.post_init(app)

    assert chat_db.is_setup
    assert post_db.is_setup


@pytest.mark.asyncio
async def test_post_init_without_a_job_queue_is_survivable(bot, tmp_path, caplog):
    from dataclasses import replace

    bot.settings = replace(bot.settings, heartbeat_filepath=tmp_path / "beat")
    app = Mock()
    app.job_queue = None

    await bot.post_init(app)

    assert "Job queue is not available" in caplog.text


@pytest.mark.asyncio
async def test_post_checker_refreshes_the_heartbeat(bot, context, tmp_path):
    from dataclasses import replace

    bot.settings = replace(bot.settings, heartbeat_filepath=tmp_path / "beat")

    await bot.post_checker(context)

    assert (tmp_path / "beat").exists()


def test_run_starts_polling(bot):
    bot.run()

    bot.app.run_polling.assert_called_once()


# --- /start ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_registers_a_new_chat_and_welcomes_it(bot, context, chat_db):
    update = make_update()

    await bot.start(update, context)

    chat = await chat_db.get(CHAT_ID)
    assert chat is not None
    assert chat.is_running
    assert chat.chat_id_admin == USER_ID
    assert "Welcome" in update.message.reply_text.texts[0]


@pytest.mark.asyncio
async def test_start_on_a_running_chat_says_so(bot, context, chat_db):
    await chat_db.add(Chat(CHAT_ID, chat_id_admin=USER_ID, is_running=True))

    await bot.start(make_update(), context)

    update = make_update()
    await bot.start(update, context)
    assert update.message.reply_text.texts == [ALREADY_RUNNING_MESSAGE]


@pytest.mark.asyncio
async def test_start_restarts_a_stopped_chat(bot, context, chat_db):
    await chat_db.add(Chat(CHAT_ID, chat_id_admin=USER_ID, is_running=False))

    await bot.start(make_update(), context)

    chat = await chat_db.get(CHAT_ID)
    assert chat is not None
    assert chat.is_running


@pytest.mark.asyncio
async def test_start_clears_the_removed_while_banned_flag(bot, context, chat_db):
    await chat_db.add(
        Chat(CHAT_ID, chat_id_admin=USER_ID, is_removed_while_banned=True)
    )

    await bot.start(make_update(), context)

    chat = await chat_db.get(CHAT_ID)
    assert chat is not None
    assert not chat.is_removed_while_banned


# --- /stop -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_on_an_unknown_chat_does_nothing(bot, context):
    update = make_update()

    await bot.stop(update, context)

    assert update.message.reply_text.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chat_type", [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]
)
async def test_stop_in_a_group_keeps_the_chat_but_pauses_it(
    bot, context, chat_db, chat_type
):
    await chat_db.add(Chat(CHAT_ID, is_running=True))
    update = make_update(chat_type=chat_type)

    await bot.stop(update, context)

    chat = await chat_db.get(CHAT_ID)
    assert chat is not None
    assert not chat.is_running
    assert update.message.reply_text.texts == [STOPPED_MESSAGE]


@pytest.mark.asyncio
async def test_stop_in_a_private_chat_removes_it(bot, context, chat_db):
    await chat_db.add(Chat(CHAT_ID, is_running=True))
    update = make_update(chat_type=ChatType.PRIVATE)

    await bot.stop(update, context)

    assert await chat_db.get(CHAT_ID) is None
    assert update.message.reply_text.texts == [STOPPED_MESSAGE]


@pytest.mark.asyncio
async def test_stop_with_an_unknown_chat_type_is_logged(bot, context, chat_db, caplog):
    await chat_db.add(Chat(CHAT_ID, is_running=True))

    await bot.stop(make_update(chat_type="carrier pigeon"), context)

    assert "Unknown chat type" in caplog.text
    chat = await chat_db.get(CHAT_ID)
    assert chat is not None
    assert chat.is_running


# --- /help -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_lists_the_commands(bot, context, chat_db):
    await chat_db.add(Chat(CHAT_ID))
    update = make_update()

    await bot.help(update, context)

    assert update.message.reply_text.texts == [HELP_MESSAGE]


@pytest.mark.asyncio
async def test_help_for_an_unknown_chat_is_skipped(bot, context, caplog):
    update = make_update()

    await bot.help(update, context)

    assert update.message.reply_text.calls == []
    assert "Chat not found" in caplog.text


# --- /latest, /news, /update, /external --------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("post_type", "title"),
    [
        (None, "Newest Overall"),
        (PostType.NEWS, "Some News"),
        (PostType.UPDATE, "Release Notes"),
        (PostType.EXTERNAL, "Elsewhere"),
    ],
)
async def test_the_latest_commands_send_the_cached_post(
    bot,
    context,
    chat_db,
    telegram_bot,
    post_db,
    make_post,
    http_response,
    post_type,
    title,
):
    http_response(url="https://example.com/resolved")
    await chat_db.add(Chat(CHAT_ID))
    await post_db.save(make_post(gid="n", title="Some News", date=10))
    await post_db.save(
        make_post(gid="u", title="Release Notes", date=20, tags=["patchnotes"])
    )
    await post_db.save(make_post(gid="e", title="Elsewhere", date=30, feed_type=0))
    if post_type is None:
        await post_db.save(make_post(gid="x", title="Newest Overall", date=99))
    await bot.notifier.load()

    await bot.send_latest(post_type)(make_update(), context)

    assert any(title in text for text in telegram_bot.texts)


@pytest.mark.asyncio
async def test_a_latest_command_with_nothing_cached_sends_nothing(
    bot, context, chat_db, telegram_bot, caplog
):
    await chat_db.add(Chat(CHAT_ID))
    await bot.notifier.load()

    await bot.send_latest(PostType.NEWS)(make_update(), context)

    assert telegram_bot.messages == []
    assert "No latest" in caplog.text


# --- spam protection ---------------------------------------------------------


@pytest.mark.asyncio
async def test_a_banned_chat_gets_no_reply(bot, context, chat_db):
    # Banned and still inside its timeout window.
    await chat_db.add(Chat(CHAT_ID, is_banned=True, last_activity=NOW))
    update = make_update()

    await bot.help(update, context)

    assert update.message.reply_text.calls == []


@pytest.mark.asyncio
async def test_spam_protection_keeps_the_handler_name(bot):
    assert bot.help.__name__ == "help"
    assert bot.start.__name__ == "start"


@pytest.mark.asyncio
async def test_an_update_without_a_message_is_ignored(bot, context):
    update = Mock()
    update.message = None

    await bot.help(update, context)
    await bot.start(update, context)
    await bot.stop(update, context)


# --- membership events -------------------------------------------------------


@pytest.mark.asyncio
async def test_being_added_to_a_chat_registers_it(bot, context, chat_db):
    bot.username = "cs2bot"
    update = make_update()
    member = Mock()
    member.username = "cs2bot"
    update.message.new_chat_members = [member]

    await bot.new_chat_member(update, context)

    chat = await chat_db.get(CHAT_ID)
    assert chat is not None
    assert chat.chat_id_admin == USER_ID


@pytest.mark.asyncio
async def test_another_member_joining_is_ignored(bot, context, chat_db):
    bot.username = "cs2bot"
    update = make_update()
    member = Mock()
    member.username = "someone_else"
    update.message.new_chat_members = [member]

    await bot.new_chat_member(update, context)

    assert await chat_db.get(CHAT_ID) is None


@pytest.mark.asyncio
async def test_being_removed_from_a_chat_deletes_it(bot, context, chat_db):
    bot.username = "cs2bot"
    await chat_db.add(Chat(CHAT_ID))
    update = make_update()
    update.message.left_chat_member.username = "cs2bot"

    await bot.left_chat_member(update, context)

    assert await chat_db.get(CHAT_ID) is None


@pytest.mark.asyncio
async def test_another_member_leaving_is_ignored(bot, context, chat_db):
    bot.username = "cs2bot"
    await chat_db.add(Chat(CHAT_ID))
    update = make_update()
    update.message.left_chat_member.username = "someone_else"

    await bot.left_chat_member(update, context)

    assert await chat_db.get(CHAT_ID) is not None


@pytest.mark.asyncio
async def test_leaving_an_unknown_chat_is_survivable(bot, context):
    bot.username = "cs2bot"
    update = make_update()
    update.message.left_chat_member.username = "cs2bot"

    await bot.left_chat_member(update, context)


@pytest.mark.asyncio
@pytest.mark.parametrize("handler", ["new_chat_member", "left_chat_member"])
async def test_membership_events_without_a_message_are_ignored(bot, context, handler):
    update = Mock()
    update.message = None

    await getattr(bot, handler)(update, context)


@pytest.mark.asyncio
async def test_a_migration_moves_the_chat_to_its_new_id(bot, context, chat_db):
    await chat_db.add(Chat(42))
    update = make_update(chat_id=-100)
    update.message.migrate_from_chat_id = 42

    await bot.migrate_chat(update, context)

    assert await chat_db.get(42) is None
    assert await chat_db.get(-100) is not None


@pytest.mark.asyncio
async def test_the_second_migration_event_is_ignored(bot, context, chat_db):
    update = make_update(chat_id=-100)
    update.message.migrate_from_chat_id = None

    await bot.migrate_chat(update, context)

    assert await chat_db.get(-100) is None


@pytest.mark.asyncio
async def test_migrating_an_unknown_chat_is_survivable(bot, context, caplog):
    update = make_update(chat_id=-100)
    update.message.migrate_from_chat_id = 42

    await bot.migrate_chat(update, context)

    assert "Nothing to do" in caplog.text


# --- backups -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_backup_job_writes_a_timestamped_file(
    bot, context, chat_db, tmp_path
):
    from dataclasses import replace

    bot.settings = replace(bot.settings, chat_db_backup_filepath=tmp_path / "backup.db")

    await bot.backup_chats_db(context)

    (written,) = chat_db.backups
    assert written.parent == tmp_path
    assert written.name.startswith("backup_")
    assert written.suffix == ".db"


@pytest.mark.asyncio
async def test_being_re_added_to_a_known_chat_updates_it(bot, context, chat_db):
    """Regression: the handler issued a bare INSERT even when the row already
    existed, so a redelivered join update -- or a re-add after the bot was
    removed while offline -- failed on the primary key."""
    bot.username = "cs2bot"
    await chat_db.add(Chat(CHAT_ID, chat_id_admin=1, is_running=True))
    update = make_update()
    member = Mock()
    member.username = "cs2bot"
    update.message.new_chat_members = [member]

    await bot.new_chat_member(update, context)

    chat = await chat_db.get(CHAT_ID)
    assert chat is not None
    assert chat.chat_id_admin == USER_ID
    # The rest of the chat's state survives re-registration.
    assert chat.is_running
