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


def _extract_info(url: str) -> dict:
    """Fetch video metadata without downloading (network; needs yt-dlp)."""
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "noprogress": True,
            "skip_download": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def _download_subs(url: str, lang: str, subtitle_type: str, out_dir: Path) -> Path:
    """Download the chosen subtitle track as json3 (network; needs yt-dlp)."""
    import yt_dlp
    opts = {
        "quiet": True, "no_warnings": True, "noprogress": True,
        "skip_download": True,
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
