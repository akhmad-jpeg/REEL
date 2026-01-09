# 🎵 REEL - Quick Reference

## Installation
```bash
pip install -r requirements.txt
```

## First Run Setup
1. `python reel.py`
2. Go to Settings (7)
3. Configure Spotify API (2)
4. Done!

## Main Options

| # | Feature | Use Case |
|---|---------|----------|
| 1 | Search & Download | Single track |
| 2 | Download from URL | Direct YouTube link |
| 3 | CSV Import | Batch from spreadsheet |
| 4 | URLs TXT | Batch from URL list |
| 5 | Spotify Album | Entire album |
| 6 | Spotify Playlist | Entire playlist |
| 7 | Settings | Configure app |
| 8 | Exit | Close REEL |

## File Naming
```
Track Name - Artist Name.mp3
```

## Directory Structure
```
Music Library/
├── Singles/           # Options 1, 2
├── Albums/            # Option 5
├── CSV Imports/       # Option 3
├── URLs TXT/          # Option 4
└── Spotify Playlists/ # Option 6
```

## CSV Format
```csv
Track Name,Artist
STICK ,Dreamville
No Pole ,Don Toliver
```

## Common Commands

### Install
```bash
pip install yt-dlp spotipy mutagen requests lyricsgenius
```

### Update
```bash
pip install --upgrade yt-dlp
```

### Run
```bash
python reel.py
```

## Spotify API Setup (2 min)
1. https://developer.spotify.com/dashboard
2. Create App
3. Copy Client ID & Secret
4. Settings (7) → Configure Spotify (2)

## Environment Variables

**Windows:**
```bash
setx SPOTIFY_CLIENT_ID "your_id"
setx SPOTIFY_CLIENT_SECRET "your_secret"
```

**macOS/Linux:**
```bash
export SPOTIFY_CLIENT_ID="your_id"
export SPOTIFY_CLIENT_SECRET="your_secret"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No credentials | Settings → Configure Spotify |
| 403 Forbidden | Wait 15 min, try again |
| FFmpeg error | Install FFmpeg |
| Failed downloads | Check `_FAILED_DOWNLOADS_*.txt` |

## Quality Settings
- **Format:** MP3
- **Quality:** 320kbps (best available)
- **Tolerance:** ±15 seconds duration
- **Metadata:** Full ID3 tags + artwork

## Batch Operations
- Preview all tracks first
- Remove unwanted with numbers (e.g., "1,5,10")
- Single Y/N confirmation
- Auto-generates failure log

## Config File
**Location:** `reel_config.txt` (same directory)
**Auto-loads:** On every startup
**Contains:** Paths + API credentials

## Tips
✅ Use your own Spotify credentials (no limits)
✅ Keep yt-dlp updated
✅ Check failed downloads log
✅ Use CSV for large batches
✅ Stable internet = better results

## Quick Stats
- **Storage:** ~3-5 MB per song
- **Speed:** ~10-30 seconds per song
- **Success Rate:** ~85% (with proper setup)

---

**Need help?** Check README.md for full documentation.
