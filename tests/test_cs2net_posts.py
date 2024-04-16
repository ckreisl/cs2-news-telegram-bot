from __future__ import annotations

import pytest

from cs2posts.cs2 import CounterStrikeNetPosts


@pytest.fixture
def crawler_data():
    return {
        "events": [
            {
                "event_type": 13,
                "gid": 1,
                "announcement_body": {
                    "posterid": 1,
                    "headline": "headline",
                    "posttime": 1679503829,
                    "updatetime": 1,
                    "body": "body"
                }
            },
            {
                "event_type": 12,
                "gid": 2,
                "announcement_body": {
                    "posterid": 2,
                    "headline": "headline",
                    "posttime": 1679503830,
                    "updatetime": 2,
                    "body": "body"
                }
            }
        ]
    }


@pytest.fixture
def cs2_posts(crawler_data):
    return CounterStrikeNetPosts(crawler_data)


def test_cs2_net_post_empty():
    cs2_posts = CounterStrikeNetPosts({})
    assert len(cs2_posts.posts) == 0
    assert cs2_posts.is_empty()


def test_cs2_net_post_none():
    cs2_posts = CounterStrikeNetPosts({})
    assert len(cs2_posts.posts) == 0


def test_cs2_net_post_no_events():
    cs2_posts = CounterStrikeNetPosts({'not_events': 'not_events'})
    assert len(cs2_posts.posts) == 0


def test_cs2_net_post_unknown_event_type():
    cs2_posts = CounterStrikeNetPosts(
        {'events': [
            {
                'event_type': 999,
                'gid': 1,
                'announcement_body': {
                    'headline': 'headline',
                }
            }
        ]})
    assert len(cs2_posts.posts) == 0


def test_cs2_net_posts(cs2_posts):
    assert len(cs2_posts) == 2


def test_cs2_net_news_posts(cs2_posts):
    assert len(cs2_posts.news_posts) == 1


def test_cs2_net_update_posts(cs2_posts):
    assert len(cs2_posts.update_posts) == 1


def test_cs2_net_latest(cs2_posts):
    assert cs2_posts.latest.gid == 1
    assert cs2_posts.latest_news_post.gid == 1
    assert cs2_posts.latest_update_post.gid == 2


def test_cs2_net_oldest(cs2_posts):
    assert cs2_posts.oldest.gid == 2

    cs2_posts = CounterStrikeNetPosts(None)
    assert cs2_posts.oldest is None


def test_cs2_net_oldest_news(cs2_posts):
    assert cs2_posts.oldest_news_post.gid == 1

    cs2_posts = CounterStrikeNetPosts(None)
    assert cs2_posts.oldest_news_post is None


def test_cs2_net_oldest_update(cs2_posts):
    assert cs2_posts.oldest_update_post.gid == 2

    cs2_posts = CounterStrikeNetPosts(None)
    assert cs2_posts.oldest_update_post is None


def test_cs2_net_is_latest_post_news(cs2_posts):
    assert cs2_posts.is_latest_post_news()

    cs2_posts = CounterStrikeNetPosts(None)
    assert not cs2_posts.is_latest_post_news()


def test_cs2_net_is_latest_post_update(cs2_posts):
    assert cs2_posts.is_latest_post_update() is False

    cs2_posts = CounterStrikeNetPosts(None)
    assert not cs2_posts.is_latest_post_update()


def test_cs2_net_posts_json(cs2_posts):
    assert cs2_posts.posts_json == [
        {
            'gid': 1,
            'posterid': 1,
            'headline': 'headline',
            'posttime': 1679503829,
            'updatetime': 1,
            'body': 'body',
            'event_type': 13
        },
        {
            'gid': 2,
            'posterid': 2,
            'headline': 'headline',
            'posttime': 1679503830,
            'updatetime': 2,
            'body': 'body',
            'event_type': 12
        }
    ]
