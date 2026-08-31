from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from cs2posts.exceptions import ConfigurationError

Env = Mapping[str, str]


def _require(env: Env, key: str) -> str:
    value = env.get(key)
    if not value:
        raise ConfigurationError(f"{key} is not set")
    return value


def _int(env: Env, key: str, default: int) -> int:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be an integer, got {raw!r}") from exc


def _path(env: Env, key: str) -> Path | None:
    raw = env.get(key)
    return Path(raw) if raw else None


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated runtime configuration.

    Built once at the composition root rather than read as module-level
    globals, so that a malformed value fails at an explicit call with a
    clear message, and tests can construct configurations directly.
    """

    telegram_token: str
    crawl_interval_seconds: int = 900
    # Liveness heartbeat consumed by the container HEALTHCHECK. The bot
    # refreshes this file once per crawl cycle; the healthcheck fails it if
    # the file goes stale.
    heartbeat_filepath: Path = Path("/app/bot.heartbeat")
    # Database filepaths (default: database/sqlite.db for both when None).
    chat_db_filepath: Path | None = None
    post_db_filepath: Path | None = None
    # Backup filepath (default: backups/backup.db when None).
    chat_db_backup_filepath: Path | None = None
    chat_db_backup_interval_seconds: int = 86400
    chat_db_backup_count: int = 5
    spam_interval_ms: int = 750
    ban_timeout_seconds: int = 600
    max_strikes: int = 3
    strike_recovery_minutes: int = 60
    # On startup, import chats and posts from a JSON file (legacy behaviour).
    import_chats_from_json: Path | None = None
    import_posts_from_json: Path | None = None

    @classmethod
    def from_env(cls, env: Env | None = None) -> Settings:
        if env is None:
            load_dotenv()
            env = os.environ

        heartbeat = _path(env, "HEARTBEAT_FILEPATH")

        return cls(
            telegram_token=_require(env, "TELEGRAM_TOKEN"),
            crawl_interval_seconds=_int(env, "CS2_UPDATE_CHECK_INTERVAL", 900),
            heartbeat_filepath=heartbeat or Path("/app/bot.heartbeat"),
            chat_db_filepath=_path(env, "CHAT_DB_FILEPATH"),
            post_db_filepath=_path(env, "POST_DB_FILEPATH"),
            chat_db_backup_filepath=_path(env, "CHAT_DB_BACKUP_FILEPATH"),
            chat_db_backup_interval_seconds=_int(env, "CHAT_DB_BACKUP_INTERVAL", 86400),
            chat_db_backup_count=_int(env, "CHAT_DB_BACKUP_COUNT", 5),
            spam_interval_ms=_int(env, "CHAT_SPAM_INTERVAL_MS", 750),
            ban_timeout_seconds=_int(env, "CHAT_BAN_TIMEOUT_SECONDS", 600),
            max_strikes=_int(env, "CHAT_MAX_STRIKES", 3),
            strike_recovery_minutes=_int(env, "CHAT_STRIKE_RECOVERY_MINUTES", 60),
            import_chats_from_json=_path(env, "IMPORT_CHATS_FROM_JSON"),
            import_posts_from_json=_path(env, "IMPORT_POSTS_FROM_JSON"),
        )

    @property
    def max_heartbeat_age_seconds(self) -> int:
        """Tolerate one fully missed crawl cycle before declaring the bot dead."""
        return self.crawl_interval_seconds * 2 + 60
