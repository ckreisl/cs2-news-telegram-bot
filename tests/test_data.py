from __future__ import annotations

import json
from pathlib import Path

import pytest
from telegram import Video

from cs2posts.content.content import Content
from cs2posts.content.content import Image
from cs2posts.content.content import TextBlock
from cs2posts.dto.post import Post
from cs2posts.msg import TelegramMessageFactory


def load_data(type: str, date: str) -> Post:
    with open(f"{Path(__file__).parent}/data/{type}_{date}.json") as fs:
        data = json.load(fs)
    return Post.from_dict(data)


def content_count(content: list[Content]) -> dict[str, int]:
    counts = {}
    for c in content:
        if c.__class__.__name__ not in counts:
            counts[c.__class__.__name__] = 0
        counts[c.__class__.__name__] += 1
    return counts


@pytest.mark.asyncio
async def test_news_2024_05_23():
    post = load_data("news", "2024-05-23")
    msg = await TelegramMessageFactory.create(post)
    assert len(msg.content) == 5

    expected_text_blocks = 3
    expected_image_blocks = 1
    expected_video_blocks = 1

    actual_values = content_count(msg.content)

    assert actual_values[TextBlock.__name__] == expected_text_blocks
    assert actual_values[Image.__name__] == expected_image_blocks
    assert actual_values[Video.__name__] == expected_video_blocks


@pytest.mark.asyncio
async def test_news_2024_10_02():
    post = load_data("news", "2024-10-02")
    msg = await TelegramMessageFactory.create(post)
    assert len(msg.content) == 3

    expected_text_blocks = 2
    expected_image_blocks = 1

    actual_values = content_count(msg.content)

    assert msg.content[0].text.endswith("</a>")
    assert not msg.content[-1].text.startswith("</a>")
    assert actual_values[TextBlock.__name__] == expected_text_blocks
    assert actual_values[Image.__name__] == expected_image_blocks


@pytest.mark.asyncio
async def test_news_2024_11_13():
    post = load_data("news", "2024-11-13")
    msg = await TelegramMessageFactory.create(post)
    assert len(msg.content) == 5

    expected_text_blocks = 3
    expected_image_blocks = 1
    expected_video_blocks = 1

    actual_values = content_count(msg.content)

    assert actual_values[TextBlock.__name__] == expected_text_blocks
    assert actual_values[Image.__name__] == expected_image_blocks
    assert actual_values[Video.__name__] == expected_video_blocks
