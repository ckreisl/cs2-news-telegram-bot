from __future__ import annotations

import os
import time

import pytest

from cs2posts import healthcheck
from cs2posts.bot.heartbeat import write_heartbeat
from cs2posts.exceptions import ConfigurationError
from cs2posts.settings import Settings


def test_write_heartbeat_creates_file_with_timestamp(tmp_path):
    filepath = tmp_path / "beat"

    before = time.time()
    write_heartbeat(filepath)
    after = time.time()

    assert filepath.exists()
    assert before <= float(filepath.read_text()) <= after


def test_write_heartbeat_creates_missing_parent_dirs(tmp_path):
    filepath = tmp_path / "nested" / "dir" / "beat"

    write_heartbeat(filepath)

    assert filepath.exists()


def test_write_heartbeat_refreshes_existing_file(tmp_path):
    filepath = tmp_path / "beat"
    write_heartbeat(filepath)
    first = float(filepath.read_text())

    time.sleep(0.01)
    write_heartbeat(filepath)

    assert float(filepath.read_text()) > first


def test_write_heartbeat_swallows_oserror(tmp_path, caplog):
    # A file standing in for the parent directory makes mkdir/write fail.
    not_a_dir = tmp_path / "file"
    not_a_dir.touch()

    # Must not raise: a heartbeat failure may never take down the bot.
    write_heartbeat(not_a_dir / "beat")

    assert "Could not write heartbeat" in caplog.text


@pytest.fixture
def heartbeat_settings(tmp_path, settings):
    from dataclasses import replace

    return replace(
        settings, heartbeat_filepath=tmp_path / "beat", crawl_interval_seconds=900
    )


def test_healthcheck_fails_when_file_missing(heartbeat_settings, caplog):
    assert healthcheck.check(heartbeat_settings) == 1
    assert "missing" in caplog.text


def test_healthcheck_passes_when_fresh(heartbeat_settings):
    write_heartbeat(heartbeat_settings.heartbeat_filepath)

    assert healthcheck.check(heartbeat_settings) == 0


def test_healthcheck_tolerates_one_missed_cycle(heartbeat_settings):
    # max age is 2 * 900 + 60 = 1860s
    path = heartbeat_settings.heartbeat_filepath
    write_heartbeat(path)
    stale = time.time() - 1800
    os.utime(path, (stale, stale))

    assert healthcheck.check(heartbeat_settings) == 0


def test_healthcheck_fails_when_stale(heartbeat_settings, caplog):
    path = heartbeat_settings.heartbeat_filepath
    write_heartbeat(path)
    stale = time.time() - 3600
    os.utime(path, (stale, stale))

    assert healthcheck.check(heartbeat_settings) == 1
    assert "stale" in caplog.text


def test_healthcheck_reports_a_missing_token_instead_of_raising(monkeypatch, caplog):
    def unconfigured(*args, **kwargs):
        raise ConfigurationError("TELEGRAM_TOKEN is not set")

    monkeypatch.setattr(Settings, "from_env", unconfigured)

    assert healthcheck.main() == 1
    assert "misconfigured" in caplog.text
