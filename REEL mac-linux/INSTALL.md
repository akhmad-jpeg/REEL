# 🎵 REEL - Installation Guide

## 📦 What's Included

This folder contains everything you need to run REEL:

```
REEL/
├── reel.py              # Main application
├── requirements.txt     # Python dependencies
├── run_reel.bat        # Windows launcher
├── run_reel.sh         # macOS/Linux launcher
├── README.md           # Full documentation
├── INSTALL.md          # This file
├── QUICKSTART.md       # Quick reference
└── ABOUT.md            # About REEL
```

---

## 🚀 Quick Installation (3 Steps)

### **Step 1: Install Python**

**Windows:**
1. Download: https://www.python.org/downloads/
2. Run installer
3. ✅ **CHECK "Add Python to PATH"** (important!)
4. Click "Install Now"

**macOS:**
```bash
brew install python3
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### **Step 2: Install FFmpeg**

**Windows:**
```bash
choco install ffmpeg
```
Or download: https://www.gyan.dev/ffmpeg/builds/
and make sure you add it to your environment variables

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### **Step 3: Install Python Packages**

**Option A: Automatic (Recommended)**
- Windows: Double-click `run_reel.bat`
- macOS/Linux: Run `./run_reel.sh`
- Choose "Y" when asked to install dependencies

**Option B: Manual**
```bash
pip install -r requirements.txt
```

---

## ✅ Verify Installation

Run these commands to check everything is installed:

```bash
# Check Python
python --version
# Should show: Python 3.8.x or higher

# Check FFmpeg
ffmpeg -version
# Should show FFmpeg version info

# Check packages
pip list | grep -E "yt-dlp|spotipy|mutagen"
# Should show all installed
```

---

## 🎯 First Run

### **Windows:**
1. Double-click `run_reel.bat`
2. Follow on-screen instructions

### **macOS/Linux:**
1. Open Terminal in REEL folder
2. Run: `./run_reel.sh`
3. Follow on-screen instructions

### **Manual (All Platforms):**
```bash
python reel.py
# or
python3 reel.py
```

---

## 🔑 Configure Spotify API (Required - First Time Only)

REEL needs **FREE** Spotify API credentials to work.

### **Get Your Credentials (2 minutes):**

1. Go to: https://developer.spotify.com/dashboard
2. Log in or create account (free)
3. Click **"Create App"**
4. Fill in:
   - App name: "REEL" (or any name)
   - App description: "Music downloader" (or anything)
   - Redirect URI: Leave default or https://localhost:8888/callback
5. Click **"Save"**
6. Copy your **Client ID** and **Client Secret**

### **In REEL:**
1. Start REEL
2. Select **7** (Settings)
3. Select **2** (Configure Spotify API)
4. Paste your Client ID
5. Paste your Client Secret
6. Done! ✅

Your settings are saved automatically and will work forever.

---

## 🎤 Configure Genius API (Optional - For Lyrics)

If you want lyrics embedded in your music:

1. Go to: https://genius.com/api-clients
2. Log in or create account
3. Click **"New API Client"**
4. Fill in any name/description
5. Copy your **Client Access Token**
6. In REEL: Settings (7) → Genius API (3)
7. Paste token

---

## 🐛 Troubleshooting

### **"Python is not recognized"**
- Python not installed or not in PATH
- Reinstall Python and check "Add to PATH"

### **"FFmpeg is not recognized"**
- FFmpeg not installed or not in PATH
- Follow installation instructions above

### **"No module named 'yt_dlp'"**
- Dependencies not installed
- Run: `pip install -r requirements.txt`

### **"Spotify API credentials not configured"**
- You need to configure Spotify API (see above)
- It's free and takes 2 minutes!

### **"Permission denied" (macOS/Linux)**
- Run: `chmod +x run_reel.sh`

### **Downloads fail with "403 Forbidden"**
- Temporary YouTube block
- Wait 10-15 minutes and try again
- Try using a VPN

### **"Can't find metadata"**
- Check your Spotify credentials are correct
- Try different search terms
- Song might not be on Spotify

---

## 📁 Where Are My Downloads?

Default location: `Music Library/` (created in REEL folder)

```
Music Library/
├── Singles/           # Single track downloads
├── Albums/            # Album downloads
├── CSV Imports/       # CSV batch downloads
├── URLs TXT/          # URL list downloads
└── Spotify Playlists/ # Playlist downloads
```

You can change this in Settings (Option 7).

---

## 🔄 Updating REEL

### **Update Python Packages:**
```bash
pip install --upgrade yt-dlp spotipy mutagen requests lyricsgenius
```

### **Update FFmpeg:**
- Windows: `choco upgrade ffmpeg`
- macOS: `brew upgrade ffmpeg`
- Linux: `sudo apt update && sudo apt upgrade ffmpeg`

**Tip:** Update yt-dlp regularly as YouTube changes frequently!

---

## 💡 Tips for Best Results

1. ✅ **Configure your own Spotify API** (no rate limits)
2. ✅ **Keep yt-dlp updated** (YouTube changes often)
3. ✅ **Use stable internet** (5+ Mbps recommended)
4. ✅ **Check failed download logs** (tells you why tracks failed)
5. ✅ **Use CSV for large batches** (preview and remove unwanted tracks)

---

## 📞 Need Help?

1. Check **README.md** for full documentation
2. Check **QUICKSTART.md** for quick reference
3. Check the troubleshooting section above
4. Review failed download logs in your download folders

---

##  You're Ready!

Run REEL and start downloading music! 🎵

**First time users:** Don't forget to configure Spotify API (Settings → Option 2)

Enjoy REEL! 
