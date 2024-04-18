from __future__ import annotations

import pytest

from cs2posts.cs2 import CounterStrike2Posts


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
                    "contents": "Today we\u2019re updating the CS2 Limited Test with a new map (Inferno!) and the all new CS Rating. \n\nYour CS Rating is a visible measurement of your Counter-Strike performance, and it will determine where you stand on global and regional leaderboards. To get your CS Rating, play matches in the updated Premier mode (our Active Duty Pick-Ban competitive mode) either on your own or with your friends.\n\n[previewyoutube=s6BNHro0vSg;full][/previewyoutube]\n\nAdditionally, today we\u2019re starting the process of inviting as many eligible players as possible to the Limited Test. To be eligible for a CS2 Limited Test invite players must have CS:GO Prime status, an active official competitive matchmaking Skill Group, and play majority of their official matchmaking games in one of the regions where the Limited Test is available.\n\n[h3]Saving Time[/h3]\nOver the past decade, we\u2019ve shipped updates to the economy and weapon balance to trim the fat and reduce the number of uncontested rounds in a match of CS.\n\nBecause of these changes, exciting competitive matches can be resolved with fewer rounds. And shorter matches mean players can play more, and more often. So with CS2, we\u2019re moving to a maximum of 24 rounds in regulation time (with a 6 round overtime in case of a tie) for Premier, Competitive, and the Majors.\n\nWe expect the structure and flow of matches to evolve over time as the community adapts. And we\u2019re excited to see where they go next.\n",
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
                    "contents": "[ GAMEPLAY ]\n[list]\n[*] Disabled Wingman\n[/list]\n[ MAPS ]\n[list]\n[*] Added Anubis to Deathmatch, Casual, and Competitive game modes\n[*] Added Ancient to Deathmatch and Casual game modes\n[*] Removed Overpass and Vertigo\n[/list]\n[ MISC ]\n[list]\n[*] Taught chickens how to swim\n[*] Weapons splash when dropped in water\n[*] Adjusted grenade/water interaction sounds\n[/list]\n[ ANIMATION ]\n[list]\n[*] Improved head animation when crouching while running\n[*] Improved foot animation when quickly alternating between standing still and moving\n[/list]",
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
def cs2_posts(crawler_data):
    return CounterStrike2Posts(crawler_data)


def test_cs2_net_post_empty():
    cs2_posts = CounterStrike2Posts({})
    assert len(cs2_posts.posts) == 0
    assert cs2_posts.is_empty()


def test_cs2_net_post_none():
    cs2_posts = CounterStrike2Posts({})
    assert len(cs2_posts.posts) == 0


def test_cs2_net_post_no_events():
    cs2_posts = CounterStrike2Posts({'not_events': 'not_events'})
    assert len(cs2_posts.posts) == 0


def test_cs2_net_post_unknown_event_type():
    cs2_posts = CounterStrike2Posts(
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


@pytest.mark.skip(reason="Not implemented yet")
def test_cs2_net_posts_json(cs2_posts):
    assert cs2_posts.posts_json == [
        {
            "gid": "5141476355659151610",
            "title": "Your Time is Now",
            "url": "https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355659151610",
            "is_external_url": True,
            "author": "Piggles ULTRAPRO",
            "contents": "Today we\u2019re updating the CS2 Limited Test with a new map (Inferno!) and the all new CS Rating. \n\nYour CS Rating is a visible measurement of your Counter-Strike performance, and it will determine where you stand on global and regional leaderboards. To get your CS Rating, play matches in the updated Premier mode (our Active Duty Pick-Ban competitive mode) either on your own or with your friends.\n\n[previewyoutube=s6BNHro0vSg;full][/previewyoutube]\n\nAdditionally, today we\u2019re starting the process of inviting as many eligible players as possible to the Limited Test. To be eligible for a CS2 Limited Test invite players must have CS:GO Prime status, an active official competitive matchmaking Skill Group, and play majority of their official matchmaking games in one of the regions where the Limited Test is available.\n\n[h3]Saving Time[/h3]\nOver the past decade, we\u2019ve shipped updates to the economy and weapon balance to trim the fat and reduce the number of uncontested rounds in a match of CS.\n\nBecause of these changes, exciting competitive matches can be resolved with fewer rounds. And shorter matches mean players can play more, and more often. So with CS2, we\u2019re moving to a maximum of 24 rounds in regulation time (with a 6 round overtime in case of a tie) for Premier, Competitive, and the Majors.\n\nWe expect the structure and flow of matches to evolve over time as the community adapts. And we\u2019re excited to see where they go next.\n",
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
            "contents": "[ GAMEPLAY ]\n[list]\n[*] Disabled Wingman\n[/list]\n[ MAPS ]\n[list]\n[*] Added Anubis to Deathmatch, Casual, and Competitive game modes\n[*] Added Ancient to Deathmatch and Casual game modes\n[*] Removed Overpass and Vertigo\n[/list]\n[ MISC ]\n[list]\n[*] Taught chickens how to swim\n[*] Weapons splash when dropped in water\n[*] Adjusted grenade/water interaction sounds\n[/list]\n[ ANIMATION ]\n[list]\n[*] Improved head animation when crouching while running\n[*] Improved foot animation when quickly alternating between standing still and moving\n[/list]",
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
