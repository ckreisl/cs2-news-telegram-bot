from __future__ import annotations

import pytest

from cs2posts.post import EventType
from cs2posts.post import Post


@pytest.fixture
def post_fixture():
    return Post(gid="1",
                posterid="2",
                headline="Test",
                posttime=1234567890,
                updatetime=9876543210,
                body="Test body",
                event_type=12)


@pytest.fixture
def post_fixture2():
    return Post(gid="2",
                posterid="2",
                headline="Test2",
                posttime=1234567890,
                updatetime=9876543210,
                body="Test body2",
                event_type=13)


def test_event_types():
    assert EventType(12) == EventType.UPDATE
    assert EventType(13) == EventType.NEWS
    assert EventType(14) == EventType.SPECIAL
    assert EventType(28) == EventType.EVENTS
    assert EventType(-1) == EventType.NOT_DEFINED
    assert EventType(0) == EventType.NOT_DEFINED
    assert EventType(100) == EventType.NOT_DEFINED


def test_post_is_update(post_fixture):
    post_fixture.event_type = EventType.UPDATE.value
    assert post_fixture.is_update()


def test_post_is_news(post_fixture):
    post_fixture.event_type = EventType.NEWS.value
    assert post_fixture.is_news()
    post_fixture.event_type = EventType.SPECIAL.value
    assert post_fixture.is_news()
    post_fixture.event_type = EventType.EVENTS.value
    assert post_fixture.is_news()


def test_post_to_dict(post_fixture):
    expected = {"gid": post_fixture.gid,
                "posterid": post_fixture.posterid,
                "headline": post_fixture.headline,
                "posttime": post_fixture.posttime,
                "updatetime": post_fixture.updatetime,
                "body": post_fixture.body,
                "event_type": post_fixture.event_type}
    assert post_fixture.to_dict() == expected


def test_post_get_item(post_fixture):
    assert post_fixture["gid"] == post_fixture.gid
    assert post_fixture["posterid"] == post_fixture.posterid
    assert post_fixture["headline"] == post_fixture.headline
    assert post_fixture["posttime"] == post_fixture.posttime
    assert post_fixture["updatetime"] == post_fixture.updatetime
    assert post_fixture["body"] == post_fixture.body
    assert post_fixture["event_type"] == post_fixture.event_type


def test_post_equals(post_fixture):
    assert post_fixture == post_fixture
    assert post_fixture != {}


def test_post_not_equals(post_fixture, post_fixture2):
    assert post_fixture != post_fixture2


def test_post_is_newer_than(post_fixture, post_fixture2):
    assert not post_fixture.is_newer_than(None)
    assert not post_fixture.is_newer_than(post_fixture2)
    post_fixture2.posttime = 123456789
    assert post_fixture.is_newer_than(post_fixture2)
