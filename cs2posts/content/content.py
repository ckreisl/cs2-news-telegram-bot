from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Content:
    text_pos_start: int
    text_pos_end: int
    is_heading: bool


@dataclass
class Video(Content):
    webm: str
    mp4: str
    poster: str
    autoplay: bool
    controls: bool


@dataclass
class Image(Content):
    url: str


@dataclass
class TextBlock(Content):
    text: str


@dataclass
class Youtube(Content):
    url: str

    def get_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.url}"
