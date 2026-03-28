"""Resolve the yt-dlp executable path — works inside virtualenv and system-wide."""
import shutil
import sys
from pathlib import Path


def get_ytdlp() -> str:
    """Return path to yt-dlp binary, preferring the current venv."""
    # 1. Same venv/bin as running Python
    venv_bin = Path(sys.executable).parent / "yt-dlp"
    if venv_bin.exists():
        return str(venv_bin)

    # 2. System PATH
    system = shutil.which("yt-dlp")
    if system:
        return system

    raise FileNotFoundError(
        "yt-dlp not found. Install with: pip install yt-dlp"
    )
