from __future__ import annotations

import pytest

from cs2posts.cs2 import CounterStrikeNetPosts


@pytest.fixture
def cs2_posts():
    return CounterStrikeNetPosts(
        {
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
    )


def test_cs2_net_post_empty():
    cs2_posts = CounterStrikeNetPosts({})
    assert len(cs2_posts.posts) == 0
    assert cs2_posts.is_empty()


def test_cs2_net_post_none():
    cs2_posts = CounterStrikeNetPosts({})
    assert len(cs2_posts.posts) == 0


def test_cs2_net_post_no_events():
    cs2_posts = CounterStrikeNetPosts({})
    assert len(cs2_posts.posts) == 0


def test_cs2_net_posts(cs2_posts):
    assert len(cs2_posts.posts) == 2


def test_cs2_net_news_posts(cs2_posts):
    assert len(cs2_posts.news_posts) == 1


def test_cs2_net_update_posts(cs2_posts):
    assert len(cs2_posts.update_posts) == 1


def test_cs2_net_latest(cs2_posts):
    assert cs2_posts.latest.gid == 1


def test_cs2_net_oldest(cs2_posts):
    assert cs2_posts.oldest.gid == 2
