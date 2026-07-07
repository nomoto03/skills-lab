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


def _fake_info(**over):
    info = {"title": "Test Video", "channel": "Test Channel", "duration": 90,
            "language": "ja", "subtitles": {"ja": [{}]}, "automatic_captions": {}}
    info.update(over)
    return info


def test_run_happy_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ft, "_extract_info", lambda url: _fake_info())

    def fake_download(url, lang, subtitle_type, out_dir):
        p = out_dir / f"captions.{lang}.json3"
        p.write_text(json.dumps({"events": [{"segs": [{"utf8": "テスト字幕"}]}]}),
                     encoding="utf-8")
        return p

    monkeypatch.setattr(ft, "_download_subs", fake_download)
    rc = ft.run(["https://youtu.be/dQw4w9WgXcQ", "--out", str(tmp_path)])
    assert rc == 0
    meta = json.loads(capsys.readouterr().out)
    assert meta["title"] == "Test Video"
    assert meta["channel"] == "Test Channel"
    assert meta["language"] == "ja"
    assert meta["subtitle_type"] == "manual"
    assert meta["duration_human"] == "0:01:30"
    assert meta["char_count"] == 5
    assert (tmp_path / "transcript.txt").read_text(encoding="utf-8") == "テスト字幕"
    assert meta["transcript_path"] == str(tmp_path / "transcript.txt")


def test_run_no_subtitles_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ft, "_extract_info",
                        lambda url: _fake_info(subtitles={}, automatic_captions={}))
    rc = ft.run(["https://youtu.be/dQw4w9WgXcQ", "--out", str(tmp_path)])
    assert rc == 2
    assert "ERROR:NO_SUBTITLES" in capsys.readouterr().err


def test_run_bad_url_exits_1(tmp_path, capsys):
    rc = ft.run(["https://example.com/x", "--out", str(tmp_path)])
    assert rc == 1
    assert "ERROR:BAD_URL" in capsys.readouterr().err


def test_run_video_unavailable_exits_4(tmp_path, monkeypatch, capsys):
    def boom(url):
        raise RuntimeError("Private video. Sign in if you've been granted access")

    monkeypatch.setattr(ft, "_extract_info", boom)
    rc = ft.run(["https://youtu.be/dQw4w9WgXcQ", "--out", str(tmp_path)])
    assert rc == 4
    assert "ERROR:VIDEO_UNAVAILABLE" in capsys.readouterr().err


def test_run_ytdlp_missing_exits_3(tmp_path, monkeypatch, capsys):
    def boom(url):
        raise ImportError("No module named 'yt_dlp'")

    monkeypatch.setattr(ft, "_extract_info", boom)
    rc = ft.run(["https://youtu.be/dQw4w9WgXcQ", "--out", str(tmp_path)])
    assert rc == 3
    assert "ERROR:YTDLP_MISSING" in capsys.readouterr().err


def test_run_generic_download_failure_exits_1(tmp_path, monkeypatch, capsys):
    def boom(url):
        raise RuntimeError("Unable to download webpage: timed out")

    monkeypatch.setattr(ft, "_extract_info", boom)
    rc = ft.run(["https://youtu.be/dQw4w9WgXcQ", "--out", str(tmp_path)])
    assert rc == 1
    assert "ERROR:DOWNLOAD_FAILED" in capsys.readouterr().err
