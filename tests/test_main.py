from __future__ import annotations

from pathlib import Path

import httpx
import pytest

import main
from cs2posts.bot.cs2 import CounterStrike2UpdateBot
from cs2posts.exceptions import ConfigurationError
from cs2posts.settings import Settings


@pytest.fixture
def steam_api(monkeypatch):
    """Answer the seeding crawl without leaving the process."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"appnews": {"newsitems": []}})
    )
    real = main.CounterStrike2Crawler
    monkeypatch.setattr(
        main,
        "CounterStrike2Crawler",
        lambda: real(client_factory=lambda: httpx.AsyncClient(transport=transport)),
    )


@pytest.fixture
def stub_application(monkeypatch):
    """Keep the composition root from opening a Telegram connection."""
    from unittest.mock import Mock

    built = Mock()

    def builder():
        chained = Mock()
        for method in ("post_init", "post_shutdown", "token", "request"):
            getattr(chained, method).return_value = chained
        chained.build.return_value = built
        return chained

    monkeypatch.setattr("cs2posts.bot.cs2.Application.builder", builder)
    return built


def test_the_composition_root_wires_a_usable_bot(stub_application, tmp_path):
    """Regression: string filepaths from the environment used to reach
    ``Path.exists()`` and crash the bot during ``async_init``."""
    settings = Settings.from_env(
        {
            "TELEGRAM_TOKEN": "abc123",
            "POST_DB_FILEPATH": str(tmp_path / "posts.db"),
            "CHAT_DB_FILEPATH": str(tmp_path / "chats.db"),
        }
    )

    bot = main.create_bot(settings)

    assert isinstance(bot, CounterStrike2UpdateBot)
    assert isinstance(bot.post_db.filepath, Path)
    assert isinstance(bot.chat_db.filepath, Path)
    assert bot.post_db.filepath == tmp_path / "posts.db"


@pytest.mark.asyncio
async def test_a_bot_built_from_env_paths_can_initialise(
    stub_application, steam_api, tmp_path
):
    settings = Settings.from_env(
        {
            "TELEGRAM_TOKEN": "abc123",
            "POST_DB_FILEPATH": str(tmp_path / "posts.db"),
            "CHAT_DB_FILEPATH": str(tmp_path / "chats.db"),
        }
    )
    bot = main.create_bot(settings)

    await bot.async_init()

    assert (tmp_path / "posts.db").exists()
    assert (tmp_path / "chats.db").exists()


def test_main_reports_a_missing_token_instead_of_crashing(monkeypatch, caplog):
    def unconfigured(*args, **kwargs):
        raise ConfigurationError("TELEGRAM_TOKEN is not set")

    monkeypatch.setattr(Settings, "from_env", unconfigured)

    assert main.main() == 1
    assert "Cannot start" in caplog.text


def test_main_leaves_the_ambient_event_loop_intact(
    monkeypatch, stub_application, tmp_path
):
    """Regression: ``asyncio.run`` before ``run_polling`` closed the loop and
    unset it, so python-telegram-bot raised "There is no current event loop".
    Async startup belongs in the post_init hook, inside the loop run_polling
    owns."""
    import asyncio

    monkeypatch.setenv("TELEGRAM_TOKEN", "abc123")
    monkeypatch.setenv("HEARTBEAT_FILEPATH", str(tmp_path / "beat"))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    seen = []

    def record_run_polling(**kwargs):
        # run_polling reaches for the ambient loop; it must still be there.
        seen.append(asyncio.get_event_loop())

    stub_application.run_polling = record_run_polling

    try:
        assert main.main() == 0
        assert seen == [loop]
        assert not loop.is_closed()
    finally:
        asyncio.set_event_loop(None)
        loop.close()
