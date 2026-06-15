from __future__ import annotations

import os
import time

import pytest

from cs2posts import healthcheck
from cs2posts.bot import settings
from cs2posts.bot.heartbeat import write_heartbeat


def test_write_heartbeat_creates_file_with_timestamp(tmp_path):
    filepath = tmp_path / 'beat'

    before = time.time()
    write_heartbeat(str(filepath))
    after = time.time()

    assert filepath.exists()
    assert before <= float(filepath.read_text()) <= after


def test_write_heartbeat_creates_missing_parent_dirs(tmp_path):
    filepath = tmp_path / 'nested' / 'dir' / 'beat'

    write_heartbeat(str(filepath))

    assert filepath.exists()


def test_write_heartbeat_refreshes_existing_file(tmp_path):
    filepath = tmp_path / 'beat'
    write_heartbeat(str(filepath))
    first = float(filepath.read_text())

    time.sleep(0.01)
    write_heartbeat(str(filepath))
    second = float(filepath.read_text())

    assert second > first


def test_write_heartbeat_swallows_oserror(tmp_path, caplog):
    # A file standing in for the parent directory makes mkdir/write fail.
    not_a_dir = tmp_path / 'file'
    not_a_dir.touch()

    # Must not raise: a heartbeat failure may never take down the bot.
    write_heartbeat(str(not_a_dir / 'beat'))

    assert 'Could not write heartbeat' in caplog.text


@pytest.fixture
def heartbeat_settings(tmp_path, monkeypatch):
    filepath = tmp_path / 'beat'
    monkeypatch.setattr(settings, 'HEARTBEAT_FILEPATH', str(filepath))
    monkeypatch.setattr(settings, 'CS2_UPDATE_CHECK_INTERVAL', 900)
    return filepath


def test_healthcheck_fails_when_file_missing(heartbeat_settings, caplog):
    assert healthcheck.main() == 1
    assert 'missing' in caplog.text


def test_healthcheck_passes_when_fresh(heartbeat_settings):
    write_heartbeat(str(heartbeat_settings))

    assert healthcheck.main() == 0


def test_healthcheck_passes_at_threshold_boundary(heartbeat_settings):
    # Within max_age (2 * 900 + 60 = 1860s): one missed cycle is tolerated.
    write_heartbeat(str(heartbeat_settings))
    stale = time.time() - 1800
    os.utime(heartbeat_settings, (stale, stale))

    assert healthcheck.main() == 0


def test_healthcheck_fails_when_stale(heartbeat_settings, caplog):
    write_heartbeat(str(heartbeat_settings))
    stale = time.time() - 3600
    os.utime(heartbeat_settings, (stale, stale))

    assert healthcheck.main() == 1
    assert 'stale' in caplog.text
