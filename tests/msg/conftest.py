from __future__ import annotations

import pytest

from cs2posts.dto.post import Post


@pytest.fixture
def mocked_cs2_update_post() -> Post:
    return Post(gid="1337",
                title="Release Notes for 2/13/2009",
                url="https://test.com",
                is_external_url=True,
                author="Valve",
                contents="my content",
                date=1234567890,
                feedlabel="feedlabel",
                feedname="feedname",
                feed_type=1,
                appid=730,
                tags=["patchnotes"])


@pytest.fixture
def mocked_cs2_news_post() -> Post:
    return Post(
        gid="1338",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1338",
        author="Valve",
        contents="[img]https://example.com/image.jpg[/img]\nThis is a test message.",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=1,
        appid=730)


@pytest.fixture
def mocked_cs2_external_news() -> Post:
    return Post(
        gid="1339",
        title="Some News",
        is_external_url=True,
        url="https://www.counter-strike.net/newsentry/1339",
        author="",
        contents="<a href='https://example.com'>Link</a> External News",
        date=1234567890,
        feedlabel="feedlabel",
        feedname="feedname",
        feed_type=0,
        appid=730)
