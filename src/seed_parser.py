"""
Reads seed_songs.txt and parses lines into Track objects.
Expected format per line: Artist - Song Title
Lines starting with # are comments and are ignored.
"""
from pathlib import Path
from src.downloader import Track


def parse_seed_file(path: str) -> list[Track]:
    tracks: list[Track] = []
    lines = Path(path).read_text(encoding="utf-8").splitlines()

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if " - " not in line:
            print(f"  [WARN] Skipping invalid line (expected 'Artist - Title'): {line!r}")
            continue
        artist, _, title = line.partition(" - ")
        tracks.append(Track(artist=artist.strip(), title=title.strip()))

    return tracks
