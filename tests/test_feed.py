from __future__ import annotations

from copy import deepcopy

import pytest

from cs2posts.dto.post import PostType
from cs2posts.feed import CS2_ANNOUNCEMENT_EPOCH
from cs2posts.feed import PostFeed


def newsitem(**overrides) -> dict:
    item = {
        "gid": "1",
        "title": "A Post",
        "url": "https://example.com/post",
        "is_external_url": True,
        "author": "Valve",
        "contents": "Contents",
        "feedlabel": "Community Announcements",
        "date": 1693524157,
        "feedname": "steam_community_announcements",
        "feed_type": 1,
        "appid": 730,
    }
    item.update(overrides)
    return item


def payload(*items: dict) -> dict:
    return {"appnews": {"appid": 730, "newsitems": list(items)}}


@pytest.fixture
def news_item():
    return newsitem(gid="news", title="Your Time is Now", date=1693524157)


@pytest.fixture
def update_item():
    return newsitem(
        gid="update",
        title="Release Notes for 8/2/2023",
        date=1691013634,
        tags=["patchnotes"],
    )


@pytest.fixture
def external_item():
    return newsitem(gid="external", title="Elsewhere", date=1700000000, feed_type=0)


@pytest.fixture
def feed(news_item, update_item, external_item):
    return PostFeed.from_api_response(payload(news_item, update_item, external_item))


def test_an_empty_payload_yields_an_empty_feed():
    for empty in (None, {}, {"appnews": None}, {"appnews": {"newsitems": None}}):
        assert PostFeed.from_api_response(empty).is_empty()


def test_a_missing_newsitems_list_yields_an_empty_feed():
    assert PostFeed.from_api_response({"appnews": {}}).is_empty()


def test_non_dict_newsitems_are_skipped(news_item):
    data = payload(news_item)
    data["appnews"]["newsitems"].append("not a dict")

    assert len(PostFeed.from_api_response(data)) == 1


def test_posts_are_ordered_newest_first(feed):
    dates = [post.date for post in feed]

    assert dates == sorted(dates, reverse=True)


def test_unsupported_feed_types_are_dropped(news_item):
    ignored = newsitem(gid="ignored", feed_type=7)

    feed = PostFeed.from_api_response(payload(news_item, ignored))

    assert [post.gid for post in feed] == ["news"]


@pytest.mark.parametrize(
    ("post_type", "expected_gid"),
    [
        (PostType.NEWS, "news"),
        (PostType.UPDATE, "update"),
        (PostType.EXTERNAL, "external"),
    ],
)
def test_of_type_selects_only_that_kind(feed, post_type, expected_gid):
    assert [post.gid for post in feed.of_type(post_type)] == [expected_gid]


def test_latest_without_a_type_is_the_newest_post(feed):
    assert feed.latest().gid == "external"


@pytest.mark.parametrize(
    ("post_type", "expected_gid"),
    [
        (PostType.NEWS, "news"),
        (PostType.UPDATE, "update"),
        (PostType.EXTERNAL, "external"),
    ],
)
def test_latest_of_a_type(feed, post_type, expected_gid):
    assert feed.latest(post_type).gid == expected_gid


def test_latest_is_none_when_the_type_is_absent(news_item):
    feed = PostFeed.from_api_response(payload(news_item))

    assert feed.latest(PostType.EXTERNAL) is None
    assert feed.latest() is not None


def test_latest_is_none_for_an_empty_feed():
    assert PostFeed.from_api_response(None).latest() is None
    assert PostFeed.from_api_response(None).latest(PostType.NEWS) is None


def test_posts_from_before_the_cs2_announcement_are_excluded(news_item):
    csgo_era = newsitem(gid="csgo", date=CS2_ANNOUNCEMENT_EPOCH - 1)

    feed = PostFeed.from_api_response(payload(news_item, csgo_era))

    assert [post.gid for post in feed.of_type(PostType.NEWS)] == ["news"]
    # ... but they are still part of the raw feed.
    assert len(feed) == 2


def test_posts_returns_a_copy(feed):
    posts = feed.posts
    posts.clear()

    assert len(feed.posts) == 3


def test_a_feed_can_be_built_from_posts_directly(make_post):
    feed = PostFeed([make_post(gid="b", date=2), make_post(gid="a", date=1)])

    assert [post.gid for post in feed] == ["b", "a"]


def test_deep_copying_a_payload_does_not_change_parsing(feed, news_item):
    assert PostFeed.from_api_response(deepcopy(payload(news_item))).latest() is not None
