from __future__ import annotations

import re

from .content import Video
from .extractor import Extractor


class VideoExtractor(Extractor):

    def extract(self) -> list[Video]:
        videos = []

        video_pattern = re.compile(r'\[video\s+(.*?)\]\[/video\]', re.DOTALL)
        matches = re.finditer(video_pattern, self.text)

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
