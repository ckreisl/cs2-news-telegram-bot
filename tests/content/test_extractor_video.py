from __future__ import annotations

from cs2posts.content.content import Video
from cs2posts.content.extractor_video import VideoExtractor


# Tests for VideoExtractor class
def test_video_extractor_extract_single_video():
    text = '[video webm="https://example.com/video.webm" mp4="https://example.com/video.mp4"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert isinstance(videos[0], Video)


def test_video_extractor_extract_video_with_webm():
    text = '[video webm="https://example.com/video.webm"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].webm == "https://example.com/video.webm"
    assert videos[0].mp4 == ""


def test_video_extractor_extract_video_with_mp4():
    text = '[video mp4="https://example.com/video.mp4"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].mp4 == "https://example.com/video.mp4"
    assert videos[0].webm == ""


def test_video_extractor_extract_video_with_poster():
    text = '[video mp4="https://example.com/video.mp4" poster="https://example.com/poster.jpg"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].poster == "https://example.com/poster.jpg"


def test_video_extractor_extract_video_autoplay_true():
    text = '[video mp4="https://example.com/video.mp4" autoplay="true"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].autoplay is True


def test_video_extractor_extract_video_autoplay_false():
    text = '[video mp4="https://example.com/video.mp4" autoplay="false"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].autoplay is False


def test_video_extractor_extract_video_autoplay_1():
    text = '[video mp4="https://example.com/video.mp4" autoplay="1"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].autoplay is True


def test_video_extractor_extract_video_autoplay_0():
    text = '[video mp4="https://example.com/video.mp4" autoplay="0"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].autoplay is False


def test_video_extractor_extract_video_controls_true():
    text = '[video mp4="https://example.com/video.mp4" controls="true"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].controls is True


def test_video_extractor_extract_video_controls_false():
    text = '[video mp4="https://example.com/video.mp4" controls="false"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].controls is False


def test_video_extractor_extract_multiple_videos():
    text = '[video mp4="https://example.com/video1.mp4"][/video] text [video mp4="https://example.com/video2.mp4"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 2
    assert videos[0].mp4 == "https://example.com/video1.mp4"
    assert videos[1].mp4 == "https://example.com/video2.mp4"


def test_video_extractor_extract_no_videos():
    text = "no videos here"
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 0


def test_video_extractor_extract_empty_string():
    text = ""
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 0


def test_video_extractor_extract_video_positions():
    text = '[video mp4="https://example.com/video.mp4"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert videos[0].text_pos_start == 0
    assert videos[0].text_pos_end == len(text)


def test_video_extractor_extract_is_heading_false():
    text = '[video mp4="https://example.com/video.mp4"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert videos[0].is_heading is False


def test_video_extractor_extract_with_html_entities():
    text = '[video mp4=&quot;https://example.com/video.mp4&quot;][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].mp4 == "https://example.com/video.mp4"


def test_video_extractor_extract_with_anchor_href():
    text = '[video mp4=<a href="https://example.com/video.mp4">link</a>][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].mp4 == "https://example.com/video.mp4"


def test_video_extractor_extract_autoplay_yes():
    text = '[video mp4="https://example.com/video.mp4" autoplay="yes"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert videos[0].autoplay is True


def test_video_extractor_extract_autoplay_no():
    text = '[video mp4="https://example.com/video.mp4" autoplay="no"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert videos[0].autoplay is False


def test_video_extractor_extract_autoplay_on():
    text = '[video mp4="https://example.com/video.mp4" autoplay="on"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert videos[0].autoplay is True


def test_video_extractor_extract_autoplay_off():
    text = '[video mp4="https://example.com/video.mp4" autoplay="off"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert videos[0].autoplay is False


def test_video_extractor_extract_all_attributes():
    text = '[video webm="https://example.com/video.webm" mp4="https://example.com/video.mp4" poster="https://example.com/poster.jpg" autoplay="true" controls="false"][/video]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].webm == "https://example.com/video.webm"
    assert videos[0].mp4 == "https://example.com/video.mp4"
    assert videos[0].poster == "https://example.com/poster.jpg"
    assert videos[0].autoplay is True
    assert videos[0].controls is False


def test_video_extractor_to_bool_none():
    extractor = VideoExtractor("")
    assert extractor._to_bool(None) is None


def test_video_extractor_to_bool_invalid():
    extractor = VideoExtractor("")
    assert extractor._to_bool("invalid") is None


def test_video_extractor_extract_url_no_match():
    extractor = VideoExtractor("")
    assert extractor._extract_url("no url here") is None


def test_video_extractor_extract_url_direct():
    extractor = VideoExtractor("")
    assert extractor._extract_url("https://example.com/video.mp4") == "https://example.com/video.mp4"


def test_video_extractor_case_insensitive():
    text = '[VIDEO MP4="https://example.com/video.mp4"][/VIDEO]'
    extractor = VideoExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].mp4 == "https://example.com/video.mp4"
