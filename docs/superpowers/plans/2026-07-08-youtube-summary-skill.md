# youtube-summary スキル実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** YouTubeのURLから字幕を取得・整形し、聞き取りミスを補正した日本語要約をチャットに返すスキル `youtube-summary` を作る。

**Architecture:** 決定論的な処理(URL解析・字幕取得・整形)は同梱の単一ファイルPythonスクリプト `fetch_transcript.py` が担い、言語理解(誤認補正・要約)は SKILL.md の指示でClaudeが行う。スクリプトはメタデータJSONをstdoutに、整形済みテキストをファイルに出力し、エラーは `ERROR:<CODE>` + 終了コードで機械判別可能にする。

**Tech Stack:** Python 3.12(標準ライブラリのみ + 実行時依存 yt-dlp)、pytest 9(開発時のみ)

**Spec:** `docs/superpowers/specs/2026-07-08-youtube-summary-skill-design.md`

## Global Constraints

- スクリプトは単一ファイル・自己完結(`~/.claude/skills/` へのコピーで動くこと)。依存は yt-dlp のみ
- yt-dlp はスクリプト冒頭で import しない(未導入検出のため遅延 import)
- 全テキストI/OはUTF-8明示(`encoding="utf-8"`)
- 終了コード: 0=成功 / 1=その他 / 2=字幕なし / 3=yt-dlp未導入 / 4=動画アクセス不可
- stderr のエラーは必ず `ERROR:<CODE>: <detail>` 形式(CODE: BAD_URL, NO_SUBTITLES, YTDLP_MISSING, VIDEO_UNAVAILABLE, DOWNLOAD_FAILED)
- テストは deploy 対象外(deploy は SKILL.md と scripts/ のみ)
- テスト実行コマンド(worktreeルートから): `python -m pytest skills/youtube-summary/tests -v`
- コミットメッセージ末尾: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

## File Structure

```
skills/youtube-summary/
  SKILL.md                            # Task 5
  scripts/fetch_transcript.py         # Task 1-4 で段階的に構築
  tests/test_fetch_transcript.py      # Task 1-4 で段階的に構築
```

---

### Task 1: URLから動画IDを抽出する `extract_video_id`

**Files:**
- Create: `skills/youtube-summary/scripts/fetch_transcript.py`
- Test: `skills/youtube-summary/tests/test_fetch_transcript.py`

**Interfaces:**
- Consumes: なし(最初のタスク)
- Produces: `extract_video_id(url: str) -> str` — 11文字の動画IDを返す。見つからなければ `ValueError`

- [ ] **Step 1: Write the failing test**

`skills/youtube-summary/tests/test_fetch_transcript.py` を新規作成:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/youtube-summary/tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetch_transcript'`(スクリプト未作成のため)

- [ ] **Step 3: Write minimal implementation**

`skills/youtube-summary/scripts/fetch_transcript.py` を新規作成:

```python
#!/usr/bin/env python3
"""Fetch and clean a YouTube video's subtitles for summarization.

Usage:
    python fetch_transcript.py <URL> --out <DIR> [--langs ja,en]

On success: prints metadata JSON to stdout, writes cleaned transcript text
to <DIR>/transcript.txt, exits 0.
On failure: prints "ERROR:<CODE>: <detail>" to stderr and exits non-zero.

Exit codes:
    0  success
    1  other failure (bad URL, network, download)
    2  NO_SUBTITLES      video has no subtitle tracks at all
    3  YTDLP_MISSING     yt-dlp is not installed (pip install yt-dlp)
    4  VIDEO_UNAVAILABLE private / age-restricted / region-locked / deleted
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(url: str) -> str:
    """Return the 11-char video ID from any common YouTube URL form."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    for prefix in ("www.", "m."):
        host = host.removeprefix(prefix)
    candidate = ""
    if host == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
    elif host in ("youtube.com", "music.youtube.com"):
        parts = parsed.path.split("/")
        if parsed.path.startswith(("/shorts/", "/live/", "/embed/")) and len(parts) > 2:
            candidate = parts[2]
        elif parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [""])[0]
    if not VIDEO_ID_RE.match(candidate):
        raise ValueError(f"YouTube video ID not found in URL: {url}")
    return candidate
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/youtube-summary/tests -v`
Expected: PASS(13件)

- [ ] **Step 5: Commit**

```bash
git add skills/youtube-summary
git commit -m "feat(youtube-summary): add video ID extraction

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: 字幕トラック選択 `pick_track`

**Files:**
- Modify: `skills/youtube-summary/scripts/fetch_transcript.py`(末尾に追記)
- Test: `skills/youtube-summary/tests/test_fetch_transcript.py`(末尾に追記)

**Interfaces:**
- Consumes: なし(純粋関数)
- Produces: `pick_track(info: dict, preferred_langs: list[str]) -> tuple[str, str] | None` — yt-dlpのinfo dictから `(言語キー, 字幕種別)` を返す。種別は `"manual" | "auto" | "translated"`。字幕が全くなければ `None`

**背景知識:** yt-dlpのinfo dictでは手動字幕が `info["subtitles"]`、自動生成字幕が `info["automatic_captions"]` に `{言語キー: [トラック,...]}` 形式で入る。動画の原語は `info["language"]`。自動字幕には原語トラックがキー `"<原語>-orig"`(例 `en-orig`)または原語キーで入り、それ以外の言語キーは機械翻訳。`subtitles` にはキー `live_chat`(チャットリプレイ、字幕ではない)が入ることがあり除外必須。

- [ ] **Step 1: Write the failing test**

`tests/test_fetch_transcript.py` の末尾に追記:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/youtube-summary/tests -v -k pick_track`
Expected: FAIL — `AttributeError: module 'fetch_transcript' has no attribute 'pick_track'`

- [ ] **Step 3: Write minimal implementation**

`scripts/fetch_transcript.py` の末尾に追記:

```python
def pick_track(info: dict, preferred_langs: list[str]) -> tuple[str, str] | None:
    """Pick the best subtitle track from a yt-dlp info dict.

    Priority: manual (original language > preferred order > regional variant
    of original > any) > auto-generated original > machine-translated.
    Returns (language key, "manual" | "auto" | "translated") or None.
    """
    manual = {k: v for k, v in (info.get("subtitles") or {}).items()
              if k != "live_chat"}
    auto = info.get("automatic_captions") or {}
    orig = info.get("language") or ""

    if manual:
        if orig and orig in manual:
            return orig, "manual"
        for lang in preferred_langs:
            if lang in manual:
                return lang, "manual"
        for key in manual:
            if orig and key.split("-")[0] == orig:
                return key, "manual"
        return next(iter(manual)), "manual"

    if auto:
        if orig and f"{orig}-orig" in auto:
            return f"{orig}-orig", "auto"
        if orig and orig in auto:
            return orig, "auto"
        for key in auto:
            if key.endswith("-orig"):
                return key, "auto"
        for lang in preferred_langs:
            if lang in auto:
                return lang, "translated"
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/youtube-summary/tests -v`
Expected: PASS(20件、Task 1の13件含む)

- [ ] **Step 5: Commit**

```bash
git add skills/youtube-summary
git commit -m "feat(youtube-summary): add subtitle track selection

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: json3字幕の整形 `parse_json3`

**Files:**
- Modify: `skills/youtube-summary/scripts/fetch_transcript.py`(末尾に追記)
- Test: `skills/youtube-summary/tests/test_fetch_transcript.py`(末尾に追記)

**Interfaces:**
- Consumes: なし(純粋関数)
- Produces: `parse_json3(data: dict) -> str` — json3字幕データからタイムスタンプなし・重複なしのプレーンテキスト(行区切り)を返す

**背景知識:** json3はYouTube字幕のJSON形式。`{"events": [{"tStartMs": int, "segs": [{"utf8": str}, ...]}, ...]}`。改行だけのイベント(`segs: [{"utf8": "\n"}]`)や `segs` を持たないメタイベントが混ざる。自動字幕のロールアップ表示由来で同一行が連続することがある。

- [ ] **Step 1: Write the failing test**

`tests/test_fetch_transcript.py` の末尾に追記:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/youtube-summary/tests -v -k parse_json3`
Expected: FAIL — `AttributeError: module 'fetch_transcript' has no attribute 'parse_json3'`

- [ ] **Step 3: Write minimal implementation**

`scripts/fetch_transcript.py` の末尾に追記:

```python
def parse_json3(data: dict) -> str:
    """Flatten json3 caption events into clean plain-text lines."""
    lines: list[str] = []
    for event in data.get("events", []):
        text = "".join(seg.get("utf8", "") for seg in event.get("segs", []))
        text = " ".join(text.split())
        if not text:
            continue
        if lines and lines[-1] == text:
            continue
        lines.append(text)
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/youtube-summary/tests -v`
Expected: PASS(24件)

- [ ] **Step 5: Commit**

```bash
git add skills/youtube-summary
git commit -m "feat(youtube-summary): add json3 caption cleaning

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: CLI組み立て `run` + ネットワーク関数

**Files:**
- Modify: `skills/youtube-summary/scripts/fetch_transcript.py`(末尾に追記)
- Test: `skills/youtube-summary/tests/test_fetch_transcript.py`(末尾に追記)

**Interfaces:**
- Consumes: `extract_video_id`(Task 1)、`pick_track`(Task 2)、`parse_json3`(Task 3)
- Produces:
  - `run(argv: list[str] | None = None) -> int` — CLIエントリポイント。終了コードを返す
  - `_extract_info(url: str) -> dict` — yt-dlpでメタデータ取得(ネットワーク。テストではmonkeypatch対象)
  - `_download_subs(url: str, lang: str, subtitle_type: str, out_dir: Path) -> Path` — json3字幕をダウンロードしファイルパスを返す(ネットワーク。テストではmonkeypatch対象)
  - stdout JSON のキー: `title, channel, duration_seconds, duration_human, language, subtitle_type, transcript_path, char_count`

**設計メモ:** `run()` 自身は yt_dlp を import しない。import は `_extract_info` / `_download_subs` の内部でのみ行い、`run()` は `ImportError` を捕まえて `YTDLP_MISSING`(exit 3)に変換する。これによりユニットテストは yt-dlp 未導入環境でも2関数のmonkeypatchだけで全経路を通せる。

- [ ] **Step 1: Write the failing test**

`tests/test_fetch_transcript.py` の末尾に追記:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/youtube-summary/tests -v -k run`
Expected: FAIL — `AttributeError: module 'fetch_transcript' has no attribute 'run'`(6件とも)

- [ ] **Step 3: Write minimal implementation**

`scripts/fetch_transcript.py` の末尾に追記:

```python
def _extract_info(url: str) -> dict:
    """Fetch video metadata without downloading (network; needs yt-dlp)."""
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "skip_download": True,
            "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def _download_subs(url: str, lang: str, subtitle_type: str, out_dir: Path) -> Path:
    """Download the chosen subtitle track as json3 (network; needs yt-dlp)."""
    import yt_dlp
    opts = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "noplaylist": True,
        "writesubtitles": subtitle_type == "manual",
        "writeautomaticsub": subtitle_type != "manual",
        "subtitleslangs": [lang],
        "subtitlesformat": "json3",
        "outtmpl": str(out_dir / "captions"),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    path = out_dir / f"captions.{lang}.json3"
    if not path.exists():
        matches = sorted(out_dir.glob("captions.*.json3"))
        if not matches:
            raise RuntimeError("subtitle file was not written by yt-dlp")
        path = matches[0]
    return path


_UNAVAILABLE_MARKERS = (
    "Private video", "Sign in to confirm your age", "age-restricted",
    "not available in your country", "Video unavailable", "members-only",
    "This video has been removed",
)


def _classify_fetch_error(e: Exception) -> int:
    msg = str(e)
    if any(marker in msg for marker in _UNAVAILABLE_MARKERS):
        print(f"ERROR:VIDEO_UNAVAILABLE: {msg}", file=sys.stderr)
        return 4
    print(f"ERROR:DOWNLOAD_FAILED: {msg}", file=sys.stderr)
    return 1


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch and clean YouTube subtitles for summarization")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--langs", default="ja,en",
                        help="comma-separated preferred subtitle languages")
    args = parser.parse_args(argv)

    try:
        video_id = extract_video_id(args.url)
    except ValueError as e:
        print(f"ERROR:BAD_URL: {e}", file=sys.stderr)
        return 1

    canonical = f"https://www.youtube.com/watch?v={video_id}"
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    preferred = [x.strip() for x in args.langs.split(",") if x.strip()]

    try:
        info = _extract_info(canonical)
    except ImportError:
        print("ERROR:YTDLP_MISSING: install with 'pip install yt-dlp' and retry",
              file=sys.stderr)
        return 3
    except Exception as e:
        return _classify_fetch_error(e)

    picked = pick_track(info, preferred)
    if picked is None:
        print("ERROR:NO_SUBTITLES: this video has no subtitle tracks",
              file=sys.stderr)
        return 2
    lang, subtitle_type = picked

    try:
        json3_path = _download_subs(canonical, lang, subtitle_type, out_dir)
    except ImportError:
        print("ERROR:YTDLP_MISSING: install with 'pip install yt-dlp' and retry",
              file=sys.stderr)
        return 3
    except Exception as e:
        return _classify_fetch_error(e)

    data = json.loads(Path(json3_path).read_text(encoding="utf-8"))
    text = parse_json3(data)
    transcript_path = out_dir / "transcript.txt"
    transcript_path.write_text(text, encoding="utf-8")

    duration = info.get("duration") or 0
    meta = {
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "duration_seconds": duration,
        "duration_human": f"{duration // 3600}:{duration % 3600 // 60:02d}:{duration % 60:02d}",
        "language": lang,
        "subtitle_type": subtitle_type,
        "transcript_path": str(transcript_path),
        "char_count": len(text),
    }
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(run())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/youtube-summary/tests -v`
Expected: PASS(30件)

- [ ] **Step 5: Commit**

```bash
git add skills/youtube-summary
git commit -m "feat(youtube-summary): add CLI entry point with error codes

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: SKILL.md

**Files:**
- Create: `skills/youtube-summary/SKILL.md`

**Interfaces:**
- Consumes: Task 4 の CLI(`python scripts/fetch_transcript.py <URL> --out <DIR>`、終了コード 0-4、stdout JSONキー `title, channel, duration_human, language, subtitle_type, transcript_path, char_count`)
- Produces: スキル本体(トリガー定義 + Claudeへの実行手順)

- [ ] **Step 1: Write SKILL.md**

`skills/youtube-summary/SKILL.md` を新規作成(内容は以下の通り、そのまま):

````markdown
---
name: youtube-summary
description: Use when the user shares a YouTube URL and wants its content summarized or explained — triggers include "このYouTube要約して", "この動画の内容を教えて", "動画をまとめて", "summarize this YouTube video", or a YouTube link pasted together with a summarization request. Fetches the video's subtitles with a bundled yt-dlp script, silently corrects likely speech-recognition errors, and returns a structured Japanese summary in chat.
---

# YouTube Summary

YouTube動画のURLから字幕を取得し、聞き取りミスを補正した日本語要約をチャットに返す。

## フロー

1. **字幕取得**: セッションのスクラッチパッドを出力先にしてスクリプトを実行する:

   ```
   python <このスキルのベースディレクトリ>/scripts/fetch_transcript.py "<URL>" --out "<スクラッチパッド>/youtube-summary"
   ```

   成功時(exit 0)はstdoutにメタデータJSONが出る:
   `title` / `channel` / `duration_human` / `language` /
   `subtitle_type`(manual|auto|translated)/ `transcript_path` / `char_count`

2. **エラー分岐**(stderrの `ERROR:<CODE>` と終了コードで判定):
   - `YTDLP_MISSING`(exit 3): `pip install yt-dlp` を実行して**1回だけ**リトライ
   - `NO_SUBTITLES`(exit 2): 「この動画には字幕がないため要約できない」と報告して終了。
     内容を推測・捏造しない
   - `VIDEO_UNAVAILABLE`(exit 4): 非公開・年齢制限・地域制限等で取得できない旨を
     エラー内容とともに報告して終了
   - その他(exit 1): **1回だけ**リトライし、2回目も失敗したらエラー内容を報告して終了。
     無限リトライ禁止

3. **transcript読み込み**: `transcript_path` のファイルを読む。
   `char_count` が **80,000 を超える**場合は Read の offset/limit で分割して読み、
   チャンクごとに中間要約を作ってから最後に統合する

4. **聞き取りミス補正**: 文脈から明らかな誤認(同音語の取り違え、固有名詞の表記揺れ)は
   黙って直した内容で要約する。確信が持てない重要語のみ「(原文: ○○)」と注記する。
   補正箇所の一覧は出さない

5. **要約出力**: 動画が何語でも**日本語**で、下のテンプレでチャットに出力する。
   ファイル保存はしない

## 要約テンプレ

```markdown
## 要約: <動画タイトル>
<チャンネル名> / <長さ> / <字幕種別: 手動字幕 or 自動生成字幕>
※自動生成字幕ベースのため、固有名詞などに誤りが残っている可能性があります
(↑この注記行は subtitle_type が auto または translated の場合のみ)

**概要**
2〜3文。

**主要ポイント**
- 内容量に応じて3〜8点の箇条書き

**結論・所感**
話者の結論と、要約者としての短い所感。
```

## 注意

- プレイリストURLでも対象は動画単体(`v=` の動画のみ)。一括要約はしない
- 字幕なし動画への音声認識フォールバックはスコープ外
````

- [ ] **Step 2: Verify frontmatter and structure**

Run: `python -c "import re,pathlib; t=pathlib.Path('skills/youtube-summary/SKILL.md').read_text(encoding='utf-8'); m=re.match(r'^---\nname: youtube-summary\ndescription: .+\n---\n', t, re.S); print('OK' if m else 'BROKEN FRONTMATTER')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/youtube-summary/SKILL.md
git commit -m "feat(youtube-summary): add SKILL.md orchestrating fetch + summary

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: 実ネットワークE2E検証

**Files:**
- なし(検証のみ。修正が出た場合は該当ファイルを直してコミット)

**Interfaces:**
- Consumes: Task 4 の CLI 全体

**注意:** このタスクはネットワークとYouTubeの実挙動に依存する。失敗した場合は superpowers:systematic-debugging で原因を特定してから直すこと。

- [ ] **Step 1: yt-dlp未導入時の実挙動確認(導入前に実行)**

開発環境にはまだ yt-dlp が入っていない(スペック作成時点で確認済み)。先にこの状態を検証する:

Run: `python skills/youtube-summary/scripts/fetch_transcript.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --out "<スクラッチパッド>/e2e-test"`
Expected: exit 3、stderr に `ERROR:YTDLP_MISSING`
(既に yt-dlp が入っていた場合はこのステップをスキップして構わない)

- [ ] **Step 2: yt-dlp導入**

Run: `pip install yt-dlp`
Expected: 正常終了。`python -c "import yt_dlp; print(yt_dlp.version.__version__)"` がバージョンを出す

- [ ] **Step 3: 実動画で英語字幕取得**

"Me at the zoo"(YouTube最古の動画、英語、字幕あり、削除リスク極小)で検証:

Run: `python skills/youtube-summary/scripts/fetch_transcript.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" --out "<スクラッチパッド>/e2e-test"`
Expected: exit 0。stdout のJSONで `title` に "Me at the zoo"、`char_count > 0`。`transcript.txt` に "elephants" を含む英文テキスト

- [ ] **Step 4: 日本語動画で検証**

ユーザーに日本語動画のURLを1つ提供してもらい(いなければ日本語の公式チャンネルの字幕付き動画を検索して選ぶ)、同様に実行:
Expected: exit 0、`language` が `ja` 系、transcript が日本語

- [ ] **Step 5: 短縮URL形式で検証**

Run: `python skills/youtube-summary/scripts/fetch_transcript.py "https://youtu.be/jNQXAC9IVRw" --out "<スクラッチパッド>/e2e-test2"`
Expected: Step 3 と同じ動画のメタデータで exit 0

- [ ] **Step 6: 字幕なしケースの扱い(確認のみ)**

スペックのE2Eケース③(字幕なし動画→エラー報告)は、字幕ゼロの実動画を安定して確保できないため、ユニットテスト `test_run_no_subtitles_exits_2` でのカバーとする。E2E中に偶然字幕なし動画に当たったら実挙動(exit 2)を確認しておく。

- [ ] **Step 7: ユニットテスト全体の回帰確認**

Run: `python -m pytest skills/youtube-summary/tests -v`
Expected: PASS(30件)

- [ ] **Step 8: 発見事項の反映**

E2Eで実挙動とテストの想定がズレていた場合(json3のキー名、yt-dlpのオプション名、エラーメッセージ文言など)は修正してテストを直し、コミット:

```bash
git add skills/youtube-summary
git commit -m "fix(youtube-summary): align with real yt-dlp behavior found in E2E

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(ズレがなければこのステップはスキップ)

---

### Task 7: スキルとしての通し検証と配布

**Files:**
- Copy: `skills/youtube-summary/SKILL.md` と `skills/youtube-summary/scripts/` → `~/.claude/skills/youtube-summary/`(tests は配布しない)

**Interfaces:**
- Consumes: Task 5 の SKILL.md、Task 6 で検証済みのスクリプト

- [ ] **Step 1: SKILL.md の手順を手動トレース**

SKILL.md を読み、Task 6 Step 3 の実行結果(メタデータJSON + transcript)を使って要約テンプレ通りの日本語要約を実際に生成してみる。テンプレの全項目(タイトル行・字幕種別・auto注記・概要・主要ポイント・結論)が埋まることを確認する。

- [ ] **Step 2: ユーザーレビュー**

生成した要約サンプルをユーザーに見せ、フォーマット・粒度・注記の出方に問題がないか確認してもらう。修正要望があれば SKILL.md を直してコミットしてから次へ。

- [ ] **Step 3: グローバル配布**

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\youtube-summary\scripts" | Out-Null
Copy-Item skills\youtube-summary\SKILL.md "$env:USERPROFILE\.claude\skills\youtube-summary\SKILL.md"
Copy-Item skills\youtube-summary\scripts\fetch_transcript.py "$env:USERPROFILE\.claude\skills\youtube-summary\scripts\fetch_transcript.py"
```

Expected: `~/.claude/skills/youtube-summary/` に SKILL.md と scripts/fetch_transcript.py の2ファイルのみ

- [ ] **Step 4: 配布内容の検証**

Run: `Get-ChildItem -Recurse "$env:USERPROFILE\.claude\skills\youtube-summary" | Select-Object FullName`
Expected: SKILL.md と scripts\fetch_transcript.py のみ(tests なし)

- [ ] **Step 5: ブランチの仕上げ**

superpowers:finishing-a-development-branch スキルを使い、master へのマージ方法をユーザーに確認する(このリポジトリは別セッションが master を触っている可能性があるため、マージ前に `git fetch` 等で最新化すること)。
