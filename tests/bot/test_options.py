from __future__ import annotations

from unittest.mock import Mock

import pytest
from telegram.constants import ParseMode

from cs2posts.bot.options import CLOSE
from cs2posts.bot.options import Options
from cs2posts.bot.options import create_options_keyboard
from cs2posts.bot.options import create_options_text
from cs2posts.bot.options import enabled_icon
from cs2posts.dto.chats import Chat
from cs2posts.dto.post import PostType
from tests.fakes import FakeBot
from tests.fakes import InMemoryChatRepository

ADMIN_ID = 99
CHAT_ID = 1337


@pytest.fixture
def chat():
    return Chat(chat_id=CHAT_ID, chat_id_admin=ADMIN_ID)


@pytest.fixture
def chat_db(chat):
    return InMemoryChatRepository([chat])


@pytest.fixture
def app():
    return Mock()


@pytest.fixture
def options(app, chat_db):
    return Options(app=app, chat_db=chat_db)


@pytest.fixture
def bot():
    return FakeBot()


@pytest.fixture
def context(bot):
    context = Mock()
    context.bot = bot
    return context


def make_update(*, user_id: int = ADMIN_ID, chat_id: int = CHAT_ID) -> Mock:
    update = Mock()
    update.message.chat_id = chat_id
    update.message.from_user.id = user_id
    update.message.reply_text = _AsyncRecorder()
    return update


def make_callback_update(
    data: str, *, user_id: int = ADMIN_ID, chat_id: int = CHAT_ID
) -> Mock:
    update = Mock()
    update.callback_query.data = data
    update.callback_query.from_user.id = user_id
    update.callback_query.message.chat_id = chat_id
    update.callback_query.message.message_id = 5
    update.callback_query.answer = _AsyncRecorder()
    return update


class _AsyncRecorder:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def __call__(self, **kwargs) -> None:
        self.calls.append(kwargs)


def test_options_registers_its_handlers(app, chat_db):
    Options(app=app, chat_db=chat_db)

    assert app.add_handler.call_count == 2


def test_enabled_icon_distinguishes_the_two_states():
    assert enabled_icon(True) != enabled_icon(False)


def test_the_keyboard_offers_one_button_per_post_type_plus_close(chat):
    buttons = [button for row in create_options_keyboard(chat) for button in row]

    assert {button.callback_data for button in buttons} == {
        *(post_type.value for post_type in PostType),
        CLOSE,
    }


def test_an_enabled_type_offers_to_disable_it(chat):
    chat.set_interest(PostType.NEWS, True)

    buttons = [button for row in create_options_keyboard(chat) for button in row]
    news = next(b for b in buttons if b.callback_data == PostType.NEWS.value)

    assert news.text == "Disable News"


def test_a_disabled_type_offers_to_enable_it(chat):
    chat.set_interest(PostType.NEWS, False)

    buttons = [button for row in create_options_keyboard(chat) for button in row]
    news = next(b for b in buttons if b.callback_data == PostType.NEWS.value)

    assert news.text == "Enable News"


def test_the_text_reports_every_post_type(chat):
    chat.set_interest(PostType.UPDATE, False)

    text = create_options_text(chat)

    assert "Send Updates Posts (disabled)" in text
    assert "Send News Posts (enabled)" in text
    assert "Send External News Posts (enabled)" in text


@pytest.mark.asyncio
async def test_the_admin_gets_the_options_message(options, context):
    update = make_update()

    await options.options(update, context)

    (call,) = update.message.reply_text.calls
    assert "<b>Options</b>" in call["text"]
    assert call["parse_mode"] == ParseMode.HTML


@pytest.mark.asyncio
async def test_a_non_admin_gets_nothing(options, context):
    update = make_update(user_id=ADMIN_ID + 1)

    await options.options(update, context)

    assert update.message.reply_text.calls == []


@pytest.mark.asyncio
async def test_an_unknown_chat_gets_nothing(options, context):
    update = make_update(chat_id=404)

    await options.options(update, context)

    assert update.message.reply_text.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("post_type", list(PostType))
async def test_pressing_a_button_toggles_that_interest(
    options, context, chat, chat_db, post_type
):
    chat.set_interest(post_type, True)
    update = make_callback_update(post_type.value)

    await options.button(update, context)

    stored = await chat_db.get(CHAT_ID)
    assert stored.is_interested_in(post_type) is False


@pytest.mark.asyncio
async def test_pressing_a_button_twice_restores_the_original_state(
    options, context, chat
):
    post_type = PostType.NEWS
    update = make_callback_update(post_type.value)

    await options.button(update, context)
    await options.button(update, context)

    assert chat.is_interested_in(post_type) is True


@pytest.mark.asyncio
async def test_toggling_redraws_the_message(options, context, bot):
    update = make_callback_update(PostType.NEWS.value)

    await options.button(update, context)

    (edit,) = bot.edited
    assert edit["chat_id"] == CHAT_ID
    assert edit["message_id"] == 5
    assert "<b>Options</b>" in edit["text"]


@pytest.mark.asyncio
async def test_close_deletes_the_message(options, context, bot):
    update = make_callback_update(CLOSE)

    await options.button(update, context)

    assert bot.deleted == [{"chat_id": CHAT_ID, "message_id": 5}]


@pytest.mark.asyncio
async def test_a_non_admin_cannot_toggle(options, context, chat, bot):
    update = make_callback_update(PostType.NEWS.value, user_id=ADMIN_ID + 1)

    await options.button(update, context)

    assert chat.is_interested_in(PostType.NEWS) is True
    assert bot.edited == []


@pytest.mark.asyncio
async def test_an_unknown_callback_value_is_ignored(
    options, context, chat, bot, caplog
):
    update = make_callback_update("SOMETHING_OLD")

    await options.button(update, context)

    assert bot.edited == []
    assert "unknown option" in caplog.text


@pytest.mark.asyncio
async def test_a_callback_without_data_is_ignored(options, context, bot):
    update = make_callback_update(PostType.NEWS.value)
    update.callback_query.data = None

    await options.button(update, context)

    assert bot.edited == []


@pytest.mark.asyncio
async def test_a_callback_without_a_message_is_ignored(options, context, bot):
    update = make_callback_update(PostType.NEWS.value)
    update.callback_query.message = None

    await options.button(update, context)

    assert bot.edited == []


@pytest.mark.asyncio
async def test_every_callback_is_acknowledged(options, context):
    update = make_callback_update(PostType.NEWS.value)

    await options.button(update, context)

    assert len(update.callback_query.answer.calls) == 1
