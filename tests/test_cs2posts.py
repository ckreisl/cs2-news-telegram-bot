from __future__ import annotations

from copy import deepcopy
from unittest.mock import patch

import pytest

from cs2posts.cs2posts import CounterStrike2Posts


@pytest.fixture
def crawler_data():
    return {
        "appnews": {
            "appid": 730,
            "newsitems": [
                {
                    "gid": "5141476355659151610",
                    "title": "Your Time is Now",
                    "url": "https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355659151610",
                    "is_external_url": True,
                    "author": "Piggles ULTRAPRO",
                    "contents": "Content News",
                    "feedlabel": "Community Announcements",
                    "date": 1693524157,
                    "feedname": "steam_community_announcements",
                    "feed_type": 1,
                    "appid": 730
                },
                {
                    "gid": "5124585319846885283",
                    "title": "Release Notes for 8/2/2023",
                    "url": "https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5124585319846885283",
                    "is_external_url": True,
                    "author": "jo",
                    "contents": "Content Update",
                    "feedlabel": "Community Announcements",
                    "date": 1691013634,
                    "feedname": "steam_community_announcements",
                    "feed_type": 1,
                    "appid": 730,
                    "tags": [
                        "patchnotes"
                    ]
                }
            ]
        }
    }


@pytest.fixture
def crawler_data_with_external(crawler_data):
    data = deepcopy(crawler_data)
    data["appnews"]["newsitems"].append(
        {
            "gid": "6000000000000000000",
            "title": "External Feature",
            "url": "https://example.com/external-feature",
            "is_external_url": True,
            "author": "Someone Else",
            "contents": "External Content",
            "feedlabel": "Community Announcements",
            "date": 1694000000,
            "feedname": "steam_community_announcements",
            "feed_type": 0,
            "appid": 730,
        }
    )
    return data


@pytest.fixture
def crawler_data_with_unknown_feed_type(crawler_data):
    data = deepcopy(crawler_data)
    data["appnews"]["newsitems"].append(
        {
            "gid": "7000000000000000000",
            "title": "Ignore Me",
            "url": "https://example.com/ignore-me",
            "is_external_url": True,
            "author": "Ignored",
            "contents": "Ignored",
            "feedlabel": "Community Announcements",
            "date": 1695000000,
            "feedname": "steam_community_announcements",
            "feed_type": 999,
            "appid": 730,
        }
    )
    return data


@pytest.fixture
def crawler_data_steam_clan_image():
    return {
        "appnews": {
            "appid": 730,
            "newsitems": [
                {
                    "gid": "5141476355659151610",
                    "title": "Your Time is Now",
                    "url": "https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355659151610",
                    "is_external_url": True,
                    "author": "Piggles ULTRAPRO",
                    "contents": "{STEAM_CLAN_IMAGE}",
                    "feedlabel": "Community Announcements",
                    "date": 1693524157,
                    "feedname": "steam_community_announcements",
                    "feed_type": 1,
                    "appid": 730
                }
            ]
        }
    }


@pytest.fixture
def cs2_posts(crawler_data):
    return CounterStrike2Posts(crawler_data)


@pytest.fixture
def cs2_posts_steam_clan_image(crawler_data_steam_clan_image):
    return CounterStrike2Posts(crawler_data_steam_clan_image)


@pytest.fixture
def cs2_posts_with_external(crawler_data_with_external):
    return CounterStrike2Posts(crawler_data_with_external)


@pytest.fixture
def cs2_posts_with_unknown_feed_type(crawler_data_with_unknown_feed_type):
    return CounterStrike2Posts(crawler_data_with_unknown_feed_type)


def test_cs2_validate_replace_steam_clan_image_url(cs2_posts_steam_clan_image):
    with patch("cs2posts.utils.Utils.is_valid_url", return_value=True):
        cs2_posts_steam_clan_image.validate()
    expected = "https://clan.akamai.steamstatic.com/images"
    assert cs2_posts_steam_clan_image.posts[0].contents == expected


def test_cs2_net_post_empty():
    cs2_posts = CounterStrike2Posts({})
    assert len(cs2_posts.posts) == 0
    assert cs2_posts.is_empty()


def test_cs2_net_post_none():
    cs2_posts = CounterStrike2Posts(None)
    assert len(cs2_posts.posts) == 0


@pytest.mark.parametrize("payload", [
    {"not_appnews": "not_appnews"},
    {"appnews": {}},
])
def test_cs2_net_post_missing_expected_keys(payload):
    cs2_posts = CounterStrike2Posts(payload)
    assert len(cs2_posts.posts) == 0


def test_cs2_net_posts(cs2_posts):
    assert len(cs2_posts) == 2


def test_cs2_net_news_posts(cs2_posts):
    assert len(cs2_posts.news_posts) == 1


def test_cs2_net_update_posts(cs2_posts):
    assert len(cs2_posts.update_posts) == 1


def test_cs2_net_external_posts(cs2_posts_with_external):
    assert len(cs2_posts_with_external.external_posts) == 1
    assert cs2_posts_with_external.latest_external_post.gid == "6000000000000000000"
    assert cs2_posts_with_external.oldest_external_post.gid == "6000000000000000000"


def test_cs2_net_is_latest_post_external(cs2_posts_with_external):
    assert cs2_posts_with_external.is_latest_post_external()

    cs2_posts = CounterStrike2Posts(None)
    assert not cs2_posts.is_latest_post_external()


def test_cs2_net_ignores_unknown_feed_type(cs2_posts_with_unknown_feed_type):
    assert len(cs2_posts_with_unknown_feed_type.posts) == 2
    assert all(post.gid != "7000000000000000000" for post in cs2_posts_with_unknown_feed_type.posts)


def test_cs2_net_latest(cs2_posts):
    assert cs2_posts.latest.gid == "5141476355659151610"
    assert cs2_posts.latest_news_post.gid == "5141476355659151610"
    assert cs2_posts.latest_update_post.gid == "5124585319846885283"


def test_cs2_net_oldest(cs2_posts):
    assert cs2_posts.oldest.gid == "5124585319846885283"

    cs2_posts = CounterStrike2Posts(None)
    assert cs2_posts.oldest is None


def test_cs2_net_oldest_news(cs2_posts):
    assert cs2_posts.oldest_news_post.gid == "5141476355659151610"

    cs2_posts = CounterStrike2Posts(None)
    assert cs2_posts.oldest_news_post is None


def test_cs2_net_oldest_update(cs2_posts):
    assert cs2_posts.oldest_update_post.gid == "5124585319846885283"

    cs2_posts = CounterStrike2Posts(None)
    assert cs2_posts.oldest_update_post is None


def test_cs2_net_is_latest_post_news(cs2_posts):
    assert cs2_posts.is_latest_post_news()

    cs2_posts = CounterStrike2Posts(None)
    assert not cs2_posts.is_latest_post_news()


def test_cs2_net_is_latest_post_update(cs2_posts):
    assert cs2_posts.is_latest_post_update() is False

    cs2_posts = CounterStrike2Posts(None)
    assert not cs2_posts.is_latest_post_update()


def test_cs2_net_posts_json(cs2_posts):
    assert cs2_posts.posts_json == [
        {
            'gid': '5141476355659151610',
            'title': 'Your Time is Now',
            'url': 'https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355659151610',
            'is_external_url': True,
            'author': 'Piggles ULTRAPRO',
            'contents': 'Content News',
            'feedlabel': 'Community Announcements',
            'date': 1693524157,
            'feedname': 'steam_community_announcements',
            'feed_type': 1,
            'appid': 730,
            'tags': []
        },
        {
            'gid': '5124585319846885283',
            'title': 'Release Notes for 8/2/2023',
            'url': 'https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5124585319846885283',
            'is_external_url': True,
            'author': 'jo',
            'contents': 'Content Update',
            'feedlabel': 'Community Announcements',
            'date': 1691013634,
            'feedname': 'steam_community_announcements',
            'feed_type': 1,
            'appid': 730,
            'tags': ['patchnotes']
        }
    ]
