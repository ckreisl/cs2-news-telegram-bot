from __future__ import annotations

from unittest.mock import patch

import pytest

from cs2posts.crawler import CounterStrike2NetCrawler


@pytest.fixture
def crawler():
    return CounterStrike2NetCrawler()


@pytest.fixture
def mock_get():
    with patch('requests.get') as mock_get:
        yield mock_get


def test_crawler_input_args_valid(crawler, mock_get):
    expected_count = 100
    mock_get.return_value.ok = True
    mock_get.return_value.text = '{"foo": "bar"}'
    crawler.crawl(count=expected_count)
    mock_get.assert_called_once_with(crawler.url % expected_count)


def test_crawler_input_args_not_valid(crawler):
    with pytest.raises(ValueError):
        crawler._validate_args(count=-1)


def test_crawler_receives_data(crawler, mock_get):
    mock_get.return_value.ok = True
    mock_get.return_value.text = '{"foo": "bar"}'
    result = crawler.crawl()
    assert result == {"foo": "bar"}


def test_crawler_raises_exception_on_timeout(crawler, mock_get):
    mock_get.side_effect = TimeoutError
    with pytest.raises(TimeoutError):
        crawler.crawl()


def test_crawler_raises_exception_on_bad_response(crawler, mock_get):
    mock_get.return_value.ok = False
    mock_get.return_value.status_code = 404
    with pytest.raises(Exception):
        crawler.crawl()
