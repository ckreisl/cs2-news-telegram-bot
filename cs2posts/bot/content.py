from __future__ import annotations

import re
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


class ContentExtractor:

    @staticmethod
    def extract_videos(text: str) -> list[Video]:
        pattern = r"\[video webm=(.*?) mp4=(.*?) poster=(.*?) autoplay=(.*?) controls=(.*?)\]\[/video\]"
        matches = re.finditer(pattern, text)
        videos = []
        for result in matches:
            videos.append(Video(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                webm=result.group(1),
                mp4=result.group(2),
                poster=result.group(3),
                autoplay=result.group(4) == "true",
                controls=result.group(5) == "true"))

        return videos

    @staticmethod
    def extract_images(text: str) -> list[Image]:
        pattern = r"\[img\](.*?)\[/img\]"
        matches = re.finditer(pattern, text)
        images = []
        for result in matches:
            images.append(Image(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                url=result.group(1)))

        return images

    @staticmethod
    def extract_text_block(text: str, images: list[Image], videos: list[Video]) -> list[Content]:
        content: list[Content] = [*videos, *images]
        content.sort(key=lambda file: file.text_pos_start)

        if len(content) == 0:
            return [TextBlock(0, len(text), False, text)]

        blocks = []
        text_pos = 0

        for c in content:
            if c.text_pos_start == 0:
                text_pos = c.text_pos_end + 1
                continue

            blocks.append(TextBlock(
                text_pos_start=text_pos,
                text_pos_end=c.text_pos_start,
                is_heading=False,
                text=text[text_pos:c.text_pos_start].strip()))

            text_pos = c.text_pos_end + 1

        blocks.append(TextBlock(
            text_pos_start=text_pos,
            text_pos_end=len(text),
            is_heading=False,
            text=text[text_pos:len(text)].strip()))

        return blocks

    @staticmethod
    def extract_message_blocks(text: str) -> list[Content]:
        videos = ContentExtractor.extract_videos(text)
        images = ContentExtractor.extract_images(text)
        texts = ContentExtractor.extract_text_block(text, images, videos)

        content: list[Content] = [*videos, *images, *texts]
        content.sort(key=lambda file: file.text_pos_start)

        content[0].is_heading = True

        return content

    @staticmethod
    def extract_url(text: str) -> str | None:
        m = re.search(r'href="([^"]+)"', text)
        return m.group(1) if m else None
