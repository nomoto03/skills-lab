import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_transcript as ft


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtube.com/watch?v=dQw4w9WgXcQ&list=PLxyz&index=2",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ?t=42",
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    "https://www.youtube.com/live/dQw4w9WgXcQ",
    "https://www.youtube.com/embed/dQw4w9WgXcQ",
    "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
])
def test_extract_video_id_valid(url):
    assert ft.extract_video_id(url) == "dQw4w9WgXcQ"


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/",
    "https://www.youtube.com/watch",
    "https://example.com/watch?v=dQw4w9WgXcQ",
    "not a url",
    "https://www.youtube.com/watch?v=short",
])
def test_extract_video_id_invalid(url):
    with pytest.raises(ValueError):
        ft.extract_video_id(url)


def test_pick_track_manual_original_language_wins():
    info = {"language": "ja",
            "subtitles": {"ja": [{}], "en": [{}]},
            "automatic_captions": {"ja-orig": [{}]}}
    assert ft.pick_track(info, ["ja", "en"]) == ("ja", "manual")


def test_pick_track_manual_preferred_order_when_no_original_manual():
    info = {"language": "de",
            "subtitles": {"en": [{}], "fr": [{}]},
            "automatic_captions": {}}
    assert ft.pick_track(info, ["ja", "en"]) == ("en", "manual")


def test_pick_track_manual_regional_variant_of_original():
    info = {"language": "en", "subtitles": {"en-US": [{}]}, "automatic_captions": {}}
    assert ft.pick_track(info, ["ja"]) == ("en-US", "manual")


def test_pick_track_auto_original_when_no_manual():
    info = {"language": "en",
            "subtitles": {},
            "automatic_captions": {"en-orig": [{}], "en": [{}], "ja": [{}]}}
    assert ft.pick_track(info, ["ja", "en"]) == ("en-orig", "auto")


def test_pick_track_translated_fallback():
    info = {"language": None, "subtitles": {}, "automatic_captions": {"ja": [{}]}}
    assert ft.pick_track(info, ["ja", "en"]) == ("ja", "translated")


def test_pick_track_live_chat_is_not_a_subtitle():
    info = {"language": "en", "subtitles": {"live_chat": [{}]}, "automatic_captions": {}}
    assert ft.pick_track(info, ["ja", "en"]) is None


def test_pick_track_no_tracks_returns_none():
    assert ft.pick_track({"language": "en"}, ["ja"]) is None


def test_parse_json3_joins_segments_and_lines():
    data = {"events": [
        {"tStartMs": 0, "segs": [{"utf8": "こんにちは"}, {"utf8": "世界"}]},
        {"tStartMs": 1000, "segs": [{"utf8": "\n"}]},
        {"tStartMs": 2000, "segs": [{"utf8": "second   line"}]},
    ]}
    assert ft.parse_json3(data) == "こんにちは世界\nsecond line"


def test_parse_json3_drops_consecutive_duplicates():
    data = {"events": [
        {"segs": [{"utf8": "same line"}]},
        {"segs": [{"utf8": "same line"}]},
        {"segs": [{"utf8": "next"}]},
    ]}
    assert ft.parse_json3(data) == "same line\nnext"


def test_parse_json3_handles_events_without_segs():
    data = {"events": [{"tStartMs": 0}, {"segs": [{"utf8": "ok"}]}]}
    assert ft.parse_json3(data) == "ok"


def test_parse_json3_empty_events():
    assert ft.parse_json3({"events": []}) == ""
    assert ft.parse_json3({}) == ""
