from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Content:
    """A span of a post body, located by its position in the source text."""

    text_pos_start: int
    text_pos_end: int
    is_heading: bool


@dataclass
class Video(Content):
    webm: str | None
    mp4: str | None
    poster: str | None
    autoplay: bool | None
    controls: bool | None

    @property
    def source_url(self) -> str | None:
        """The playable source, preferring mp4 for Telegram compatibility.

        An empty string counts as absent, so a video carrying only a webm is
        still sent rather than silently skipped.
        """
        return self.mp4 or self.webm or None

    def is_empty(self) -> bool:
        return self.source_url is None


@dataclass
class Image(Content):
    url: str


@dataclass
class Carousel(Content):
    images: list[Image]


@dataclass
class TextBlock(Content):
    text: str


@dataclass
class Youtube(Content):
    url: str

    @property
    def watch_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.url}"
