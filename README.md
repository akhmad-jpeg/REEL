![image alt](https://github.com/akhmad-jpeg/REEL/blob/main/REEL%20Windows/logo.png?raw=true)

# 🎵 REEL

A powerful Python-based music downloader that fetches high-quality audio from YouTube with proper metadata from Spotify.

## ⚠️ IMPORTANT: API Setup Required

**This app requires FREE Spotify API credentials to work.** You must set these up before using the downloader.

### Quick Setup (2 minutes):

1. Go to https://developer.spotify.com/dashboard
2. Log in (or create free account)
3. Click "Create App"
4. Enter any name/description
5. Redirect URL: https://localhost:8888/callback
6. Copy your Client ID and Client Secret
7. Run the app and go to Settings (Option 7) → Configure Spotify API

**That's it!** The API is 100% free, no credit card required.

---

## ✨ Features

- 🎯 **Smart Search**: Automatically finds the correct audio version with duration matching
- 🎨 **Full Metadata**: Embeds track name, artist, album, year, and artwork
- 📊 **Batch Downloads**: Import from CSV, TXT files, or entire Spotify albums/playlists
- 🚫 **No Music Videos**: Automatically filters out music videos, downloads audio only
- 📝 **Failed Downloads Log**: Creates detailed logs for tracks that couldn't be downloaded
- ⚙️ **Configurable**: Save your library path and API credentials
- 🔄 **Resume Support**: Skips already downloaded files

---

## 📋 Requirements

- **Python 3.8+**
- **FFmpeg** (for audio conversion)
- **Spotify API credentials** (free, required)

### Python Packages:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install yt-dlp spotipy lyricsgenius mutagen requests
```

### Install FFmpeg:

**Windows:**
```bash
choco install ffmpeg
```
Or download from: https://www.gyan.dev/ffmpeg/builds/

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

---

## 🚀 Quick Start

1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Spotify API credentials** (see setup instructions above)

3. **Run REEL:**
   ```bash
   python reel.py
   ```

4. **Configure Spotify API** (first time only):
   - Select Option 7 (Settings)
   - Select Option 2 (Configure Spotify API)
   - Enter your credentials

5. **Start downloading!**

---

## 📖 Usage

### Main Menu:
```
1. Search & Download Track      - Search for a single track
2. Download from URL            - Direct YouTube URL download
3. CSV Import                   - Batch download from CSV
4. URLs from TXT file           - Batch download from URL list
5. Download Spotify Album       - Get entire albums
6. Download Spotify Playlist    - Get entire playlists
7. Settings                     - Configure paths and API keys
8. Exit
```

### Example Workflows:

**Single Track:**
```
Select: 1
Track: God's Plan
Artist: Drake
[Downloads to: Music Library/Singles/]
```

**CSV Import:**
```
CSV format:
Track Name, Artist
God's Plan, Drake
Circles, Post Malone

[Shows preview, allows removing tracks, downloads all]
```

**Spotify Playlist:**
```
Select: 6
URL: https://open.spotify.com/playlist/...
[Shows all tracks, allows removing unwanted ones, downloads all]
```

---

## 📁 Directory Structure

```
Music Library/
├── Singles/                    # Single track downloads
├── Albums/                     # Spotify album downloads
│   └── [Album Name]/
├── CSV Imports/               # CSV batch downloads
│   └── [CSV Filename]/
├── URLs TXT/                  # TXT file batch downloads
│   └── [TXT Filename]/
└── Spotify Playlists/         # Playlist downloads
    └── [Playlist Name]/
```

---

## 🔧 Configuration

### Option 7 → Settings Menu:

1. **Change library path** - Customize download location
2. **Configure Spotify API** - Enter your credentials
3. **Configure Genius API** - Optional (for future features)
4. **Show directory structure** - View all folders
5. **Save configuration** - Persist your settings

Settings are saved to `reel_config.txt` and auto-load on startup.

### Environment Variables (Recommended):

**Windows:**
```bash
setx SPOTIFY_CLIENT_ID "your_client_id"
setx SPOTIFY_CLIENT_SECRET "your_client_secret"
```

**macOS/Linux:**
```bash
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"
```

---

## 📝 CSV Format

Your CSV can use any of these column names (case-insensitive):

**Track:** `track name`, `track`, `title`, `name`, `song name`
**Artist:** `artist`, `artist name`, `artist name(s)`, `artists`

Example CSV:
```csv
Track Name,Artist
God's Plan,Drake
Circles,Post Malone
Blinding Lights,The Weeknd
```

---

## 🎯 Download Quality

- **Format:** MP3
- **Quality:** Best available (typically 320kbps or VBR)
- **Metadata:** Complete ID3 tags (title, artist, album, year, artwork)
- **Naming:** `Track Name - Artist Name.mp3`

---

## 🐛 Troubleshooting

### "Spotify API credentials not configured"
- You need to set up free Spotify API credentials (see setup section)

### "HTTP Error 403: Forbidden"
- YouTube temporarily blocked the request
- Wait 10-15 minutes and try again
- Try using a VPN

### "No match found"
- The song might not be available on YouTube
- Try Option 2 with a direct URL
- Check the failed downloads log for details

### "FFmpeg not found"
- FFmpeg is not installed or not in PATH
- Follow installation instructions for your OS

### Failed Downloads
- Check the `_FAILED_DOWNLOADS_*.txt` file in the download folder
- Contains detailed reasons for each failure
- Use the log to manually search for failed tracks

---

## ⚡ Performance Tips

1. **Use your own Spotify API credentials** (no rate limits)
2. **Stable internet connection** (5+ Mbps recommended)
3. **Update yt-dlp regularly:** `pip install --upgrade yt-dlp`
4. **Close bandwidth-heavy apps** during downloads
5. **Use SSD** for faster file operations

---

## 📊 Features Comparison

| Feature | Single Track | CSV/TXT | Album/Playlist |
|---------|-------------|---------|----------------|
| Duration matching | ✅ ±15s | ✅ ±15s | ✅ ±15s |
| Music video filtering | ✅ | ✅ | ✅ |
| Full metadata | ✅ | ✅ | ✅ |
| Failed downloads log | ❌ | ✅ | ✅ |
| Preview before download | ✅ | ✅ | ✅ |
| Selective removal | ❌ | ✅ | ✅ |
| Batch processing | ❌ | ✅ | ✅ |

---

## 🎓 Advanced Usage

### Multiple Search Strategies:
The downloader tries 3 different search queries:
1. "{track} {artist} official audio"
2. "{track} {artist} audio"
3. "{track} {artist} lyrics"

### Duration Tolerance:
- **±15 seconds** for better matching
- Shows "near misses" that were close but didn't match

### Failed Downloads Logging:
All batch operations create detailed logs:
```
_FAILED_DOWNLOADS_[name].txt
```

Contains:
- Track and artist names
- Failure reason
- Expected duration
- Timestamp

---

## 📄 License

This project is for personal use only. Respect copyright laws and artist rights.

**Disclaimer:** This tool is for downloading legally available content only. The author is not responsible for any misuse of this software.

---

## 🤝 Contributing

This is a personal project inspired by SpotFetch, but feel free to fork and modify for your own use!

---

## ❓ FAQ

**Q: Is this legal?**
A: This tool downloads publicly available audio. Use responsibly and respect copyright laws.

**Q: Why do I need Spotify API credentials?**
A: To get accurate metadata (track names, artists, albums, artwork) for proper tagging.

**Q: Are the API credentials free?**
A: Yes! Both Spotify and Genius APIs are 100% free, no credit card required.

**Q: Can I download private Spotify playlists?**
A: No, only public playlists/albums are accessible through the free API.

**Q: Why do some downloads fail?**
A: Common reasons: duration mismatch, video not available, region-locked content, or temporary YouTube blocks.

**Q: How much storage do I need?**
A: Each song is ~3-5 MB. An album is ~40-60 MB, a 50-track playlist is ~150-250 MB.

---

## 🙏 Credits

Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [Spotipy](https://github.com/plamere/spotipy) - Spotify API client
- [Mutagen](https://github.com/quodlibet/mutagen) - Metadata editing
- [FFmpeg](https://ffmpeg.org/) - Audio conversion

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the failed downloads log
3. Make sure all requirements are installed
4. Verify your API credentials are configured

---

**Enjoy your music! 🎵**
