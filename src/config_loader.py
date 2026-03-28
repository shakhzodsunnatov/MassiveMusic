import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_config() -> dict:
    config_path = ROOT / "config.json"
    if not config_path.exists():
        print("[ERROR] config.json not found. Copy config.json.example and fill in your settings.")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    required = ["lastfm_api_key", "download_dir"]
    for key in required:
        if not config.get(key):
            print(f"[ERROR] Missing required config key: {key}")
            sys.exit(1)

    if config["lastfm_api_key"] == "YOUR_LASTFM_API_KEY":
        print("[ERROR] Please set your Last.fm API key in config.json")
        print("  Get a free key at: https://www.last.fm/api/account/create")
        sys.exit(1)

    # Resolve download_dir relative to project root
    config["download_dir"] = str(ROOT / config["download_dir"])
    return config
