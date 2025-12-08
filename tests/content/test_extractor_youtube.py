from __future__ import annotations

from cs2posts.content.content import Youtube
from cs2posts.content.extractor_youtube import YoutubeExtractor


def test_youtube_extractor_extract_single_video():
    text = '[previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert isinstance(videos[0], Youtube)


def test_youtube_extractor_extract_video_id():
    text = '[previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert videos[0].url == "dQw4w9WgXcQ"


def test_youtube_extractor_extract_multiple_videos():
    text = '[previewyoutube=video1;full][/previewyoutube] text [previewyoutube=video2;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 2
    assert videos[0].url == "video1"
    assert videos[1].url == "video2"


def test_youtube_extractor_extract_no_videos():
    text = "no youtube videos here"
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 0


def test_youtube_extractor_extract_empty_string():
    text = ""
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 0


def test_youtube_extractor_extract_video_positions():
    text = '[previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert videos[0].text_pos_start == 0
    assert videos[0].text_pos_end == len(text)


def test_youtube_extractor_extract_is_heading_false():
    text = '[previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert videos[0].is_heading is False


def test_youtube_extractor_extract_with_text_before():
    text = 'before [previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].text_pos_start == 7


def test_youtube_extractor_extract_with_text_after():
    text = '[previewyoutube=dQw4w9WgXcQ;full][/previewyoutube] after'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1


def test_youtube_extractor_extract_different_options():
    text = '[previewyoutube=abc123;leftalign][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].url == "abc123"


def test_youtube_extractor_extract_video_url_generation():
    text = '[previewyoutube=dQw4w9WgXcQ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert videos[0].get_url() == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_youtube_extractor_extract_long_video_id():
    text = '[previewyoutube=abcdefghijk;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].url == "abcdefghijk"


def test_youtube_extractor_extract_video_id_with_underscore():
    text = '[previewyoutube=abc_123_XYZ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].url == "abc_123_XYZ"


def test_youtube_extractor_extract_video_id_with_hyphen():
    text = '[previewyoutube=abc-123-XYZ;full][/previewyoutube]'
    extractor = YoutubeExtractor(text)
    videos = extractor.extract()
    assert len(videos) == 1
    assert videos[0].url == "abc-123-XYZ"
