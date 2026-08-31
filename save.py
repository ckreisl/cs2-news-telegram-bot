"""Crawl one post and save it as JSON, for reproducing rendering bugs."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.dto.post import Post
from cs2posts.dto.post import PostType
from cs2posts.feed import PostFeed


class PostNotFound(Exception):
    pass


def find_post_on(posts: list[Post], date: datetime) -> Post:
    for post in posts:
        if post.date_as_datetime.date() == date.date():
            return post
    raise PostNotFound(f"No post found for {date.date()}")


def main(args: argparse.Namespace) -> int:
    payload = asyncio.run(CounterStrike2Crawler().crawl(count=args.count))
    feed = PostFeed.from_api_response(payload)

    post_type = PostType(args.type)
    post = find_post_on(feed.of_type(post_type), args.date)

    args.save_dir.mkdir(parents=True, exist_ok=True)
    filepath = args.save_dir / f"{post_type}_{args.date.date()}.json"
    filepath.write_text(json.dumps(post.to_dict(), indent=4), encoding="utf-8")
    print(f"Saved {filepath}")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "type",
        choices=[post_type.value for post_type in PostType],
        help="Type of post to crawl",
    )
    parser.add_argument(
        "--date",
        help="Date of the post to crawl (ISO format)",
        type=datetime.fromisoformat,
        required=True,
    )
    parser.add_argument(
        "--count", help="Number of posts to crawl", type=int, default=100
    )
    parser.add_argument(
        "--save-dir",
        help="Save directory for the JSON files",
        default=Path(__file__).parent / "tests" / "data",
        type=Path,
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
