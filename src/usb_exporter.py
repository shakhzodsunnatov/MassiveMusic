"""
Copies downloaded MP3s to a USB flash drive, preserving Artist/Song structure.
Works on both macOS and Windows.
"""
import shutil
from pathlib import Path


def export_to_usb(download_dir: str, usb_path: str) -> tuple[int, int]:
    """
    Copy all MP3 files from download_dir to usb_path.
    Keeps Artist subfolder structure.
    Returns (copied_count, skipped_count).
    """
    src = Path(download_dir)
    dst = Path(usb_path)

    if not dst.exists():
        print(f"[ERROR] USB path not found: {usb_path}")
        print("  Make sure your USB drive is connected and the path is correct.")
        return 0, 0

    copied = 0
    skipped = 0

    mp3_files = list(src.rglob("*.mp3"))
    if not mp3_files:
        print("[WARN] No MP3 files found to copy.")
        return 0, 0

    print(f"Copying {len(mp3_files)} files to {usb_path}...")

    for mp3 in mp3_files:
        # Preserve relative path (e.g. Artist/Artist - Song.mp3)
        relative = mp3.relative_to(src)
        target = dst / relative
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            skipped += 1
            continue

        shutil.copy2(mp3, target)
        copied += 1
        print(f"  Copied: {relative}")

    return copied, skipped
