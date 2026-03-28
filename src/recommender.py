"""
Music recommender — uses Last.fm when available, falls back to YouTube search.
Last.fm works well for globally known artists.
YouTube search works for ALL artists including Uzbek/Russian/regional.
"""
import re
import subprocess
import requests
from typing import NamedTuple
from src.ytdlp_path import get_ytdlp


LASTFM_BASE = "https://ws.audioscrobbler.com/2.0/"

# Patterns to strip from YouTube video titles
_TITLE_NOISE = re.compile(
    r"\s*[\(\[\|].*?[\)\]\|]|\s*-?\s*(official\s*)?(music\s*)?video|"
    r"\s*official\s*(audio|lyric|clip)|\s*\d{4}|\s*HD|,.*$",
    re.IGNORECASE,
)


class Track(NamedTuple):
    artist: str
    title: str


# ─── Last.fm helpers ─────────────────────────────────────────────────────────

def _lastfm_get(api_key: str, method: str, params: dict) -> dict:
    response = requests.get(
        LASTFM_BASE,
        params={"method": method, "api_key": api_key, "format": "json", **params},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _lastfm_similar_tracks(api_key: str, artist: str, title: str, limit: int) -> list[Track]:
    try:
        data = _lastfm_get(api_key, "track.getSimilar", {
            "artist": artist,
            "track": title,
            "limit": limit,
            "autocorrect": 1,
        })
        tracks = data.get("similartracks", {}).get("track", [])
        return [Track(artist=t["artist"]["name"], title=t["name"]) for t in tracks]
    except Exception:
        return []


def _lastfm_artist_has_data(api_key: str, artist: str) -> bool:
    """Check if Last.fm has meaningful data for this artist (>1000 listeners)."""
    try:
        data = _lastfm_get(api_key, "artist.getInfo", {
            "artist": artist,
            "autocorrect": 1,
        })
        listeners = int(data.get("artist", {}).get("stats", {}).get("listeners", 0))
        return listeners > 1000
    except Exception:
        return False


def _lastfm_similar_artists_tracks(api_key: str, artist: str, limit: int) -> list[Track]:
    results: list[Track] = []
    try:
        data = _lastfm_get(api_key, "artist.getSimilar", {
            "artist": artist,
            "limit": 3,
            "autocorrect": 1,
        })
        similar_artists = data.get("similarartists", {}).get("artist", [])
        for sim in similar_artists:
            top = _lastfm_get(api_key, "artist.getTopTracks", {
                "artist": sim["name"],
                "limit": limit,
            })
            for t in top.get("toptracks", {}).get("track", []):
                results.append(Track(artist=sim["name"], title=t["name"]))
    except Exception:
        pass
    return results


# ─── YouTube helpers ──────────────────────────────────────────────────────────

def _clean_youtube_title(raw_title: str, artist: str) -> str:
    """Strip noise from YouTube title to get clean song name."""
    title = _TITLE_NOISE.sub("", raw_title).strip(" -–—")
    # Remove artist name prefix if present
    artist_pattern = re.compile(re.escape(artist), re.IGNORECASE)
    title = artist_pattern.sub("", title).strip(" -–—")
    return title or raw_title.strip()


def _youtube_top_songs(artist: str, count: int) -> list[Track]:
    """Search YouTube for an artist's top songs and return Track list."""
    query = f"ytsearch{count}:{artist} official music video"
    cmd = [
        get_ytdlp(),
        "--flat-playlist",
        "--print", "%(uploader)s\t%(title)s",
        "--no-warnings",
        "--quiet",
        query,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        tracks: list[Track] = []
        for line in result.stdout.strip().splitlines():
            if "\t" not in line:
                continue
            uploader, raw_title = line.split("\t", 1)
            title = _clean_youtube_title(raw_title, artist)
            if title:
                tracks.append(Track(artist=artist, title=title))
        return tracks
    except Exception as e:
        print(f"  [WARN] YouTube search failed for '{artist}': {e}")
        return []


def _youtube_related_artists(artist: str) -> list[str]:
    """
    Search YouTube for '[artist] mix' playlists to find related artists mentioned.
    Simple heuristic: extract artist names from video titles in results.
    """
    query = f"ytsearch5:{artist} similar artists mix playlist"
    cmd = [
        get_ytdlp(),
        "--flat-playlist",
        "--print", "%(title)s",
        "--no-warnings",
        "--quiet",
        query,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        # Very naive: look for "Artist1 & Artist2" or "feat." patterns
        related: set[str] = set()
        for line in result.stdout.strip().splitlines():
            # Match "Artist ft. Other" or "Artist feat. Other" or "Artist & Other"
            for m in re.finditer(r"(?:feat\.?|ft\.?|&)\s+([A-Za-z\u0400-\u04FF ]{3,30}?)(?:\s*[-–|,]|$)", line, re.IGNORECASE):
                name = m.group(1).strip()
                if name.lower() != artist.lower() and len(name) > 2:
                    related.add(name)
        return list(related)[:3]
    except Exception:
        return []


# ─── Main expander ────────────────────────────────────────────────────────────

def expand_seed_list(api_key: str, seeds: list[Track], similar_per_seed: int) -> list[Track]:
    """
    Given seed tracks, return expanded recommendations.
    Strategy:
      1. If artist is well-known on Last.fm → use Last.fm similar tracks
      2. Otherwise → use YouTube top songs for that artist + related artists
    Deduplicates and excludes original seeds.
    """
    seen: set[tuple[str, str]] = {(t.artist.lower(), t.title.lower()) for t in seeds}
    recommendations: list[Track] = []

    def add(track: Track) -> None:
        key = (track.artist.lower(), track.title.lower())
        if key not in seen:
            seen.add(key)
            recommendations.append(track)

    for seed in seeds:
        print(f"  Finding similar to: {seed.artist} - {seed.title}")

        if api_key and _lastfm_artist_has_data(api_key, seed.artist):
            # Last.fm path — globally known artist
            print(f"    [Last.fm] Artist found in database")
            for t in _lastfm_similar_tracks(api_key, seed.artist, seed.title, limit=similar_per_seed):
                add(t)
            for t in _lastfm_similar_artists_tracks(api_key, seed.artist, limit=2):
                add(t)
        else:
            # YouTube path — regional/Uzbek/less-known artist
            print(f"    [YouTube] Using YouTube search (artist not in Last.fm)")
            for t in _youtube_top_songs(seed.artist, count=similar_per_seed):
                add(t)
            # Try to find related artists from YouTube
            for related_artist in _youtube_related_artists(seed.artist):
                for t in _youtube_top_songs(related_artist, count=3):
                    add(t)

    return recommendations
