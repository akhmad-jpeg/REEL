# 🎵 REEL v2.0.2

**A powerful Python-based music downloader with smart metadata matching and batch processing capabilities.**

Download high-quality audio from YouTube with automatic Spotify metadata, album artwork, and lyrics embedding.

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run REEL
python reel.py

# 3. Configure Spotify API (Settings → Option 2)
# Get free credentials at: https://developer.spotify.com/dashboard

# 4. Start downloading!
```

---

## ✨ Features

### 🎯 Smart Downloads
- **Intelligent Matching** - Finds exact audio versions using duration verification (±15s tolerance)
- **Clean Track Names** - Automatically removes YouTube suffixes and featuring artists for better matching
- **Multiple Search Strategies** - Tries 3 different query patterns for best results
- **Music Video Filtering** - Automatically skips music videos, downloads audio only

### 📊 Full Metadata
- **Complete ID3 Tags** - Track name, artist, album, year, disc/track numbers
- **High-Quality Artwork** - Embeds album covers from Spotify
- **Lyrics Support** - Optional Genius API integration (unsynchronized lyrics)
- **Clean Filenames** - `Track Name - Artist Name.mp3` format

### 🔄 Batch Processing
- **CSV Import** - Download from spreadsheets (Exportify, TuneMyMusic, custom)
- **TXT URLs** - Batch download from URL lists
- **Spotify Albums** - Download entire albums by ID, URL, or search
- **Spotify Playlists** - Download entire playlists with previews
- **YouTube Playlists** - Download full YouTube playlists

### 🎨 User Experience
- **Preview Before Download** - See track info and confirm before downloading
- **Selective Removal** - Remove unwanted tracks from batch operations
- **Progress Indicators** - Real-time download progress
- **Failed Download Logs** - Detailed logs for troubleshooting
- **Duplicate Detection** - Skips already downloaded files
- **Colorful Interface** - Clear, organized terminal UI

---

## 📋 Requirements

### System Requirements
- **Python 3.8+**
- **FFmpeg** (for audio conversion)
- **5+ Mbps internet connection** (recommended)
- **~3-5 MB per track** storage space

### Required APIs (Free)
- **Spotify API** - For metadata (REQUIRED)
- **Genius API** - For lyrics (OPTIONAL)

Get credentials at:
- Spotify: https://developer.spotify.com/dashboard
- Genius: https://genius.com/api-clients

---

## 🚀 Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install yt-dlp spotipy lyricsgenius mutagen requests colorama
```

### Step 2: Install FFmpeg

**Windows:**
```bash
choco install ffmpeg
```
Or download from: https://www.gyan.dev/ffmpeg/builds/

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Linux (Fedora):**
```bash
sudo dnf install ffmpeg
```

### Step 3: Configure API Credentials

**Method 1: In-App Configuration (Easiest)**
```bash
python reel.py
# Select Option 8 → Settings
# Select Option 2 → Configure Spotify API
# Enter your Client ID and Client Secret
```

**Method 2: Environment Variables (Recommended)**

**Windows:**
```bash
setx SPOTIFY_CLIENT_ID "your_client_id_here"
setx SPOTIFY_CLIENT_SECRET "your_client_secret_here"
setx GENIUS_TOKEN "your_genius_token_here"
```

**macOS/Linux:**
```bash
export SPOTIFY_CLIENT_ID="your_client_id_here"
export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
export GENIUS_TOKEN="your_genius_token_here"
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

---

## 📖 Usage Guide

### Main Menu

```
╔════════════════════════════════════════╗
║              REEL v2.0.2               ║
╚════════════════════════════════════════╝

1. Search & Download Track      - Search by track and artist name
2. Download from URL            - Direct YouTube/SoundCloud URL
3. CSV Import                   - Batch download from spreadsheet
4. URLs from TXT                - Batch download from URL list
5. Spotify Album                - Download entire album
6. Spotify Playlist             - Download entire playlist
7. YouTube Playlist             - Download YouTube playlist
8. Settings                     - Configure paths and API keys
9. Exit
```

---

### Option 1: Search & Download Track

Search for any track by name and artist.

**Example:**
```
Select [1-9]: 1
Track: Blinding Lights
Artist: The Weeknd

[GOOD MATCH] Blinding Lights by The Weeknd (score: 135)
[PREVIEW]
  Track: Blinding Lights
  Artist: The Weeknd
  Album: After Hours (2020)
Download? [Y/N]: y

[BEST MATCH] The Weeknd - Blinding Lights (Official Audio) (200s, Δ0s, score: 1400)
[DOWNLOADED] Converting to MP3...
[✓] Lyrics embedded
[SUCCESS] Blinding Lights - The Weeknd.mp3
```

**Downloads to:** `Music Library/Singles/`

---

### Option 2: Download from URL

Download directly from YouTube, SoundCloud, or any yt-dlp supported URL.

**Supported URLs:**
- YouTube videos/music
- SoundCloud tracks
- Bandcamp tracks
- 1000+ other sites (via yt-dlp)

**Example:**
```
Select [1-9]: 2
URL: https://youtu.be/4NRXx6U8ABQ

[INFO] Extracting info...

============================================================
URL PREVIEW
============================================================
Track: Blinding Lights
Artist: The Weeknd
Duration: 3:20
Source: The Weeknd
============================================================

Download this track? [Y/N]: y

[INFO] Parsed: Blinding Lights by The Weeknd
[GOOD MATCH] Blinding Lights by The Weeknd (score: 135)
[INFO] Using Spotify metadata
[SUCCESS] Blinding Lights - The Weeknd.mp3
```

**Features:**
- ✅ Shows preview before downloading
- ✅ Extracts artist/track from video title
- ✅ Searches for Spotify metadata
- ✅ Falls back to YouTube thumbnail if no Spotify match

**Downloads to:** `Music Library/Singles/`

---

### Option 3: CSV Import

Import tracks from spreadsheets. Supports multiple CSV formats.

**Supported Formats:**
- ✅ **Exportify** (Spotify playlist export)
- ✅ **TuneMyMusic** (multi-platform export)
- ✅ **Custom CSV** (any format with track/artist columns)

**CSV Column Names (case-insensitive):**
- **Track:** `Track Name`, `Track name`, `track`, `Track`, `name`, `Name`
- **Artist:** `Artist Name(s)`, `Artist Name`, `Artist name`, `Artist`, `artist`

**Example CSV:**
```csv
Track Name,Artist
Blinding Lights,The Weeknd
God's Plan,Drake
Circles,Post Malone
```

**Example Usage:**
```
Select [1-9]: 3
CSV path: my_playlist.csv

[INFO] Detected CSV columns: Track Name, Artist
[INFO] Fetching metadata for 3 tracks...

============================================================
CSV PREVIEW - my_playlist
============================================================
[1] The Weeknd - Blinding Lights (After Hours, 2020)
[2] Drake - God's Plan (Scorpion, 2018)
[3] Post Malone - Circles (Hollywood's Bleeding, 2019)

Remove tracks (comma-separated, Enter for none): 
Download 3 tracks? [Y/N]: y

[1/3] The Weeknd - Blinding Lights
[SUCCESS] Blinding Lights - The Weeknd.mp3

[2/3] Drake - God's Plan
[SUCCESS] God's Plan - Drake.mp3

[3/3] Post Malone - Circles
[SUCCESS] Circles - Post Malone.mp3

[SUCCESS] All downloads completed!
```

**Special Handling:**
- **TuneMyMusic Format** - Automatically parses "Artist - Track" from track name column when artist column is empty
- **YouTube Suffixes** - Removes "(Official Video)", "[Official Audio]", etc.
- **Featuring Artists** - Removes "feat.", "ft.", "[with ...]" for better matching

**Downloads to:** `Music Library/CSV Imports/[CSV Filename]/`

---

### Option 4: URLs from TXT

Download multiple URLs from a text file.

**TXT Format:**
```
https://youtu.be/video1
https://youtu.be/video2
https://youtu.be/video3
```

**Example:**
```
Select [1-9]: 4
TXT path: urls.txt

[INFO] Extracting info from 3 URLs...

============================================================
TXT PREVIEW - urls
============================================================
[1] The Weeknd - Blinding Lights
[2] Drake - God's Plan
[3] Post Malone - Circles

Remove URLs (comma-separated numbers, Enter for none):
Download 3 videos? [Y/N]: y
```

**Downloads to:** `Music Library/URLs TXT/[TXT Filename]/`

---

### Option 5: Spotify Album

Download entire albums from Spotify.

**Input Methods:**
1. **Album URL:** `https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj`
2. **Album ID:** `4yP0hdKOZPNshxUOjY0cZj`
3. **Search:** Album name + artist name

**Example (URL/ID):**
```
Select [1-9]: 5
Album ID/URL or search name: https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj

============================================================
SPOTIFY ALBUM PREVIEW
============================================================
Album: After Hours
Artist: The Weeknd
Year: 2020
Tracks: 14

[1] Alone Again
[2] Too Late
[3] Hardest To Love
...

Remove tracks (comma-separated, Enter for none):
Download 14 tracks? [Y/N]: y
```

**Example (Search):**
```
Select [1-9]: 5
Album ID/URL or search name: After Hours
Artist: The Weeknd

Found 5 albums. Select one:
[1] After Hours - The Weeknd (2020) [14 tracks]
[2] After Hours (Deluxe) - The Weeknd (2020) [17 tracks]
...

Select album [1-5]: 1
```

**Downloads to:** `Music Library/Albums/[Album Name]/`

---

### Option 6: Spotify Playlist

Download entire Spotify playlists (public only).

**Input Methods:**
1. **Playlist URL:** `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`
2. **Playlist ID:** `37i9dQZF1DXcBWIGoYBM5M`

**Example:**
```
Select [1-9]: 6
Playlist ID/URL: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

============================================================
SPOTIFY PLAYLIST PREVIEW - Today's Top Hits (50 tracks)
============================================================
[1] Artist - Track Name
[2] Artist - Track Name
...

Remove tracks (comma-separated, Enter for none):
Download 50 tracks? [Y/N]: y
```

**Downloads to:** `Music Library/Spotify Playlists/[Playlist Name]/`

---

### Option 7: YouTube Playlist

Download entire YouTube playlists.

**Example:**
```
Select [1-9]: 7
Playlist URL: https://www.youtube.com/playlist?list=...

[INFO] Extracting playlist info...

============================================================
YOUTUBE PLAYLIST PREVIEW - My Playlist (25 videos)
============================================================
[1] Artist - Track Name
[2] Artist - Track Name
...

Remove videos (comma-separated, Enter for none):
Download 25 videos? [Y/N]: y
```

**Downloads to:** `Music Library/YouTube Playlists/[Playlist Name]/`

---

### Option 8: Settings

Configure REEL settings and API credentials.

**Settings Menu:**
```
1. Change library path
2. Configure Spotify API
3. Configure Genius API (Optional)
4. Show directory structure
5. Back to main menu
```

**Current Settings:**
```
Library: C:\Users\User\Music Library
Spotify: ✓ Configured
Genius: ✗ Not configured
```

---

## 📁 Directory Structure

```
Music Library/
├── Singles/                    # Single track downloads (Options 1, 2)
├── Albums/                     # Spotify album downloads (Option 5)
│   └── [Album Name]/
├── CSV Imports/                # CSV batch downloads (Option 3)
│   └── [CSV Filename]/
│       ├── Track1.mp3
│       ├── Track2.mp3
│       └── _FAILED_DOWNLOADS_[name].txt
├── URLs TXT/                   # TXT file batch downloads (Option 4)
│   └── [TXT Filename]/
├── Spotify Playlists/          # Playlist downloads (Option 6)
│   └── [Playlist Name]/
└── YouTube Playlists/          # YouTube playlist downloads (Option 7)
    └── [Playlist Name]/
```

---

## 🎯 Download Quality & Format

| Aspect | Details |
|--------|---------|
| **Format** | MP3 |
| **Quality** | Best available (typically 320kbps VBR) |
| **Metadata** | Full ID3v2 tags |
| **Artwork** | High-resolution album covers |
| **Lyrics** | Unsynchronized lyrics (if Genius configured) |
| **Naming** | `Track Name - Artist Name.mp3` |

**Embedded Metadata:**
- Title (TIT2)
- Artist (TPE1)
- Album (TALB)
- Album Artist (TPE2)
- Year (TDRC)
- Track Number (TRCK)
- Disc Number (TPOS)
- Album Artwork (APIC)
- Lyrics (USLT) - if Genius configured

---

## 🔧 Advanced Features

### Smart Search Algorithm

REEL uses a sophisticated scoring system to find the best match:

**Search Queries (in order):**
1. `{track} {artist} official audio`
2. `{track} {artist} audio`
3. `{track} {artist} lyrics`

**Scoring Factors:**
- Duration match (within ±15 seconds)
- Title keyword matching
- "Audio" vs "Video" in title
- Channel name matching
- Video length optimization

**Scoring Weights:**
- Duration match: +1000 points
- Title match: +200 points per keyword
- "Audio" in title: +300 points
- "Music Video" in title: -400 points

### Track Name Cleanup

Automatically removes common YouTube patterns:

**Removed Patterns:**
- `(Official Video)`, `[Official Video]`
- `(Official Audio)`, `[Official Audio]`
- `(Official Music Video)`
- `(Lyrics)`, `(Lyric Video)`
- `(Visualizer)`, `(Official Visualizer)`
- `(HD)`, `(4K)`, `(Live)`

**Featuring Artist Removal:**
- `feat. Artist`, `ft. Artist`
- `featuring Artist`
- `(feat. Artist)`, `[feat. Artist]`
- `(ft. Artist)`, `[ft. Artist]`
- `[with Artist]`

**Example:**
```
Input:  "Drake - God's Plan (feat. Future) [Official Music Video]"
Output: "God's Plan" by "Drake"
```

### Failed Downloads Logging

All batch operations generate detailed failure logs:

**Log Location:** `_FAILED_DOWNLOADS_[name].txt`

**Log Contents:**
```
Failed Downloads - my_playlist
Time: 2026-01-17 14:30:00
Total: 3

Track: Obscure Track Name
Artist: Unknown Artist
Reason: No YouTube match
------------------------------------------------------------
Track: Another Track
Artist: Another Artist
Reason: Duration mismatch (expected 180s, found 240s)
------------------------------------------------------------
```

Use logs to manually search for failed tracks or adjust search terms.

---

## 🐛 Troubleshooting

### Common Issues

#### "Spotify API credentials not configured"
**Solution:** 
1. Go to https://developer.spotify.com/dashboard
2. Create a free app
3. Copy Client ID and Client Secret
4. Run REEL → Settings → Configure Spotify API

#### "HTTP Error 403: Forbidden"
**Cause:** YouTube temporarily blocked the request  
**Solution:**
- Wait 10-15 minutes and try again
- Use a VPN to change your IP
- Try during off-peak hours

#### "No match found"
**Cause:** Song not available on YouTube or metadata mismatch  
**Solution:**
- Use Option 2 with a direct YouTube URL
- Try different spelling or artist name
- Check if track is region-locked

#### "FFmpeg not found"
**Cause:** FFmpeg not installed or not in PATH  
**Solution:**
- Follow installation instructions for your OS
- Verify with: `ffmpeg -version`
- Add FFmpeg to system PATH

#### Downloads are slow
**Cause:** Internet speed or YouTube throttling  
**Solution:**
- Close bandwidth-heavy applications
- Try during off-peak hours
- Check your internet speed (need 5+ Mbps)

#### Some tracks show [NO MATCH]
**Cause:** Track name has unusual formatting or isn't on Spotify  
**Solution:**
- Track will still download with basic metadata
- YouTube thumbnail will be used as artwork
- Edit metadata manually after download if needed

---

## ⚡ Performance Tips

1. **Use Your Own API Credentials**
   - Avoid rate limits
   - Better performance
   - More reliable

2. **Stable Internet Connection**
   - 5+ Mbps recommended
   - Wired connection preferred
   - Close streaming services during downloads

3. **Keep yt-dlp Updated**
   ```bash
   pip install --upgrade yt-dlp
   ```

4. **Use SSD Storage**
   - Faster file operations
   - Better for batch downloads

5. **Batch Operations**
   - CSV/TXT imports are more efficient than individual downloads
   - Downloads run sequentially to avoid rate limits

---

## 📊 CSV Format Guide

### Supported CSV Formats

#### 1. Exportify (Spotify Export)

Export your Spotify playlists at: https://exportify.net/

**Columns:** `Track Name`, `Artist Name(s)`, `Album Name`, etc.

**Example:**
```csv
Track URI,Track Name,Artist Name(s),Album Name,...
spotify:track:123,Blinding Lights,The Weeknd,After Hours,...
```

#### 2. TuneMyMusic (Multi-Platform)

Export from any platform at: https://tunemymusic.com/

**Format 1 - Standard:**
```csv
Track name,Artist name,Album,Playlist name,Type,ISRC
Blinding Lights,The Weeknd,After Hours,My Playlist,track,USUG12000123
```

**Format 2 - Combined (Artist in track name):**
```csv
Track name,Artist name,Album,Playlist name,Type,ISRC
The Weeknd - Blinding Lights,,,My Playlist,Playlist,
Drake - God's Plan,,,My Playlist,Playlist,
```

**Note:** REEL automatically detects and parses "Artist - Track" format when artist column is empty!

#### 3. Custom CSV

Create your own CSV with any of these column names:

**Track Columns:** `Track Name`, `Track name`, `track`, `Track`, `name`, `Name`  
**Artist Columns:** `Artist Name(s)`, `Artist Name`, `Artist name`, `Artist`, `artist`

**Minimal Example:**
```csv
Track Name,Artist
Blinding Lights,The Weeknd
God's Plan,Drake
Circles,Post Malone
```

---

## 🔒 Privacy & Security

### API Credentials
- Never share your API credentials
- Store in environment variables (recommended)
- Config file is local only (not synced)
- No credentials are sent to third parties

### Downloaded Content
- All files stored locally
- No cloud uploads
- Complete privacy

### Legal Compliance
- This tool is for personal use only
- Download only content you have rights to
- Respect copyright laws in your jurisdiction
- Support artists through official channels

---

## 📄 License

**Personal Use License**

This software is provided for personal, non-commercial use only. You may:
- ✅ Use for personal music library management
- ✅ Download content you have rights to access
- ✅ Modify for your own use

You may not:
- ❌ Distribute downloaded content
- ❌ Use for commercial purposes
- ❌ Share API credentials
- ❌ Violate copyright laws

**Disclaimer:** The author is not responsible for any misuse of this software. Users must comply with all applicable laws and respect intellectual property rights.

See LICENSE.txt for full terms.

---

## 🤝 Contributing

REEL is currently a personal project. Feel free to fork and modify for your own use!

**If you find REEL useful:**
- Star the repository
- Share with friends (for personal use)
- Support the artists whose music you download

---

## 🙏 Credits & Dependencies

Built with amazing open-source tools:

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - YouTube downloader (Unlicense)
- **[Spotipy](https://github.com/plamere/spotipy)** - Spotify API client (MIT)
- **[Mutagen](https://github.com/quodlibet/mutagen)** - Audio metadata editor (GPL-2.0)
- **[LyricsGenius](https://github.com/johnwmillr/LyricsGenius)** - Genius API client (MIT)
- **[FFmpeg](https://ffmpeg.org/)** - Audio/video converter (LGPL/GPL)
- **[Colorama](https://github.com/tartley/colorama)** - Terminal colors (BSD)
- **[Requests](https://github.com/psf/requests)** - HTTP library (Apache 2.0)

Special thanks to the open-source community! 🎉

---

## 📞 Support

### Getting Help

1. **Check Documentation**
   - README.md (this file)
   - INSTALL.md
   - QUICKSTART.md
   - CSV_FORMAT_GUIDE.md

2. **Review Logs**
   - Failed download logs in output directories
   - Check for specific error messages

3. **Verify Setup**
   - Python 3.8+ installed
   - All dependencies installed
   - FFmpeg in PATH
   - API credentials configured

4. **Common Solutions**
   - Update yt-dlp: `pip install --upgrade yt-dlp`
   - Restart terminal after installing FFmpeg
   - Check internet connection
   - Wait if rate-limited (10-15 minutes)

---

## 🎓 FAQ

**Q: Is this legal?**  
A: This tool downloads publicly available audio. Use responsibly and comply with all applicable laws in your jurisdiction. Download only content you have rights to access.

**Q: Why do I need Spotify API credentials?**  
A: To get accurate metadata (track names, artists, albums, artwork) for proper file tagging. The API is free and requires no credit card.

**Q: Can I download private Spotify playlists?**  
A: No, only public playlists are accessible through the free Spotify API.

**Q: How much storage do I need?**  
A: Each track is ~3-5 MB. A 12-track album is ~40-60 MB. A 50-track playlist is ~150-250 MB.

**Q: Why do some downloads fail?**  
A: Common reasons include: duration mismatch, content not available, region restrictions, or temporary YouTube rate limits. Check the failed downloads log for details.

**Q: Can I use this with Apple Music/Tidal/Deezer?**  
A: REEL uses Spotify API for metadata only. It downloads audio from YouTube, so it works regardless of which streaming service you use.

**Q: Does this download from Spotify directly?**  
A: No, Spotify streams are DRM-protected. REEL uses Spotify only for metadata (track info, artwork) and downloads audio from YouTube.

**Q: What quality will I get?**  
A: Best available from YouTube, typically 128-320kbps MP3. Actual quality depends on what's available for each track.

**Q: Can I edit the metadata after download?**  
A: Yes! Files have standard ID3 tags that can be edited with any music player (iTunes, MusicBee, foobar2000, etc.).

**Q: Will this work on my country/region?**  
A: REEL works worldwide, but some content may be region-locked by YouTube. Use a VPN if needed.

---

## 🚀 What's New in v2.0.2

See CHANGELOG.md for complete version history.

**Latest Updates:**
- ✅ Fixed CSV import for TuneMyMusic format
- ✅ Added URL preview for Option 2
- ✅ Improved track name cleanup
- ✅ Enhanced featuring artist removal
- ✅ Better error messages and debugging
- ✅ Automatic parsing of "Artist - Track" format

---

**Made with ❤️ for music lovers everywhere**

**Version:** 2.0.2  
**Release Date:** January 17, 2026  
**Status:** Stable  

---

**Enjoy your music! 🎵**
