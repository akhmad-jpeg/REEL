import os
import csv
import re
import sys
import subprocess
import warnings
import requests
import time

import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.exceptions
import lyricsgenius

from mutagen.id3 import (
    ID3, TIT2, TALB, TPE1, TPE2,
    TRCK, TPOS, TDRC, APIC, USLT, ID3NoHeaderError
)

# Try to import colorama for Windows color support
try:
    from colorama import init as colorama_init, Fore, Style, Back
    colorama_init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama not installed
    COLORS_AVAILABLE = False
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = LIGHTWHITE_EX = LIGHTGREEN_EX = LIGHTCYAN_EX = LIGHTYELLOW_EX = LIGHTMAGENTA_EX = ""
    class Style:
        BRIGHT = RESET_ALL = ""
    class Back:
        BLACK = ""

warnings.filterwarnings("ignore")

# ======================= UTILITIES =======================

def clean_path(p):
    """Clean and normalize file paths"""
    return os.path.abspath(p.strip().strip('"').strip("'"))

def clean_name(t):
    """Remove invalid filename characters"""
    return re.sub(r'[<>:"/\\|?*]', '', t).strip()

def audio_duration_seconds(path):
    """Get audio file duration using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
        return float(result.stdout.strip())
    except Exception:
        return 0

def wait_for_file_ready(path, timeout=10):
    """Wait for file to finish writing"""
    start = time.time()
    last_size = -1

    while time.time() - start < timeout:
        if not os.path.exists(path):
            time.sleep(0.2)
            continue

        size = os.path.getsize(path)
        if size > 0 and size == last_size:
            return True

        last_size = size
        time.sleep(0.3)

    return False

# ===================== YT-DLP LOGGER =====================

def yt_logger():
    """Silent logger for yt-dlp"""
    class Logger:
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    return Logger()

# ======================== DIRECTORIES ====================

BASE = os.path.join(os.getcwd(), "Music Library")

def set_dirs(new_base=None):
    """Initialize or update directory structure"""
    global BASE, DIRS
    if new_base:
        BASE = clean_path(new_base)

    DIRS = {
        "SINGLE": os.path.join(BASE, "Singles"),
        "ALBUM": os.path.join(BASE, "Albums"),
        "CSV": os.path.join(BASE, "CSV Imports"),
        "URLS_TXT": os.path.join(BASE, "URLs TXT"),
        "PLAYLIST": os.path.join(BASE, "Spotify Playlists")
    }

    for d in DIRS.values():
        os.makedirs(d, exist_ok=True)

set_dirs()

# ========================= AUTH ==========================

def init_spotify():
    """Initialize Spotify client with credentials from environment"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        # Return None, will be initialized later when credentials are provided
        return None
    
    try:
        return spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
        )
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize Spotify client: {e}")
        return None

def init_genius():
    """Initialize Genius client with credentials from environment"""
    token = os.getenv("GENIUS_TOKEN")
    
    if not token:
        # Genius is optional, so just silently create client
        token = ""
    
    try:
        return lyricsgenius.Genius(
            token,
            skip_non_songs=True,
            remove_section_headers=True
        )
    except:
        return None

sp = init_spotify()
genius = init_genius()

# ======================= PROGRESS ========================

def progress_hook(d):
    """Display download progress"""
    title = d.get("info_dict", {}).get("title", "Unknown")
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        done = d.get("downloaded_bytes", 0)
        if total:
            pct = done / total * 100
            print(f"\r[Downloading] {title[:40]:40} | {pct:5.1f}%", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r[Processing] {title[:60]}".ljust(90))

# ====================== SPOTIFY META =====================

def build_meta(t):
    """Build metadata dictionary from Spotify track object"""
    a = t["album"]
    return {
        "track": t["name"],
        "artist": ", ".join(x["name"] for x in t["artists"]),
        "album": a["name"],
        "album_artist": a["artists"][0]["name"],
        "track_no": t["track_number"],
        "disc_no": t["disc_number"],
        "year": a["release_date"][:4],
        "art": a["images"][0]["url"] if a["images"] else None,
        "duration": t["duration_ms"] / 1000 
    }


def spotify_meta(track, artist):
    """Search Spotify for track metadata with improved matching"""
    if not sp:
        print(f"\n[ERROR] Spotify API not configured. Please configure in Settings (Option 7)")
        return None
    
    try:
        q = f'{track} {artist}'
        r = sp.search(q=q, type="track", limit=10)
        items = r["tracks"]["items"]

        if not items:
            return None

        # 1️⃣ Exact title match
        for item in items:
            if item["name"].lower() == track.lower():
                return build_meta(item)

        # 2️⃣ Featured artist match (partial name in title + artist in credits)
        for item in items:
            artists = [a["name"].lower() for a in item["artists"]]
            if track.lower() in item["name"].lower() and any(artist.lower() in a for a in artists):
                return build_meta(item)

        # 3️⃣ Final fallback (Spotify best match)
        return build_meta(items[0])

    except Exception as e:
        print(f"\n[ERROR] Spotify API: {e}")
        return None

def spotify_album(album_id):
    """Get all tracks from a Spotify album"""
    if not sp:
        print(f"\n[ERROR] Spotify API not configured. Please configure in Settings (Option 7)")
        return None, None
    
    try:
        print(f"\n[INFO] Fetching album ID: {album_id}")
        album = sp.album(album_id)
        tracks = []
        for track in album["tracks"]["items"]:
            tracks.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"]
            })
        return tracks, album["name"]
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            print(f"\n[ERROR] Album not found. The album may be:")
            print("  - Not available in your region")
            print("  - Deleted")
            print("  - Invalid ID")
        elif e.http_status == 403:
            print(f"\n[ERROR] Access forbidden.")
        else:
            print(f"\n[ERROR] Spotify API error ({e.http_status}): {e.msg}")
        return None, None
    except Exception as e:
        print(f"\n[ERROR] Spotify Album: {e}")
        return None, None

def search_spotify_album(album_name, artist_name):
    """Search for album by name and artist, returns album ID if found"""
    if not sp:
        print(f"\n[ERROR] Spotify API not configured. Please configure in Settings (Option 7)")
        return None
    
    try:
        query = f"album:{album_name} artist:{artist_name}"
        print(f"\n[INFO] Searching for: {album_name} by {artist_name}")
        
        results = sp.search(q=query, type="album", limit=10)
        albums = results["albums"]["items"]
        
        if not albums:
            print(f"\n[ERROR] No albums found matching '{album_name}' by '{artist_name}'")
            return None
        
        # Show all matches for user to choose
        print("\n========== ALBUM SEARCH RESULTS ==========")
        for i, album in enumerate(albums, 1):
            artists = ", ".join([a["name"] for a in album["artists"]])
            year = album["release_date"][:4] if album.get("release_date") else "Unknown"
            total_tracks = album.get("total_tracks", "?")
            print(f"[{i}] {album['name']} - {artists} ({year}) [{total_tracks} tracks]")
        
        # Let user select
        while True:
            choice = input(f"\nSelect album [1-{len(albums)}] or 0 to cancel: ").strip()
            if choice == "0":
                return None
            if choice.isdigit() and 1 <= int(choice) <= len(albums):
                selected = albums[int(choice) - 1]
                print(f"\n[INFO] Selected: {selected['name']} - {selected['artists'][0]['name']}")
                return selected["id"]
            else:
                print(f"[ERROR] Invalid choice. Enter a number between 1 and {len(albums)}")
                
    except Exception as e:
        print(f"\n[ERROR] Search failed: {e}")
        return None

def spotify_playlist(playlist_id):
    """Get all tracks from a Spotify playlist"""
    if not sp:
        print(f"\n[ERROR] Spotify API not configured. Please configure in Settings (Option 7)")
        return None, None
    
    try:
        print(f"\n[INFO] Fetching playlist ID: {playlist_id}")
        results = sp.playlist_tracks(playlist_id)
        tracks = []
        for item in results["items"]:
            if item["track"]:
                track = item["track"]
                tracks.append({
                    "name": track["name"],
                    "artist": track["artists"][0]["name"]
                })
        
        playlist = sp.playlist(playlist_id)
        return tracks, playlist["name"]
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            print(f"\n[ERROR] Playlist not found. The playlist may be:")
            print("  - Private (you need the playlist owner's permission)")
            print("  - Deleted")
            print("  - Invalid ID")
        elif e.http_status == 403:
            print(f"\n[ERROR] Access forbidden. The playlist is private.")
        else:
            print(f"\n[ERROR] Spotify API error ({e.http_status}): {e.msg}")
        return None, None
    except Exception as e:
        print(f"\n[ERROR] Spotify Playlist: {e}")
        return None, None

# ========================= TAGGING =======================

def get_lyrics(track, artist):
    """Fetch lyrics from Genius API if available"""
    if not genius:
        return None
    
    try:
        song = genius.search_song(track, artist)
        if song:
            return song.lyrics
        return None
    except Exception as e:
        print(f"[INFO] Could not fetch lyrics: {e}")
        return None

def embed(path, meta, lyrics=None):
    """Embed ID3 tags and album art into MP3 file"""
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()

    tags["TIT2"] = TIT2(encoding=3, text=meta["track"])
    tags["TPE1"] = TPE1(encoding=3, text=meta["artist"])
    tags["TALB"] = TALB(encoding=3, text=meta["album"])
    tags["TPE2"] = TPE2(encoding=3, text=meta["album_artist"])
    tags["TRCK"] = TRCK(encoding=3, text=str(meta["track_no"]))
    tags["TPOS"] = TPOS(encoding=3, text=str(meta["disc_no"]))
    tags["TDRC"] = TDRC(encoding=3, text=meta["year"])

    # Embed lyrics if available
    if lyrics:
        from mutagen.id3 import USLT
        tags["USLT"] = USLT(encoding=3, lang='eng', desc='', text=lyrics)
        print(f"[✓] Lyrics embedded")

    # Download and embed album art
    if meta.get("art"):
        try:
            img = requests.get(meta["art"], timeout=10).content
            tags.delall("APIC")
            tags.add(APIC(encoding=3, mime="image/jpeg", type=3, data=img))
        except Exception:
            pass

    tags.save(path)

# ====================== CSV PARSING ======================

TRACK_KEYS = {"track name", "track", "title", "name", "song name"}
ARTIST_KEYS = {"artist", "artist name", "artist name(s)", "artists", "artist(s)"}

def extract_track_artist(row):
    """Extract track and artist from CSV row with flexible column names"""
    r = {k.lower().strip(): str(v).strip() for k, v in row.items() if k}

    track = next((r[k] for k in TRACK_KEYS if k in r and r[k]), None)
    artist = next((r[k] for k in ARTIST_KEYS if k in r and r[k]), None)

    # Handle "Artist - Track" format
    if (not artist or not track) and track and " - " in track:
        left, right = track.split(" - ", 1)
        artist = artist or left.strip()
        track = right.strip()

    # Use only primary artist if multiple
    if artist and "," in artist:
        artist = artist.split(",")[0].strip()

    return (track, artist) if track and artist else (None, None)

def process_csv(path):
    """Process CSV file and download all tracks"""
    path = clean_path(path)
    
    if not os.path.exists(path):
        print(f"\n[ERROR] File not found: {path}")
        return
    
    csv_name = clean_name(os.path.splitext(os.path.basename(path))[0])
    out = os.path.join(DIRS["CSV"], csv_name)
    os.makedirs(out, exist_ok=True)

    tracks = []
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t, a = extract_track_artist(row)
                if t and a:
                    tracks.append((t, a))
    except Exception as e:
        print(f"\n[ERROR] Failed to read CSV: {e}")
        return

    if not tracks:
        print("\n[ERROR] No usable tracks found in CSV.")
        return

    # Fetch metadata for preview
    print(f"\n[INFO] Fetching metadata for {len(tracks)} tracks...")
    tracks_with_meta = []
    
    for i, (t, a) in enumerate(tracks, 1):
        print(f"\r[{i}/{len(tracks)}] Fetching metadata...", end="", flush=True)
        meta = spotify_meta(t, a)
        if meta:
            tracks_with_meta.append((t, a, meta))
        else:
            tracks_with_meta.append((t, a, None))
    
    print()  # New line after progress

    print("\n========== CSV PREVIEW ==========")
    for i, (t, a, meta) in enumerate(tracks_with_meta, 1):
        if meta:
            print(f"[{i}] {meta['artist']} - {meta['track']} ({meta['album']}, {meta['year']})")
        else:
            print(f"[{i}] {a} - {t} [NO METADATA FOUND]")

    remove = input("\nTracks to remove (comma-separated numbers, Enter for none): ").strip()
    if remove:
        try:
            bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
            tracks_with_meta = [t for i, t in enumerate(tracks_with_meta) if i not in bad]
        except ValueError:
            print("\n[WARNING] Invalid input, proceeding with all tracks")

    if not tracks_with_meta:
        print("\n[ERROR] No tracks remaining after removal")
        return

    if input(f"\nDownload {len(tracks_with_meta)} tracks? [Y/N]: ").strip().lower() != "y":
        return

    print(f"\n[INFO] Downloading to: {out}\n")
    
    # Track failed downloads
    failed_downloads = []
    
    for i, (t, a, meta) in enumerate(tracks_with_meta, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(tracks_with_meta)}] Processing: {a} - {t}")
        print('='*60)
        result = download_track(t, a, out, ask=False)
        
        if not result["success"]:
            failed_downloads.append({
                "track": result["track"],
                "artist": result["artist"],
                "reason": result["reason"]
            })
    
    # Write failed downloads log
    if failed_downloads:
        log_file = os.path.join(out, f"_FAILED_DOWNLOADS_{csv_name}.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed Downloads Log - {csv_name}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Failed: {len(failed_downloads)}/{len(tracks_with_meta)}\n")
            f.write("="*60 + "\n\n")
            
            for item in failed_downloads:
                f.write(f"Track: {item['track']}\n")
                f.write(f"Artist: {item['artist']}\n")
                f.write(f"Reason: {item['reason']}\n")
                f.write("-"*60 + "\n")
        
        print(f"\n{'='*60}")
        print(f"[WARNING] {len(failed_downloads)} track(s) failed to download")
        print(f"[INFO] Failed downloads log saved to:")
        print(f"       {log_file}")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print(f"[SUCCESS] All tracks downloaded successfully!")
        print('='*60)

# ==================== DOWNLOAD TRACK =====================

def download_track(track, artist, out_dir=None, ask=True):
    """Download track from YouTube with Spotify metadata"""
    meta = spotify_meta(track, artist)
    if not meta:
        print(f"\n[SKIP] Could not find metadata for: {artist} - {track}")
        return {"success": False, "reason": "No Spotify metadata found", "track": track, "artist": artist}

    expected = int(meta["duration"])
    tolerance = 15  # Increased from 6 to 15 seconds for better matching

    if ask:
        print("\n[PREVIEW]")
        print(f"  Track: {meta['track']}")
        print(f"  Artist: {meta['artist']}")
        print(f"  Album: {meta['album']} ({meta['year']})")
        print(f"  Duration: {expected}s")

        if input("\nDownload? [Y/N]: ").strip().lower() != "y":
            return {"success": False, "reason": "User cancelled", "track": track, "artist": artist}

    out_dir = out_dir or DIRS["SINGLE"]
    base = clean_name(f"{meta['track']} - {meta['artist']}")
    final = os.path.join(out_dir, base + ".mp3")
    
    # Skip if already exists
    if os.path.exists(final):
        print(f"\n[SKIP] File already exists: {base}.mp3")
        return {"success": True, "reason": "Already exists", "track": meta['track'], "artist": meta['artist']}
    
    outtmpl = os.path.join(out_dir, base + ".%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "logger": yt_logger(),
        "noplaylist": True,
        "progress_hooks": [progress_hook],

        # 🔑 CRITICAL 403 FIXES
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/"
        },
        "force_ipv4": True,
        "concurrent_fragment_downloads": 1,

        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Try multiple search strategies
            search_queries = [
                f"ytsearch15:{meta['track']} {meta['artist']} official audio",  # Increased to 15 results
                f"ytsearch15:{meta['track']} {meta['artist']} audio",
                f"ytsearch15:{meta['track']} {meta['artist']} lyrics",
            ]
            
            for search_query in search_queries:
                info = ydl.extract_info(search_query, download=False)

                if not info or "entries" not in info:
                    continue

                for entry in info["entries"]:
                    dur = entry.get("duration")
                    title = entry.get("title", "")
                    
                    if not dur:
                        continue
                    
                    # 🚫 SKIP MUSIC VIDEOS
                    video_keywords = ["music video", "official video", "official music video", "(official video)"]
                    if any(keyword in title.lower() for keyword in video_keywords):
                        print(f"[SKIP] Music video detected: {title}")
                        continue

                    if abs(dur - expected) <= tolerance:
                        print(f"\n[MATCH] {entry['title']} ({dur}s)")
                        try:
                            ydl.download([entry["webpage_url"]])
                            
                            # Verify file was created
                            if os.path.exists(final):
                                # Fetch lyrics if Genius API is configured
                                lyrics = None
                                if genius:
                                    print(f"[INFO] Fetching lyrics...")
                                    lyrics = get_lyrics(meta['track'], meta['artist'])
                                
                                embed(final, meta, lyrics)
                                print(f"[SUCCESS] Downloaded: {base}.mp3")
                                return {"success": True, "reason": "Downloaded successfully", "track": meta['track'], "artist": meta['artist']}
                            
                        except yt_dlp.utils.DownloadError as e:
                            print(f"\n[ERROR] Download blocked: {e}")
                            print("[INFO] Trying next match...")
                            continue
                    else:
                        if abs(dur - expected) <= tolerance + 10:  # Show near misses
                            print(f"[SKIP] Near miss: {entry['title']} ({dur}s vs {expected}s expected, diff: {abs(dur - expected)}s)")

            print(f"\n[FAIL] Could not find official audio for: {track}")
            return {"success": False, "reason": f"No match found (expected duration: {expected}s)", "track": track, "artist": artist}
            
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        return {"success": False, "reason": f"Error: {str(e)}", "track": track, "artist": artist}

# ==================== URL DOWNLOAD =======================

def download_url(url, out_dir=None):
    """Download audio from direct URL with metadata matching and duration check"""
    out_dir = out_dir or DIRS["SINGLE"]  # Changed from URLS to SINGLE
    
    # First, extract info to get title and artist
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            print(f"\n[INFO] Extracting video information...")
            info = ydl.extract_info(url, download=False)
            
            if not info:
                print("[ERROR] Could not extract video information")
                return False
            
            video_title = info.get("title", "")
            video_duration = info.get("duration", 0)
            
            # 🚫 CHECK FOR MUSIC VIDEO
            video_keywords = ["music video", "official video", "official music video", "(official video)", "[official video]"]
            if any(keyword in video_title.lower() for keyword in video_keywords):
                print(f"\n[WARNING] This appears to be a MUSIC VIDEO: {video_title}")
                print("[WARNING] Music videos may have intro/outro and different audio quality")
                if input("\nContinue anyway? [Y/N]: ").strip().lower() != "y":
                    return False
            
            print(f"[INFO] Video: {video_title}")
            print(f"[INFO] Duration: {video_duration}s")
            
            # Try to parse artist and track from title
            # Common formats: "Artist - Track", "Track - Artist", "Artist: Track"
            track, artist = None, None
            
            # Try different separators
            for sep in [" - ", " – ", ": ", " | "]:
                if sep in video_title:
                    parts = video_title.split(sep, 1)
                    # Assume first part is artist, second is track
                    artist = parts[0].strip()
                    track = parts[1].strip()
                    # Remove common suffixes
                    for suffix in ["(Official Audio)", "(Official Video)", "(Lyrics)", "(Audio)", "[Official]"]:
                        track = track.replace(suffix, "").strip()
                        artist = artist.replace(suffix, "").strip()
                    break
            
            # If we couldn't parse, ask user
            if not track or not artist:
                print("\n[INFO] Could not auto-detect track and artist")
                track = input("Enter track name: ").strip()
                artist = input("Enter artist name: ").strip()
                
                if not track or not artist:
                    print("[ERROR] Track and artist are required")
                    return False
            
            # Get Spotify metadata for proper naming and tagging
            meta = spotify_meta(track, artist)
            
            if not meta:
                print(f"\n[WARNING] Could not find Spotify metadata")
                print(f"[INFO] Using video title for naming")
                base = clean_name(f"{track} - {artist}")
                
                # Create minimal metadata
                meta = {
                    "track": track,
                    "artist": artist,
                    "album": "Unknown Album",
                    "album_artist": artist,
                    "track_no": 1,
                    "disc_no": 1,
                    "year": "2024",
                    "art": None,
                    "duration": video_duration
                }
            else:
                base = clean_name(f"{meta['track']} - {meta['artist']}")
                expected_duration = int(meta["duration"])
                tolerance = 10
                
                # Check duration match
                if abs(video_duration - expected_duration) > tolerance:
                    print(f"\n[WARNING] Duration mismatch!")
                    print(f"  Video: {video_duration}s")
                    print(f"  Expected: {expected_duration}s")
                    print(f"  Difference: {abs(video_duration - expected_duration)}s")
                    
                    if input("\nContinue anyway? [Y/N]: ").strip().lower() != "y":
                        return False
            
            final = os.path.join(out_dir, base + ".mp3")
            
            # Skip if already exists
            if os.path.exists(final):
                print(f"\n[SKIP] File already exists: {base}.mp3")
                return True
            
            print(f"\n[INFO] Will save as: {base}.mp3")
            
            if input("\nDownload? [Y/N]: ").strip().lower() != "y":
                return False
            
            outtmpl = os.path.join(out_dir, base + ".%(ext)s")
            
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": outtmpl,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [progress_hook],
                
                # 🔑 CRITICAL 403 FIXES
                "http_headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.youtube.com/"
                },
                "force_ipv4": True,
                "concurrent_fragment_downloads": 1,
                
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"\n[INFO] Downloading...")
                ydl.download([url])
                
                # Verify file was created
                if os.path.exists(final):
                    # Fetch lyrics if Genius API is configured
                    lyrics = None
                    if genius:
                        print(f"[INFO] Fetching lyrics...")
                        lyrics = get_lyrics(meta['track'], meta['artist'])
                    
                    # Add metadata tags
                    embed(final, meta, lyrics)
                    print(f"\n[SUCCESS] Downloaded: {base}.mp3")
                    print(f"[INFO] Location: {out_dir}")
                    return True
                else:
                    print(f"\n[ERROR] File was not created")
                    return False
                    
    except Exception as e:
        print(f"\n[ERROR] Failed to download URL: {e}")
        return False

# ==================== TXT PROCESSING =====================

def process_urls_txt(path):
    """Process text file containing URLs (one per line)"""
    path = clean_path(path)
    
    if not os.path.exists(path):
        print(f"\n[ERROR] File not found: {path}")
        return
    
    # Create output directory based on txt filename
    txt_name = clean_name(os.path.splitext(os.path.basename(path))[0])
    out_dir = os.path.join(DIRS["URLS_TXT"], txt_name)
    os.makedirs(out_dir, exist_ok=True)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not urls:
            print("\n[ERROR] No URLs found in file")
            return
        
        # Extract info for all URLs first (for preview)
        print(f"\n[INFO] Extracting information from {len(urls)} URLs...")
        tracks_info = []
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"\r[{i}/{len(urls)}] Processing URL info...", end="", flush=True)
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        video_title = info.get("title", "Unknown")
                        video_duration = info.get("duration", 0)
                        
                        # Try to parse artist and track from title
                        track, artist = None, None
                        for sep in [" - ", " – ", ": ", " | "]:
                            if sep in video_title:
                                parts = video_title.split(sep, 1)
                                artist = parts[0].strip()
                                track = parts[1].strip()
                                # Remove common suffixes
                                for suffix in ["(Official Audio)", "(Official Video)", "(Lyrics)", "(Audio)", "[Official]", "(Official Music Video)"]:
                                    track = track.replace(suffix, "").strip()
                                    artist = artist.replace(suffix, "").strip()
                                break
                        
                        if not track or not artist:
                            track = video_title
                            artist = "Unknown Artist"
                        
                        tracks_info.append({
                            "url": url,
                            "track": track,
                            "artist": artist,
                            "duration": video_duration,
                            "title": video_title
                        })
            except Exception as e:
                print(f"\n[WARNING] Could not extract info from URL {i}: {e}")
                tracks_info.append({
                    "url": url,
                    "track": f"Unknown Track {i}",
                    "artist": "Unknown Artist",
                    "duration": 0,
                    "title": "Failed to extract",
                    "error": str(e)
                })
                continue
        
        print()  # New line after progress
        
        if not tracks_info:
            print("\n[ERROR] Could not extract info from any URLs")
            return
        
        # Show preview
        print("\n========== URLS TXT PREVIEW ==========")
        for i, info in enumerate(tracks_info, 1):
            if "error" in info:
                print(f"[{i}] ERROR: {info['title']}")
            else:
                print(f"[{i}] {info['artist']} - {info['track']} ({info['duration']}s)")
        
        # Option to remove tracks
        remove = input("\nTracks to remove (comma-separated numbers, Enter for none): ").strip()
        if remove:
            try:
                bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
                tracks_info = [t for i, t in enumerate(tracks_info) if i not in bad]
            except ValueError:
                print("\n[WARNING] Invalid input, proceeding with all tracks")
        
        if not tracks_info:
            print("\n[ERROR] No tracks remaining after removal")
            return
        
        if input(f"\nDownload {len(tracks_info)} tracks? [Y/N]: ").strip().lower() != "y":
            return
        
        print(f"\n[INFO] Downloading to: {out_dir}\n")
        
        # Track failed downloads
        failed_downloads = []
        
        # Download all tracks without asking Y/N for each
        for i, info in enumerate(tracks_info, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(tracks_info)}] {info['artist']} - {info['track']}")
            print('='*60)
            
            if "error" in info:
                failed_downloads.append({
                    "track": info['track'],
                    "artist": info['artist'],
                    "url": info['url'],
                    "reason": f"Failed to extract info: {info['error']}"
                })
                print(f"[SKIP] Could not extract info from URL")
                continue
            
            result = download_url_direct(info["url"], info["track"], info["artist"], out_dir)
            
            if not result:
                failed_downloads.append({
                    "track": info['track'],
                    "artist": info['artist'],
                    "url": info['url'],
                    "reason": "Download failed"
                })
        
        # Write failed downloads log
        if failed_downloads:
            log_file = os.path.join(out_dir, f"_FAILED_DOWNLOADS_{txt_name}.txt")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Failed Downloads Log - {txt_name}\n")
                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Failed: {len(failed_downloads)}/{len(tracks_info)}\n")
                f.write("="*60 + "\n\n")
                
                for item in failed_downloads:
                    f.write(f"Track: {item['track']}\n")
                    f.write(f"Artist: {item['artist']}\n")
                    f.write(f"URL: {item['url']}\n")
                    f.write(f"Reason: {item['reason']}\n")
                    f.write("-"*60 + "\n")
            
            print(f"\n{'='*60}")
            print(f"[WARNING] {len(failed_downloads)} track(s) failed to download")
            print(f"[INFO] Failed downloads log saved to:")
            print(f"       {log_file}")
            print('='*60)
        else:
            print(f"\n{'='*60}")
            print(f"[SUCCESS] All tracks downloaded successfully!")
            print('='*60)
            
    except Exception as e:
        print(f"\n[ERROR] Failed to process file: {e}")


def download_url_direct(url, track, artist, out_dir):
    """Download from URL without preview prompts (used by process_urls_txt)"""
    # Get Spotify metadata for proper naming and tagging
    meta = spotify_meta(track, artist)
    
    if not meta:
        print(f"[WARNING] Could not find Spotify metadata, using parsed names")
        base = clean_name(f"{track} - {artist}")
        meta = {
            "track": track,
            "artist": artist,
            "album": "Unknown Album",
            "album_artist": artist,
            "track_no": 1,
            "disc_no": 1,
            "year": "2024",
            "art": None,
            "duration": 0
        }
    else:
        base = clean_name(f"{meta['track']} - {meta['artist']}")
    
    final = os.path.join(out_dir, base + ".mp3")
    
    # Skip if already exists
    if os.path.exists(final):
        print(f"[SKIP] File already exists: {base}.mp3")
        return True
    
    outtmpl = os.path.join(out_dir, base + ".%(ext)s")
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
        
        # 🔑 CRITICAL 403 FIXES + NO MUSIC VIDEOS
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/"
        },
        "force_ipv4": True,
        "concurrent_fragment_downloads": 1,
        
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0",
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            if os.path.exists(final):
                # Fetch lyrics if Genius API is configured
                lyrics = None
                if genius:
                    print(f"[INFO] Fetching lyrics...")
                    lyrics = get_lyrics(meta['track'], meta['artist'])
                
                embed(final, meta, lyrics)
                print(f"[SUCCESS] Downloaded: {base}.mp3")
                return True
            else:
                print(f"[ERROR] File was not created")
                return False
                
    except Exception as e:
        print(f"[ERROR] Failed to download: {e}")
        return False

# ==================== ALBUM DOWNLOAD =====================

def download_album(album_input=None):
    """Download entire Spotify album - supports name+artist, ID, or URL"""
    
    # If no input provided, ask user for input method
    if not album_input:
        print("\n========== SPOTIFY ALBUM DOWNLOAD ==========")
        print("1. Search by Album Name + Artist")
        print("2. Enter Album ID")
        print("3. Enter Spotify URL")
        
        choice = input("\nSelect input method [1-3]: ").strip()
        
        if choice == "1":
            # Search by name and artist
            album_name = input("\nAlbum name: ").strip()
            artist_name = input("Artist name: ").strip()
            
            if not album_name or not artist_name:
                print("\n[ERROR] Both album name and artist name are required")
                return
            
            album_id = search_spotify_album(album_name, artist_name)
            if not album_id:
                return
                
        elif choice == "2":
            # Direct ID input
            album_id = input("\nEnter Album ID: ").strip()
            if not album_id:
                print("\n[ERROR] Album ID is required")
                return
                
        elif choice == "3":
            # URL input
            album_url = input("\nEnter Spotify Album URL: ").strip()
            if not album_url:
                print("\n[ERROR] URL is required")
                return
            
            if "spotify.com/album/" in album_url:
                album_id = album_url.split("album/")[1].split("?")[0]
            else:
                print("\n[ERROR] Invalid Spotify album URL")
                return
        else:
            print("\n[ERROR] Invalid selection")
            return
    else:
        # Direct input provided (legacy support)
        if "spotify.com/album/" in album_input:
            album_id = album_input.split("album/")[1].split("?")[0]
        else:
            album_id = album_input
    
    # Fetch album tracks
    tracks, album_name = spotify_album(album_id)
    
    if not tracks:
        print("\n[ERROR] Could not fetch album")
        return
    
    print(f"\n========== SPOTIFY ALBUM PREVIEW ==========")
    print(f"Album: {album_name}")
    print(f"Tracks: {len(tracks)}\n")
    
    for i, track in enumerate(tracks, 1):
        print(f"[{i}] {track['artist']} - {track['name']}")
    
    # Option to remove tracks
    remove = input("\nTracks to remove (comma-separated numbers, Enter for none): ").strip()
    if remove:
        try:
            bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
            tracks = [t for i, t in enumerate(tracks) if i not in bad]
        except ValueError:
            print("\n[WARNING] Invalid input, proceeding with all tracks")
    
    if not tracks:
        print("\n[ERROR] No tracks remaining after removal")
        return
    
    if input(f"\nDownload {len(tracks)} tracks? [Y/N]: ").strip().lower() != "y":
        return
    
    out_dir = os.path.join(DIRS["ALBUM"], clean_name(album_name))
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"\n[INFO] Downloading to: {out_dir}\n")
    
    # Track failed downloads
    failed_downloads = []
    
    for i, track in enumerate(tracks, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(tracks)}] {track['artist']} - {track['name']}")
        print('='*60)
        result = download_track(track["name"], track["artist"], out_dir, ask=False)
        
        if not result["success"]:
            failed_downloads.append({
                "track": result["track"],
                "artist": result["artist"],
                "reason": result["reason"]
            })
    
    # Write failed downloads log
    if failed_downloads:
        log_file = os.path.join(out_dir, f"_FAILED_DOWNLOADS_{clean_name(album_name)}.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed Downloads Log - {album_name}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Failed: {len(failed_downloads)}/{len(tracks)}\n")
            f.write("="*60 + "\n\n")
            
            for item in failed_downloads:
                f.write(f"Track: {item['track']}\n")
                f.write(f"Artist: {item['artist']}\n")
                f.write(f"Reason: {item['reason']}\n")
                f.write("-"*60 + "\n")
        
        print(f"\n{'='*60}")
        print(f"[WARNING] {len(failed_downloads)} track(s) failed to download")
        print(f"[INFO] Failed downloads log saved to:")
        print(f"       {log_file}")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print(f"[SUCCESS] All tracks downloaded successfully!")
        print('='*60)

# ==================== PLAYLIST DOWNLOAD ==================

def download_playlist(playlist_id_or_url):
    """Download entire Spotify playlist"""
    # Extract playlist ID from URL if needed
    if "spotify.com/playlist/" in playlist_id_or_url:
        playlist_id = playlist_id_or_url.split("playlist/")[1].split("?")[0]
    else:
        playlist_id = playlist_id_or_url
    
    tracks, playlist_name = spotify_playlist(playlist_id)
    
    if not tracks:
        print("\n[ERROR] Could not fetch playlist")
        return
    
    print(f"\n========== SPOTIFY PLAYLIST PREVIEW ==========")
    print(f"Playlist: {playlist_name}")
    print(f"Tracks: {len(tracks)}\n")
    
    for i, track in enumerate(tracks, 1):
        print(f"[{i}] {track['artist']} - {track['name']}")
    
    # Option to remove tracks
    remove = input("\nTracks to remove (comma-separated numbers, Enter for none): ").strip()
    if remove:
        try:
            bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
            tracks = [t for i, t in enumerate(tracks) if i not in bad]
        except ValueError:
            print("\n[WARNING] Invalid input, proceeding with all tracks")
    
    if not tracks:
        print("\n[ERROR] No tracks remaining after removal")
        return
    
    if input(f"\nDownload {len(tracks)} tracks? [Y/N]: ").strip().lower() != "y":
        return
    
    out_dir = os.path.join(DIRS["PLAYLIST"], clean_name(playlist_name))
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"\n[INFO] Downloading to: {out_dir}\n")
    
    # Track failed downloads
    failed_downloads = []
    
    for i, track in enumerate(tracks, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(tracks)}] {track['artist']} - {track['name']}")
        print('='*60)
        result = download_track(track["name"], track["artist"], out_dir, ask=False)
        
        if not result["success"]:
            failed_downloads.append({
                "track": result["track"],
                "artist": result["artist"],
                "reason": result["reason"]
            })
    
    # Write failed downloads log
    if failed_downloads:
        log_file = os.path.join(out_dir, f"_FAILED_DOWNLOADS_{clean_name(playlist_name)}.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed Downloads Log - {playlist_name}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Failed: {len(failed_downloads)}/{len(tracks)}\n")
            f.write("="*60 + "\n\n")
            
            for item in failed_downloads:
                f.write(f"Track: {item['track']}\n")
                f.write(f"Artist: {item['artist']}\n")
                f.write(f"Reason: {item['reason']}\n")
                f.write("-"*60 + "\n")
        
        print(f"\n{'='*60}")
        print(f"[WARNING] {len(failed_downloads)} track(s) failed to download")
        print(f"[INFO] Failed downloads log saved to:")
        print(f"       {log_file}")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print(f"[SUCCESS] All tracks downloaded successfully!")
        print('='*60)

# ======================== SETTINGS =======================

def save_config():
    """Save current configuration to a file"""
    config = {
        "library_path": BASE,
        "spotify_client_id": os.getenv("SPOTIFY_CLIENT_ID", ""),
        "spotify_client_secret": os.getenv("SPOTIFY_CLIENT_SECRET", ""),
        "genius_token": os.getenv("GENIUS_TOKEN", "")
    }
    
    config_file = os.path.join(os.getcwd(), "reel_config.txt")
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("# REEL Configuration\n")
            f.write(f"# Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"LIBRARY_PATH={config['library_path']}\n")
            f.write(f"SPOTIFY_CLIENT_ID={config['spotify_client_id']}\n")
            f.write(f"SPOTIFY_CLIENT_SECRET={config['spotify_client_secret']}\n")
            f.write(f"GENIUS_TOKEN={config['genius_token']}\n")
        print(f"\n[SUCCESS] Configuration saved to: {config_file}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to save configuration: {e}")
        return False

def load_config():
    """Load configuration from file if it exists"""
    config_file = os.path.join(os.getcwd(), "reel_config.txt")
    
    if not os.path.exists(config_file):
        return None
    
    config = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        return config
    except Exception:
        return None

def configure_spotify():
    """Configure Spotify API credentials"""
    print("\n========== SPOTIFY API CONFIGURATION ==========")
    print("\nTo get your Spotify API credentials:")
    print("1. Go to: https://developer.spotify.com/dashboard")
    print("2. Log in or create an account")
    print("3. Click 'Create App'")
    print("4. Fill in the form (any name/description)")
    print("5. Copy your Client ID and Client Secret")
    print("\n" + "="*50)
    
    current_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    current_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    
    if current_id:
        print(f"\nCurrent Client ID: {current_id[:20]}...")
        print(f"Current Client Secret: {current_secret[:20]}...")
    else:
        print("\nNo credentials configured yet")
    
    print("\nLeave blank to keep current values.")
    
    client_id = input("\nEnter Spotify Client ID: ").strip()
    client_secret = input("Enter Spotify Client Secret: ").strip()
    
    if client_id and client_secret:
        # Set environment variables for current session
        os.environ["SPOTIFY_CLIENT_ID"] = client_id
        os.environ["SPOTIFY_CLIENT_SECRET"] = client_secret
        
        # Reinitialize Spotify client
        global sp
        sp = init_spotify()
        
        # Test the credentials
        print("\n[INFO] Testing credentials...")
        try:
            sp.search(q="test", type="track", limit=1)
            print("[SUCCESS] Spotify credentials are valid!")
            
            # Save to config file
            save_config()
            
            print("\n" + "="*50)
            print("IMPORTANT: To make these credentials permanent,")
            print("set them as environment variables:")
            print("\nWindows:")
            print(f'  setx SPOTIFY_CLIENT_ID "{client_id}"')
            print(f'  setx SPOTIFY_CLIENT_SECRET "{client_secret}"')
            print("\nmacOS/Linux:")
            print(f'  export SPOTIFY_CLIENT_ID="{client_id}"')
            print(f'  export SPOTIFY_CLIENT_SECRET="{client_secret}"')
            print("="*50)
            
        except Exception as e:
            print(f"[ERROR] Invalid credentials: {e}")
            print("[INFO] Reverting to previous credentials...")
            # Revert to previous values
            if current_id:
                os.environ["SPOTIFY_CLIENT_ID"] = current_id
                os.environ["SPOTIFY_CLIENT_SECRET"] = current_secret
            sp = init_spotify()
    else:
        print("\n[INFO] No changes made to Spotify credentials")

def configure_genius():
    """Configure Genius API credentials"""
    print("\n========== GENIUS API CONFIGURATION ==========")
    print("\nTo get your Genius API token:")
    print("1. Go to: https://genius.com/api-clients")
    print("2. Log in or create an account")
    print("3. Click 'New API Client'")
    print("4. Fill in the form (any name/description)")
    print("5. Copy your 'Client Access Token'")
    print("\n" + "="*50)
    
    current_token = os.getenv("GENIUS_TOKEN", "")
    
    if current_token:
        print(f"\nCurrent Token: {current_token[:30]}...")
    else:
        print("\nNo token configured yet")
    
    print("\nLeave blank to keep current value.")
    print("Note: Genius API is currently not used by the downloader.")
    
    token = input("\nEnter Genius Access Token: ").strip()
    
    if token:
        # Set environment variable for current session
        os.environ["GENIUS_TOKEN"] = token
        
        # Reinitialize Genius client
        global genius
        genius = init_genius()
        
        print("[SUCCESS] Genius token updated!")
        
        # Save to config file
        save_config()
        
        print("\n" + "="*50)
        print("IMPORTANT: To make this token permanent,")
        print("set it as an environment variable:")
        print("\nWindows:")
        print(f'  setx GENIUS_TOKEN "{token}"')
        print("\nmacOS/Linux:")
        print(f'  export GENIUS_TOKEN="{token}"')
        print("="*50)
    else:
        print("\n[INFO] No changes made to Genius token")

def settings_menu():
    """Configure application settings"""
    while True:
        print("\n========== SETTINGS ==========")
        print(f"Current library path: {BASE}")
        
        # Show current API status
        current_spotify_id = os.getenv("SPOTIFY_CLIENT_ID", "")
        if current_spotify_id:
            print("Spotify API: ✅ Configured")
        else:
            print("Spotify API: ❌ Not configured")
        
        current_genius = os.getenv("GENIUS_TOKEN", "")
        if current_genius:
            print("Genius API: ✅ Configured")
        else:
            print("Genius API: ❌ Not configured (optional)")
        
        print("\n1. Change library path")
        print("2. Configure Spotify API credentials")
        print("3. Configure Genius API token")
        print("4. Show directory structure")
        print("5. Save current configuration")
        print("6. Back to main menu")
        
        choice = input("\nSelect [1-6]: ").strip()
        
        if choice == "1":
            new_path = input("\nEnter new library path: ").strip()
            if new_path:
                try:
                    new_path = clean_path(new_path)
                    set_dirs(new_path)
                    save_config()
                    print(f"\n[SUCCESS] Library path updated to: {BASE}")
                except Exception as e:
                    print(f"\n[ERROR] Invalid path: {e}")
            else:
                print("\n[INFO] No changes made")
                
        elif choice == "2":
            configure_spotify()
            
        elif choice == "3":
            configure_genius()
            
        elif choice == "4":
            print("\n========== DIRECTORY STRUCTURE ==========")
            for name, path in DIRS.items():
                exists = "✅" if os.path.exists(path) else "❌"
                print(f"{exists} {name:12} → {path}")
                
        elif choice == "5":
            save_config()
            
        elif choice == "6":
            break
            
        else:
            print("\n[ERROR] Invalid selection")

# ========================== MENU =========================

def menu():
    """Display main menu and handle user input"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}╔════════════════════════════════════════╗")
    print(f"{Fore.CYAN}{Style.BRIGHT}║{Fore.WHITE}              REEL v2.0                 {Fore.CYAN}║")
    print(f"{Fore.CYAN}{Style.BRIGHT}╚════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    print(f"{Fore.LIGHTGREEN_EX}1. {Fore.WHITE}Search & Download Track")
    print(f"{Fore.LIGHTGREEN_EX}2. {Fore.WHITE}Download from URL")
    print(f"{Fore.LIGHTCYAN_EX}3. {Fore.WHITE}CSV Import")
    print(f"{Fore.LIGHTCYAN_EX}4. {Fore.WHITE}URLs from TXT file")
    print(f"{Fore.LIGHTMAGENTA_EX}5. {Fore.WHITE}Download Spotify Album")
    print(f"{Fore.LIGHTMAGENTA_EX}6. {Fore.WHITE}Download Spotify Playlist")
    print(f"{Fore.LIGHTYELLOW_EX}7. {Fore.WHITE}Settings")
    print(f"{Fore.RED}8. {Fore.WHITE}Exit{Style.RESET_ALL}\n")

    try:
        c = input(f"{Fore.CYAN}Select [1-8]: {Style.RESET_ALL}").strip()

        if c == "1":
            print(f"\n{Fore.LIGHTGREEN_EX}═══ Search & Download Track ═══{Style.RESET_ALL}")
            track = input(f"{Fore.WHITE}Track name: {Style.RESET_ALL}").strip()
            artist = input(f"{Fore.WHITE}Artist name: {Style.RESET_ALL}").strip()
            if track and artist:
                download_track(track, artist)
            else:
                print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Both track and artist are required")
                
        elif c == "2":
            print(f"\n{Fore.LIGHTGREEN_EX}═══ Download from URL ═══{Style.RESET_ALL}")
            url = input(f"{Fore.WHITE}Enter URL: {Style.RESET_ALL}").strip()
            if url:
                download_url(url)
            else:
                print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} URL required")
                
        elif c == "3":
            print(f"\n{Fore.LIGHTCYAN_EX}═══ CSV Import ═══{Style.RESET_ALL}")
            path = input(f"{Fore.WHITE}CSV file path: {Style.RESET_ALL}").strip()
            if path:
                process_csv(path)
            else:
                print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Path required")
                
        elif c == "4":
            print(f"\n{Fore.LIGHTCYAN_EX}═══ URLs from TXT ═══{Style.RESET_ALL}")
            path = input(f"{Fore.WHITE}TXT file path (one URL per line): {Style.RESET_ALL}").strip()
            if path:
                process_urls_txt(path)
            else:
                print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Path required")
                
        elif c == "5":
            print(f"\n{Fore.LIGHTMAGENTA_EX}═══ Download Spotify Album ═══{Style.RESET_ALL}")
            download_album()  # Call without parameters to show input method selection
                
        elif c == "6":
            print(f"\n{Fore.LIGHTMAGENTA_EX}═══ Download Spotify Playlist ═══{Style.RESET_ALL}")
            playlist = input(f"{Fore.WHITE}Spotify Playlist ID or URL: {Style.RESET_ALL}").strip()
            if playlist:
                download_playlist(playlist)
            else:
                print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Playlist ID/URL required")
                
        elif c == "7":
            print(f"\n{Fore.LIGHTYELLOW_EX}═══ Settings ═══{Style.RESET_ALL}")
            settings_menu()
            
        elif c == "8":
            print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Exiting... Goodbye!")
            sys.exit(0)
            
        else:
            print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Invalid selection. Please choose 1-8")
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[INFO]{Style.RESET_ALL} Operation cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")

# =========================== RUN =========================

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f" {Fore.WHITE}REEL - Starting...")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # Try to load saved configuration
    config = load_config()
    if config:
        print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Loading saved configuration...")
        
        # Load library path
        if config.get("LIBRARY_PATH"):
            try:
                set_dirs(config["LIBRARY_PATH"])
                print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} Library path: {BASE}")
            except:
                pass
        
        # Load Spotify credentials
        if config.get("SPOTIFY_CLIENT_ID") and config.get("SPOTIFY_CLIENT_SECRET"):
            os.environ["SPOTIFY_CLIENT_ID"] = config["SPOTIFY_CLIENT_ID"]
            os.environ["SPOTIFY_CLIENT_SECRET"] = config["SPOTIFY_CLIENT_SECRET"]
            sp = init_spotify()
            if sp:
                print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} Spotify API: Credentials loaded")
            else:
                print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} Spotify API: Failed to initialize")
        else:
            sp = None
            print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} Spotify API: Not configured")
        
        # Load Genius token
        if config.get("GENIUS_TOKEN"):
            os.environ["GENIUS_TOKEN"] = config["GENIUS_TOKEN"]
            genius = init_genius()
            if genius:
                print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} Genius API: Token loaded (lyrics support enabled)")
    else:
        print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Library location: {BASE}")
        sp = init_spotify()
        if not sp:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'='*60}")
            print(f"{Fore.RED}⚠️  WARNING: Spotify API credentials not configured!")
            print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
            print(f"\n{Fore.WHITE}To use REEL, you need FREE Spotify API credentials.")
            print(f"\n{Fore.CYAN}How to get them (takes 2 minutes):{Style.RESET_ALL}")
            print(f"{Fore.WHITE}1. Go to: {Fore.LIGHTCYAN_EX}https://developer.spotify.com/dashboard")
            print(f"{Fore.WHITE}2. Log in (or create free account)")
            print(f"{Fore.WHITE}3. Click 'Create App'")
            print(f"{Fore.WHITE}4. Copy your Client ID and Client Secret")
            print(f"{Fore.WHITE}5. Go to Settings (Option 7) to configure them")
            print(f"\n{Fore.YELLOW}OR set environment variables:")
            print(f"{Fore.WHITE}  Windows: {Fore.LIGHTGREEN_EX}setx SPOTIFY_CLIENT_ID \"your_id\"")
            print(f"{Fore.WHITE}  macOS/Linux: {Fore.LIGHTGREEN_EX}export SPOTIFY_CLIENT_ID=\"your_id\"")
            print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} You can still access Settings to configure credentials")
    
    print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Press Ctrl+C at any time to cancel\n")
    
    try:
        while True:
            menu()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Shutdown complete. Goodbye!")
        sys.exit(0)
