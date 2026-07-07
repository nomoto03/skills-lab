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
