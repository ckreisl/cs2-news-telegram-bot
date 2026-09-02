from __future__ import annotations

from pathlib import Path

import pytest

from cs2posts.exceptions import ConfigurationError
from cs2posts.settings import Settings

MINIMAL = {"TELEGRAM_TOKEN": "abc123"}


def test_a_token_is_required():
    with pytest.raises(ConfigurationError, match="TELEGRAM_TOKEN is not set"):
        Settings.from_env({})


def test_an_empty_token_is_rejected():
    with pytest.raises(ConfigurationError, match="TELEGRAM_TOKEN"):
        Settings.from_env({"TELEGRAM_TOKEN": ""})


def test_the_defaults_describe_a_runnable_bot():
    settings = Settings.from_env(MINIMAL)

    assert settings.telegram_token == "abc123"
    assert settings.crawl_interval_seconds == 900
    assert settings.chat_db_backup_count == 5
    assert settings.max_strikes == 3


def test_every_value_can_be_overridden():
    settings = Settings.from_env(
        {
            **MINIMAL,
            "CS2_UPDATE_CHECK_INTERVAL": "60",
            "CHAT_DB_BACKUP_INTERVAL": "3600",
            "CHAT_DB_BACKUP_COUNT": "2",
            "CHAT_SPAM_INTERVAL_MS": "100",
            "CHAT_BAN_TIMEOUT_SECONDS": "30",
            "CHAT_MAX_STRIKES": "5",
            "CHAT_STRIKE_RECOVERY_MINUTES": "10",
        }
    )

    assert settings.crawl_interval_seconds == 60
    assert settings.chat_db_backup_interval_seconds == 3600
    assert settings.chat_db_backup_count == 2
    assert settings.spam_interval_ms == 100
    assert settings.ban_timeout_seconds == 30
    assert settings.max_strikes == 5
    assert settings.strike_recovery_minutes == 10


def test_a_non_numeric_interval_is_reported_clearly():
    with pytest.raises(ConfigurationError, match="CS2_UPDATE_CHECK_INTERVAL"):
        Settings.from_env({**MINIMAL, "CS2_UPDATE_CHECK_INTERVAL": "soon"})


def test_an_empty_numeric_value_falls_back_to_the_default():
    settings = Settings.from_env({**MINIMAL, "CHAT_MAX_STRIKES": ""})

    assert settings.max_strikes == 3


@pytest.mark.parametrize(
    ("variable", "attribute"),
    [
        ("CHAT_DB_FILEPATH", "chat_db_filepath"),
        ("POST_DB_FILEPATH", "post_db_filepath"),
        ("CHAT_DB_BACKUP_FILEPATH", "chat_db_backup_filepath"),
        ("HEARTBEAT_FILEPATH", "heartbeat_filepath"),
        ("IMPORT_CHATS_FROM_JSON", "import_chats_from_json"),
        ("IMPORT_POSTS_FROM_JSON", "import_posts_from_json"),
    ],
)
def test_filepaths_arrive_as_paths_not_strings(variable, attribute):
    """Regression: a str here used to reach ``Path.exists()`` and crash startup."""
    settings = Settings.from_env({**MINIMAL, variable: "/tmp/somewhere.db"})

    assert getattr(settings, attribute) == Path("/tmp/somewhere.db")


@pytest.mark.parametrize(
    "attribute",
    [
        "chat_db_filepath",
        "post_db_filepath",
        "chat_db_backup_filepath",
        "import_chats_from_json",
        "import_posts_from_json",
    ],
)
def test_optional_filepaths_default_to_none(attribute):
    assert getattr(Settings.from_env(MINIMAL), attribute) is None


def test_the_heartbeat_has_a_container_default():
    assert Settings.from_env(MINIMAL).heartbeat_filepath == Path("/app/bot.heartbeat")


def test_the_max_heartbeat_age_tolerates_one_missed_cycle():
    settings = Settings.from_env({**MINIMAL, "CS2_UPDATE_CHECK_INTERVAL": "900"})

    assert settings.max_heartbeat_age_seconds == 1860


def test_settings_are_frozen():
    settings = Settings.from_env(MINIMAL)

    with pytest.raises(AttributeError):
        settings.max_strikes = 99  # type: ignore[misc]
