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
