"""
yt-dlp wrapper — searches YouTube for a track and downloads best MP3.
Tracks already downloaded are skipped via a downloaded.json log.
"""
import json
import subprocess
import re
from pathlib import Path
from typing import NamedTuple
from src.ytdlp_path import get_ytdlp


class Track(NamedTuple):
    artist: str
    title: str


def _sanitize(name: str) -> str:
    """Remove characters that are invalid in file/folder names (cross-platform)."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def _log_path(download_dir: str) -> Path:
    return Path(download_dir) / "downloaded.json"


def load_downloaded_log(download_dir: str) -> set[str]:
    path = _log_path(download_dir)
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return set(json.load(f))


def save_downloaded_log(download_dir: str, log: set[str]) -> None:
    path = _log_path(download_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(log), f, ensure_ascii=False, indent=2)


def _track_key(track: Track) -> str:
    return f"{track.artist.lower()} - {track.title.lower()}"


def download_track(track: Track, download_dir: str, quality: str = "320") -> bool:
    """
    Search YouTube for `artist - title`, download as MP3 into
    `download_dir/<Artist>/Artist - Title.mp3`.
    Returns True on success.
    """
    artist_dir = Path(download_dir) / _sanitize(track.artist)
    artist_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(artist_dir / f"{_sanitize(track.artist)} - {_sanitize(track.title)}.%(ext)s")
    search_query = f"ytsearch1:{track.artist} - {track.title} official audio"

    try:
        ytdlp = get_ytdlp()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return False

    cmd = [
        ytdlp,
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", quality,
        "--output", output_template,
        "--no-warnings",
        "--quiet",
        search_query,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return True
        print(f"  [WARN] yt-dlp error for '{track.artist} - {track.title}': {result.stderr.strip()}")
        return False
    except subprocess.TimeoutExpired:
        print(f"  [WARN] Download timed out: {track.artist} - {track.title}")
        return False


def download_all(
    tracks: list[Track],
    download_dir: str,
    quality: str = "320",
) -> tuple[int, int]:
    """
    Download all tracks, skip already-downloaded ones.
    Returns (success_count, skipped_count).
    """
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    log = load_downloaded_log(download_dir)
    success = 0
    skipped = 0

    for i, track in enumerate(tracks, 1):
        key = _track_key(track)
        label = f"{track.artist} - {track.title}"

        if key in log:
            print(f"  [{i}/{len(tracks)}] SKIP  {label}")
            skipped += 1
            continue

        print(f"  [{i}/{len(tracks)}] DL    {label}")
        ok = download_track(track, download_dir, quality)
        if ok:
            log.add(key)
            save_downloaded_log(download_dir, log)
            success += 1
        else:
            print(f"  [{i}/{len(tracks)}] FAIL  {label}")

    return success, skipped
