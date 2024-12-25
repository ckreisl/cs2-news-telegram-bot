from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

from cs2posts.crawler import CounterStrike2Crawler
from cs2posts.cs2posts import CounterStrike2Posts
from cs2posts.dto.post import Post


class PostNotFound(Exception):
    pass


def get_post(posts: list[Post], date: datetime) -> Post:
    for post in posts:
        if post.date_as_datetime.date() == date.date():
            return post
    raise PostNotFound(f"Post not found for {date=}")


def main(args) -> int:
    crawler = CounterStrike2Crawler()
    data = asyncio.run(crawler.crawl(count=args.count))
    posts = CounterStrike2Posts(data)

    if args.type == "news":
        post = get_post(posts.news_posts, args.date)
    elif args.type == "external":
        post = get_post(posts.external_posts, args.date)
    elif args.type == "update":
        post = get_post(posts.update_posts, args.date)
    else:
        raise ValueError(f"Unknown post type {args.type=}")

    with open(args.save_dir / f"{args.type}_{args.date.date()}.json", "w") as fs:
        json.dump(post.to_dict(), fs, indent=4)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Utils helping debugging by crawling and saving buggy posts")
    parser.add_argument("type",
                        choices=["news", "external", "update"],
                        help="Type of post to crawl")
    parser.add_argument("--date",
                        help="Date of the post to crawl",
                        type=datetime.fromisoformat,
                        required=True)
    parser.add_argument("--count",
                        help="Number of posts to crawl",
                        type=int,
                        default=100)
    parser.add_argument("--save-dir",
                        help="Save directory for the JSON files",
                        default=f"{Path(__file__).parent}/tests/data",
                        type=Path)

    raise SystemExit(main(parser.parse_args()))
