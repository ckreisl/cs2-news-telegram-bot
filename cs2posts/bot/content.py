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
class Youtube(Content):
    url: str

    def get_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.url}"


@dataclass
class Image(Content):
    url: str


@dataclass
class TextBlock(Content):
    text: str


class ContentExtractor:

    @staticmethod
    def extract_youtube(text: str) -> list[Youtube]:
        videos = []

        youtube_pattern = r"\[previewyoutube=([^;]+);.*?\]\[/previewyoutube\]"
        matches = re.finditer(youtube_pattern, text)

        for result in matches:
            videos.append(Youtube(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                url=result.group(1)))

        return videos

    @staticmethod
    def extract_videos(text: str) -> list[Video]:
        videos = []

        video_pattern = re.compile(r'\[video\s+(.*?)\]\[/video\]', re.DOTALL)
        matches = re.finditer(video_pattern, text)

        patterns = {
            'mp4': r'mp4=<a[^>]+href="([^"]+)">',
            'webm': r'webm=<a[^>]+href="([^"]+)">',
            'poster': r'poster=<a[^>]+href="([^"]+)">',
            'autoplay': r'autoplay=([^\s\]]+)',
            'controls': r'controls=([^\s\]]+)'
        }

        for result in matches:
            attr = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, result[0])
                if not match:
                    continue
                attr[key] = match.group(1)

            videos.append(Video(
                text_pos_start=result.start(),
                text_pos_end=result.end(),
                is_heading=False,
                webm=attr.get('webm', ''),
                mp4=attr.get('mp4', ''),
                poster=attr.get('poster', ''),
                autoplay=attr.get('autoplay', 'false') == "true",
                controls=attr.get('controls', 'false') == "true"))

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
    def extract_text_block(text: str, images: list[Image], videos: list[Video], youtube: list[Youtube]) -> list[Content]:
        content: list[Content] = [*videos, *youtube, *images]
        content.sort(key=lambda file: file.text_pos_start)

        if len(content) == 0:
            return [TextBlock(0, len(text), False, text)]

        blocks = []
        text_pos = 0

        for c in content:
            if c.text_pos_start == 0:
                text_pos = c.text_pos_end
                continue

            blocks.append(TextBlock(
                text_pos_start=text_pos,
                text_pos_end=c.text_pos_start,
                is_heading=False,
                text=text[text_pos:c.text_pos_start].strip()))

            text_pos = c.text_pos_end

        blocks.append(TextBlock(
            text_pos_start=text_pos,
            text_pos_end=len(text),
            is_heading=False,
            text=text[text_pos:len(text)].strip()))

        return blocks

    @staticmethod
    def extract_message_blocks(text: str) -> list[Content]:
        youtube = ContentExtractor.extract_youtube(text)
        videos = ContentExtractor.extract_videos(text)
        images = ContentExtractor.extract_images(text)
        texts = ContentExtractor.extract_text_block(text, images, videos, youtube)

        # TODO: Refactor this
        # New Steam news if image is clickable the link contains an image
        def combine_text_blocks(text_blocks: list[TextBlock]) -> list[TextBlock]:

            if len(text_blocks) == 0:
                return text_blocks

            if len(text_blocks) == 1:
                return text_blocks

            blocks = []

            i = 0
            while i < len(text_blocks):
                left = text_blocks[i]
                idx_right = i + 1
                if idx_right >= len(text_blocks):
                    blocks.append(left)
                    break
                right = text_blocks[idx_right]

                if left.text.endswith('>') and right.text.startswith('</a>'):
                    blocks.append(TextBlock(
                        text_pos_start=left.text_pos_start,
                        text_pos_end=right.text_pos_end,
                        is_heading=left.is_heading,
                        text=left.text + "\nImage Link" + right.text))
                    i += 2
                    continue

                blocks.append(left)
                i += 1

            return blocks

        texts = combine_text_blocks(texts)

        content: list[Content] = [*youtube, *videos, *images, *texts]
        content.sort(key=lambda file: file.text_pos_start)

        content[0].is_heading = True

        return content

    @staticmethod
    def extract_url(text: str) -> str | None:
        if ContentExtractor.is_url(text):
            return text
        m = re.search(r'href="([^"]+)"', text)
        return m.group(1) if m else None

    @staticmethod
    def is_url(text: str) -> bool:
        url_regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        url_pattern = re.compile(url_regex)
        return re.match(url_pattern, text) is not None
