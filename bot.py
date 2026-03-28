"""
MassivMusicBot — Smart car music downloader.

Usage:
  python bot.py --seeds data/seed_songs.txt              # Download seeds only
  python bot.py --seeds data/seed_songs.txt --expand     # Seeds + similar songs
  python bot.py --seeds data/seed_songs.txt --expand --usb /Volumes/USB  # + copy to USB
  python bot.py --expand --count 30                      # Find 30 extra similar songs
"""
import argparse
import sys
from pathlib import Path

from src.config_loader import load_config
from src.seed_parser import parse_seed_file
from src.recommender import expand_seed_list, Track as RecTrack
from src.downloader import download_all, Track


BANNER = """
  __  __               _       __  __           _      ____        _
 |  \/  | __ _ ___ ___(_)_   _|  \/  |_   _ ___(_) ___| __ )  ___ | |_
 | |\/| |/ _` / __/ __| \ \ / / |\/| | | | / __| |/ __|  _ \ / _ \| __|
 | |  | | (_| \__ \__ \ |\ V /| |  | | |_| \__ \ | (__| |_) | (_) | |_
 |_|  |_|\__,_|___/___/_| \_/ |_|  |_|\__,_|___/_|\___|____/ \___/ \__|
"""


def rec_to_dl(t: RecTrack) -> Track:
    return Track(artist=t.artist, title=t.title)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smart car music downloader — seeds + similar songs"
    )
    parser.add_argument(
        "--seeds",
        default="data/seed_songs.txt",
        help="Path to seed songs file (default: data/seed_songs.txt)",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Auto-find similar songs based on seed list",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Limit total tracks to download (seeds + recommended)",
    )
    parser.add_argument(
        "--usb",
        default=None,
        help="USB drive path to copy music to after download (e.g. /Volumes/USB or D:\\)",
    )
    args = parser.parse_args()

    print(BANNER)
    config = load_config()

    # Override USB path from CLI if provided
    usb_path = args.usb or config.get("usb_path") or ""

    # --- Parse seed songs ---
    seeds_path = args.seeds
    if not Path(seeds_path).exists():
        print(f"[ERROR] Seed file not found: {seeds_path}")
        print("  Edit data/seed_songs.txt and add your songs.")
        sys.exit(1)

    from src.seed_parser import parse_seed_file
    seed_tracks = parse_seed_file(seeds_path)

    if not seed_tracks:
        print("[ERROR] No valid songs found in seed file.")
        print("  Format: Artist - Song Title (one per line)")
        sys.exit(1)

    print(f"\nLoaded {len(seed_tracks)} seed songs.")

    # --- Expand with recommendations ---
    all_tracks: list[Track] = [Track(t.artist, t.title) for t in seed_tracks]

    if args.expand:
        print(f"\nFinding similar songs via Last.fm...")
        rec_tracks = expand_seed_list(
            api_key=config["lastfm_api_key"],
            seeds=[RecTrack(t.artist, t.title) for t in seed_tracks],
            similar_per_seed=config.get("max_similar_per_seed", 5),
        )
        extra = [Track(t.artist, t.title) for t in rec_tracks]
        print(f"  Found {len(extra)} additional recommended tracks.")
        all_tracks = all_tracks + extra

    # Apply count limit
    if args.count and len(all_tracks) > args.count:
        all_tracks = all_tracks[: args.count]
        print(f"  Limited to {args.count} total tracks.")

    # --- Download ---
    print(f"\nDownloading {len(all_tracks)} tracks to: {config['download_dir']}\n")
    success, skipped = download_all(
        tracks=all_tracks,
        download_dir=config["download_dir"],
        quality=config.get("audio_quality", "320"),
    )
    print(f"\nDone: {success} downloaded, {skipped} already existed.")

    # --- Copy to USB ---
    if usb_path:
        print(f"\nExporting to USB: {usb_path}")
        from src.usb_exporter import export_to_usb
        copied, usb_skipped = export_to_usb(config["download_dir"], usb_path)
        print(f"USB export done: {copied} copied, {usb_skipped} already on USB.")
    else:
        print("\nTip: Run with --usb /path/to/USB to copy music to your flash drive.")


if __name__ == "__main__":
    main()
