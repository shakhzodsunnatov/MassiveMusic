# MassivMusicBot Setup

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

Also install ffmpeg (needed for MP3 conversion):
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/download.html and add to PATH

## 2. Get a FREE Last.fm API key

1. Go to: https://www.last.fm/api/account/create
2. Sign up (free)
3. Create an API account — fill any name/description
4. Copy your **API key**

## 3. Configure

Edit `config.json`:
```json
{
  "lastfm_api_key": "PASTE_YOUR_KEY_HERE",
  "download_dir": "downloads",
  "usb_path": "D:\\",
  "max_similar_per_seed": 5,
  "audio_quality": "320",
  "audio_format": "mp3"
}
```

- `usb_path` on Windows: `D:\\` or `E:\\`
- `usb_path` on macOS: `/Volumes/USB` (replace USB with your drive name)
- `max_similar_per_seed`: how many similar songs to find per seed song

## 4. Add your seed songs

Edit `data/seed_songs.txt`:
```
Aziz Aliev - Sevgilim
Munisa Rizayeva - Yolgizman
Shahlo Agzamova - Yor-Yor
```
One song per line, format: `Artist - Song Title`

## 5. Run

```bash
# Download only your seed songs
python bot.py

# Download seeds + auto-find similar songs
python bot.py --expand

# Download seeds + similar + copy to USB automatically
python bot.py --expand --usb D:\

# Limit total songs (e.g. 50 songs max)
python bot.py --expand --count 50

# Limit and copy to USB
python bot.py --expand --count 100 --usb D:\
```

## How "Continue" works

1. Add your 10 songs to `data/seed_songs.txt`
2. Run: `python bot.py --expand`
3. Bot finds ~5-10 similar songs per seed automatically
4. Already downloaded songs are **never re-downloaded** (tracked in `downloads/downloaded.json`)
5. Add more seeds anytime and re-run — only new songs download

## File structure on USB

```
USB/
  Aziz Aliev/
    Aziz Aliev - Sevgilim.mp3
    Aziz Aliev - Dilnoza.mp3
  Munisa Rizayeva/
    Munisa Rizayeva - Yolgizman.mp3
  ...
```
