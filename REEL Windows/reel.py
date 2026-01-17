import os, csv, re, sys, subprocess, warnings, requests, time
import yt_dlp, spotipy, lyricsgenius
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.exceptions
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, TRCK, TPOS, TDRC, APIC, USLT, ID3NoHeaderError

# Color support
try:
    from colorama import init as colorama_init, Fore, Style, Back
    colorama_init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = LIGHTWHITE_EX = LIGHTGREEN_EX = LIGHTCYAN_EX = LIGHTYELLOW_EX = LIGHTMAGENTA_EX = ""
    class Style:
        BRIGHT = RESET_ALL = ""
    class Back:
        BLACK = ""

warnings.filterwarnings("ignore")

# ========================= GLOBALS ===========================

BASE = os.path.join(os.path.expanduser("~"), "Music Library")
DIRS = {}

sp = None
genius = None

# ========================= HELPERS ===========================

def clean_name(s):
    """Clean string for filename"""
    return re.sub(r'[<>:"/\\|?*]', '', s).strip()

def clean_path(p):
    """Clean and expand path"""
    return os.path.abspath(os.path.expanduser(p.strip().strip('"').strip("'")))

class yt_logger:
    """Suppress yt-dlp logs and warnings"""
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
    def info(self, msg): pass

def progress_hook(d):
    """Show download progress"""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', 'N/A').strip()
        eta = d.get('_eta_str', 'N/A').strip()
        print(f"\r{Fore.CYAN}[DOWNLOADING]{Style.RESET_ALL} {percent} | Speed: {speed} | ETA: {eta}     ", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\r{Fore.GREEN}[DOWNLOADED]{Style.RESET_ALL} Converting to MP3...                    ", end='', flush=True)

def set_dirs(new_base=None):
    """Initialize directory structure"""
    global BASE, DIRS
    if new_base:
        BASE = clean_path(new_base)
    
    DIRS = {
        "SINGLE": os.path.join(BASE, "Singles"),
        "ALBUM": os.path.join(BASE, "Albums"),
        "CSV": os.path.join(BASE, "CSV Imports"),
        "URLS_TXT": os.path.join(BASE, "URLs TXT"),
        "PLAYLIST": os.path.join(BASE, "Spotify Playlists"),
        "YT_PLAYLIST": os.path.join(BASE, "YouTube Playlists")
    }
    
    for d in DIRS.values():
        os.makedirs(d, exist_ok=True)

set_dirs()

# ========================= AUTH ==============================

def init_spotify():
    """Initialize Spotify client"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    try:
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    except:
        return None

def init_genius():
    """Initialize Genius client"""
    token = os.getenv("GENIUS_TOKEN", "")
    if not token:
        return None
    try:
        return lyricsgenius.Genius(token, skip_non_songs=True, remove_section_headers=True)
    except:
        return None

sp = init_spotify()
genius = init_genius()

# ========================= METADATA ==========================

def build_meta(item):
    """Build metadata dict from Spotify track"""
    return {
        "track": item["name"],
        "artist": item["artists"][0]["name"],
        "album": item["album"]["name"],
        "album_artist": item["album"]["artists"][0]["name"],
        "track_no": item["track_number"],
        "disc_no": item["disc_number"],
        "year": item["album"]["release_date"][:4],
        "art": item["album"]["images"][0]["url"] if item["album"]["images"] else None,
        "duration": item["duration_ms"] / 1000
    }

def spotify_meta(track, artist):
    """Search Spotify for track metadata with smart scoring"""
    if not sp:
        print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Spotify API not configured")
        return None
    
    try:
        r = sp.search(q=f'{track} {artist}', type="track", limit=20)
        items = r["tracks"]["items"]
        if not items:
            return None
        
        # Calculate match scores
        def score(item):
            s = 0
            t_name = item["name"].lower().strip()
            artists = [a["name"].lower().strip() for a in item["artists"]]
            search_t = track.lower().strip()
            search_a = artist.lower().strip()
            
            if t_name == search_t: s += 100
            elif search_t in t_name: s += 50
            
            if search_a in artists: s += 80
            elif any(search_a in a for a in artists): s += 40
            
            s += min(item.get('popularity', 0) / 10, 5)
            return s
        
        scored = [(score(item), item) for item in items]
        scored.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_item = scored[0]
        
        if best_score >= 100:
            match_type = "EXACT" if best_score >= 180 else "GOOD" if best_score >= 130 else "CLOSE"
            color = Fore.GREEN if best_score >= 180 else Fore.YELLOW
            print(f"{color}[{match_type}]{Style.RESET_ALL} {best_item['name']} by {best_item['artists'][0]['name']} (score: {int(best_score)})")
            return build_meta(best_item)
        
        print(f"{Fore.RED}[NO MATCH]{Style.RESET_ALL} for '{track}' by '{artist}'")
        return None
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Spotify: {e}")
        return None

def get_lyrics(track, artist):
    """Fetch lyrics from Genius"""
    if not genius:
        return None
    try:
        song = genius.search_song(track, artist)
        return song.lyrics if song else None
    except:
        return None

def embed(path, meta, lyrics=None):
    """Embed ID3 tags and artwork"""
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
    
    if lyrics:
        tags["USLT"] = USLT(encoding=3, lang='eng', desc='', text=lyrics)
        print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} Lyrics embedded")
    
    if meta.get("art"):
        try:
            img = requests.get(meta["art"], timeout=10).content
            tags.delall("APIC")
            tags.add(APIC(encoding=3, mime="image/jpeg", type=3, data=img))
        except:
            pass
    
    tags.save(path)

# ======================= DOWNLOAD CORE =======================

def download_audio(url, track, artist, out_dir, meta=None):
    """Core download function - downloads and tags audio"""
    if not meta:
        meta = spotify_meta(track, artist)
        if not meta:
            return {"success": False, "reason": "No metadata", "track": track, "artist": artist}
    
    base = clean_name(f"{meta['track']} - {meta['artist']}")
    final = os.path.join(out_dir, base + ".mp3")
    
    if os.path.exists(final):
        print(f"{Fore.YELLOW}[SKIP]{Style.RESET_ALL} Already exists: {base}.mp3")
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
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/"
        },
        "force_ipv4": True,
        "concurrent_fragment_downloads": 1,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}],
        "ignoreerrors": True,
        "no_color": True
    }
    
    try:
        # Suppress stderr output
        import io
        import contextlib
        
        stderr_buffer = io.StringIO()
        with contextlib.redirect_stderr(stderr_buffer):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        
        if os.path.exists(final):
            lyrics = get_lyrics(meta['track'], meta['artist']) if genius else None
            embed(final, meta, lyrics)
            print(f"\n{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {base}.mp3")
            return {"success": True, "reason": "Downloaded", "track": meta['track'], "artist": meta['artist']}
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")
    
    return {"success": False, "reason": "Download failed", "track": track, "artist": artist}

def find_best_youtube(track, artist, expected_duration):
    """Find best YouTube match using smart scoring"""
    best_match = None
    best_score = -1
    tolerance = 15
    
    search_queries = [
        f"ytsearch20:{track} {artist} official audio",
        f"ytsearch20:{track} {artist} audio",
        f"ytsearch20:{track} {artist} lyrics",
    ]
    
    for query in search_queries:
        try:
            import io
            import contextlib
            
            stderr_buffer = io.StringIO()
            with contextlib.redirect_stderr(stderr_buffer):
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "logger": yt_logger(), "no_color": True}) as ydl:
                    info = ydl.extract_info(query, download=False)
                    if not info or "entries" not in info:
                        continue
                    
                    for entry in info["entries"]:
                        dur = entry.get("duration")
                        title = entry.get("title", "").lower()
                        
                        if not dur:
                            continue
                        
                        # Skip music videos
                        if any(kw in title for kw in ["music video", "official video", "(official video)"]):
                            continue
                        
                        duration_diff = abs(dur - expected_duration)
                        if duration_diff > tolerance:
                            continue
                        
                        # Score calculation
                        score = 1000 - (duration_diff * 50)
                        if "official audio" in title: score += 200
                        elif "audio" in title: score += 100
                        if "lyrics" in title: score += 50
                        if track.lower() in title: score += 100
                        if artist.lower() in title: score += 100
                        if "cover" in title: score -= 300
                        if "remix" in title and "remix" not in track.lower(): score -= 300
                        if "live" in title and "live" not in track.lower(): score -= 200
                        if "instrumental" in title: score -= 400
                        if "karaoke" in title: score -= 500
                        
                        if score > best_score:
                            best_score = score
                            best_match = entry
            
            if best_match and best_score >= 800:
                break
        except:
            continue
    
    if best_match:
        dur = best_match.get("duration")
        diff = abs(dur - expected_duration)
        print(f"{Fore.GREEN}[BEST MATCH]{Style.RESET_ALL} {best_match['title']} ({dur}s, Δ{diff}s, score: {int(best_score)})")
        return best_match["webpage_url"]
    
    print(f"{Fore.RED}[NO MATCH]{Style.RESET_ALL} No suitable audio found")
    return None

def search_youtube_videos(query, limit=5):
    """Search YouTube and return top results for user selection"""
    try:
        import io
        import contextlib
        
        search_query = f"ytsearch{limit}:{query}"
        
        stderr_buffer = io.StringIO()
        with contextlib.redirect_stderr(stderr_buffer):
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "logger": yt_logger(), "no_color": True}) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                if not info or "entries" not in info:
                    return []
                
                results = []
                for entry in info["entries"]:
                    if entry:
                        results.append({
                            "title": entry.get("title", "Unknown"),
                            "url": entry.get("webpage_url", ""),
                            "duration": entry.get("duration", 0),
                            "channel": entry.get("channel", "Unknown")
                        })
                
                return results
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} YouTube search failed: {e}")
        return []

# ======================= DOWNLOAD OPTIONS ====================

def download_track(track, artist, out_dir=None, ask=True):
    """Download single track with YouTube fallback if Spotify fails"""
    meta = spotify_meta(track, artist)
    
    if not meta:
        # YouTube fallback for non-Spotify tracks
        print(f"\n{Fore.YELLOW}[NO SPOTIFY MATCH]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Searching YouTube directly...")
        
        # Search YouTube
        search_query = f"{track} {artist}"
        results = search_youtube_videos(search_query, limit=5)
        
        if not results:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No YouTube results found")
            return {"success": False, "reason": "No results found", "track": track, "artist": artist}
        
        # Show results
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"YOUTUBE SEARCH RESULTS")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        for i, video in enumerate(results, 1):
            duration_min = video['duration'] // 60
            duration_sec = video['duration'] % 60
            print(f"{Fore.WHITE}[{i}] {video['title']}{Style.RESET_ALL}")
            print(f"    Channel: {video['channel']}")
            print(f"    Duration: {duration_min}:{duration_sec:02d}")
            print()
        
        choice = input(f"{Fore.CYAN}Select [1-{len(results)}] or 0 to cancel: {Style.RESET_ALL}").strip()
        
        if choice == "0" or not choice.isdigit():
            return {"success": False, "reason": "Cancelled", "track": track, "artist": artist}
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(results):
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Invalid choice")
            return {"success": False, "reason": "Invalid choice", "track": track, "artist": artist}
        
        selected = results[idx]
        
        # Download with basic metadata (no Spotify)
        out_dir = out_dir or DIRS["SINGLE"]
        return download_url(selected['url'], out_dir)
    
    # Continue with normal Spotify flow
    if ask:
        print(f"\n{Fore.CYAN}[PREVIEW]{Style.RESET_ALL}")
        print(f"  Track: {meta['track']}")
        print(f"  Artist: {meta['artist']}")
        print(f"  Album: {meta['album']} ({meta['year']})")
        if input(f"\n{Fore.CYAN}Download? [Y/N]: {Style.RESET_ALL}").strip().lower() != "y":
            return {"success": False, "reason": "Cancelled", "track": track, "artist": artist}
    
    out_dir = out_dir or DIRS["SINGLE"]
    url = find_best_youtube(track, artist, int(meta["duration"]))
    
    if not url:
        return {"success": False, "reason": "No YouTube match", "track": track, "artist": artist}
    
    return download_audio(url, track, artist, out_dir, meta)

def download_url(url, out_dir=None):
    """Download from direct URL"""
    out_dir = out_dir or DIRS["SINGLE"]
    
    try:
        import io
        import contextlib
        
        stderr_buffer = io.StringIO()
        with contextlib.redirect_stderr(stderr_buffer):
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "logger": yt_logger(), "no_color": True}) as ydl:
                print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Extracting info...")
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "Unknown")
                
                # Parse track/artist from title
                if " - " in title:
                    parts = title.split(" - ", 1)
                    artist, track = parts[0].strip(), parts[1].strip()
                else:
                    track, artist = title, "Unknown"
                
                # Clean up common suffixes from BOTH track and artist
                cleanup_patterns = [
                    "(Official Video)", "(Official Audio)", "(Official Music Video)",
                    "[Official Video]", "[Official Audio]", "[Official Music Video]",
                    "(Lyrics)", "[Lyrics]", "(Lyric Video)", "[Lyric Video]",
                    "(Official Lyric Video)", "[Official Lyric Video]",
                    "(Audio)", "[Audio]", "(Visualizer)", "[Visualizer]",
                    "(Official Visualizer)", "[Official Visualizer]",
                    "(Music Video)", "[Music Video]", "(HD)", "[HD]",
                    "(4K)", "[4K]", "(Live)", "[Live]"
                ]
                
                for pattern in cleanup_patterns:
                    track = track.replace(pattern, "").strip()
                    artist = artist.replace(pattern, "").strip()
                
                # Remove featuring artists from track name for better Spotify matching
                # Keep original for metadata, but search without "ft."
                track_for_search = track
                
                # Remove featuring patterns: "ft.", "feat.", "featuring"
                feat_patterns = [
                    r'\s+ft\.?\s+.*',  # " ft. Artist"
                    r'\s+feat\.?\s+.*',  # " feat. Artist"
                    r'\s+featuring\s+.*',  # " featuring Artist"
                    r'\s+\(ft\.?.*?\)',  # " (ft. Artist)"
                    r'\s+\[ft\.?.*?\]',  # " [ft. Artist]"
                    r'\s+\(feat\.?.*?\)',  # " (feat. Artist)"
                    r'\s+\[feat\.?.*?\]',  # " [feat. Artist]"
                ]
                
                for pattern in feat_patterns:
                    track_for_search = re.sub(pattern, '', track_for_search, flags=re.IGNORECASE).strip()
                
                print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Parsed: {track} by {artist}")
                if track_for_search != track:
                    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Searching as: {track_for_search} by {artist}")
                
                # Try to get Spotify metadata (use cleaned track name for search)
                meta = spotify_meta(track_for_search, artist)
                
                if meta:
                    # Download with full metadata (use Spotify's proper track name)
                    print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Using Spotify metadata")
                    return download_audio(url, track_for_search, artist, out_dir, meta)
                else:
                    # Download without Spotify - just use basic info
                    print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Downloading with basic metadata (no Spotify match)")
                    
                    # Use cleaned track name for filename
                    base = clean_name(f"{track_for_search} - {artist}")
                    final = os.path.join(out_dir, base + ".mp3")
                    
                    if os.path.exists(final):
                        print(f"{Fore.YELLOW}[SKIP]{Style.RESET_ALL} Already exists: {base}.mp3")
                        return {"success": True, "reason": "Already exists", "track": track_for_search, "artist": artist}
                    
                    outtmpl = os.path.join(out_dir, base + ".%(ext)s")
                    
                    ydl_opts = {
                        "format": "bestaudio/best",
                        "outtmpl": outtmpl,
                        "quiet": True,
                        "no_warnings": True,
                        "logger": yt_logger(),
                        "progress_hooks": [progress_hook],
                        "http_headers": {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept-Language": "en-US,en;q=0.9",
                            "Referer": "https://www.youtube.com/"
                        },
                        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}],
                    }
                    
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            ydl2.download([url])
                            
                            if os.path.exists(final):
                                # Add basic metadata
                                try:
                                    tags = ID3(final)
                                except ID3NoHeaderError:
                                    tags = ID3()
                                
                                tags["TIT2"] = TIT2(encoding=3, text=track_for_search)
                                tags["TPE1"] = TPE1(encoding=3, text=artist)
                                
                                # Try to get YouTube thumbnail as artwork
                                thumbnail_url = info.get("thumbnail")
                                if thumbnail_url:
                                    try:
                                        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Downloading thumbnail...")
                                        img_data = requests.get(thumbnail_url, timeout=10).content
                                        tags.delall("APIC")
                                        tags.add(APIC(encoding=3, mime="image/jpeg", type=3, data=img_data))
                                        print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} Thumbnail embedded")
                                    except Exception as e:
                                        print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} Couldn't download thumbnail")
                                
                                tags.save(final)
                                
                                print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {base}.mp3")
                                return {"success": True, "reason": "Downloaded", "track": track_for_search, "artist": artist}
                    except Exception as e:
                        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Download failed: {e}")
                        return {"success": False, "reason": str(e), "track": track_for_search, "artist": artist}
                
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")
        return False

def process_batch(items, out_dir, item_type="track"):
    """Generic batch processor"""
    failed = []
    
    for i, item in enumerate(items, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(items)}] Processing...")
        print('='*60)
        
        if item_type == "track":
            track, artist = item
            result = download_track(track, artist, out_dir, ask=False)
        else:  # URL
            result = download_url(item, out_dir)
        
        if isinstance(result, dict) and not result["success"]:
            failed.append(result)
    
    return failed

def write_failed_log(failed, out_dir, name):
    """Write failed downloads log"""
    if not failed:
        print(f"\n{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} All downloads completed!")
        return
    
    log_file = os.path.join(out_dir, f"_FAILED_DOWNLOADS_{clean_name(name)}.txt")
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Failed Downloads - {name}\n")
        f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total: {len(failed)}\n")
        f.write("="*60 + "\n\n")
        
        for item in failed:
            f.write(f"Track: {item.get('track', 'N/A')}\n")
            f.write(f"Artist: {item.get('artist', 'N/A')}\n")
            f.write(f"Reason: {item['reason']}\n")
            f.write("-"*60 + "\n")
    
    print(f"\n{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {len(failed)} failed")
    print(f"{Fore.CYAN}[LOG]{Style.RESET_ALL} {log_file}")

# ===================== CSV / TXT / PLAYLISTS ==================

def search_spotify_album(album_name, artist_name):
    """Search for Spotify album"""
    if not sp:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Spotify not configured")
        return None
    
    try:
        # Try multiple search strategies
        queries = [
            f'album:"{album_name}" artist:"{artist_name}"',
            f'{album_name} {artist_name}',
            album_name
        ]
        
        all_albums = []
        seen = set()
        
        for query in queries:
            try:
                results = sp.search(q=query, type="album", limit=10)
                for album in results["albums"]["items"]:
                    if album["id"] not in seen:
                        all_albums.append(album)
                        seen.add(album["id"])
            except:
                continue
        
        if not all_albums:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No albums found")
            return None
        
        # Score and sort
        def score_album(album):
            s = 0
            a_name = album['name'].lower()
            search = album_name.lower()
            if a_name == search: s += 100
            elif search in a_name or a_name in search: s += 50
            
            for artist in album["artists"]:
                a_artist = artist["name"].lower()
                search_artist = artist_name.lower()
                if a_artist == search_artist: s += 80
                elif search_artist in a_artist or a_artist in search_artist: s += 40
            return s
        
        scored = [(score_album(a), a) for a in all_albums]
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Show top 10
        print(f"\n{Fore.CYAN}=== ALBUM RESULTS ==={Style.RESET_ALL}")
        for i, (score, album) in enumerate(scored[:10], 1):
            artists = ", ".join([a["name"] for a in album["artists"]])
            year = album["release_date"][:4] if album.get("release_date") else "?"
            tracks = album.get("total_tracks", "?")
            match = "EXACT" if score >= 150 else "GOOD" if score >= 80 else "MAYBE"
            color = Fore.GREEN if score >= 150 else Fore.YELLOW if score >= 80 else Fore.WHITE
            print(f"{color}[{i}] {album['name']} - {artists} ({year}) [{tracks} tracks] ({match}){Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.CYAN}Select [1-{min(10, len(scored))}] or 0 to cancel: {Style.RESET_ALL}").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= min(10, len(scored)):
            return scored[int(choice)-1][1]["id"]
        return None
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")
        return None

def download_spotify_album(album_id):
    """Download Spotify album"""
    if not sp:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Spotify not configured")
        return
    
    try:
        album = sp.album(album_id)
        tracks = [(t["name"], t["artists"][0]["name"]) for t in album["tracks"]["items"]]
        name = album["name"]
        artist = album["artists"][0]["name"]
        year = album["release_date"][:4] if album.get("release_date") else "?"
        
        out_dir = os.path.join(DIRS["ALBUM"], clean_name(name))
        os.makedirs(out_dir, exist_ok=True)
        
        # Show preview with album info
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"SPOTIFY ALBUM PREVIEW")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Album:{Style.RESET_ALL} {name}")
        print(f"{Fore.GREEN}Artist:{Style.RESET_ALL} {artist}")
        print(f"{Fore.GREEN}Year:{Style.RESET_ALL} {year}")
        print(f"{Fore.GREEN}Tracks:{Style.RESET_ALL} {len(tracks)}\n")
        
        for i, (t, a) in enumerate(tracks, 1):
            print(f"{Fore.GREEN}[{i}]{Style.RESET_ALL} {t}")
        
        remove = input(f"\n{Fore.CYAN}Remove tracks (comma-separated, Enter for none): {Style.RESET_ALL}").strip()
        if remove:
            try:
                bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
                tracks = [t for i, t in enumerate(tracks) if i not in bad]
            except:
                pass
        
        if not tracks:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No tracks remaining")
            return
        
        if input(f"\n{Fore.CYAN}Download {len(tracks)} tracks? [Y/N]: {Style.RESET_ALL}").strip().lower() != "y":
            return
        
        print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Downloading to: {out_dir}\n")
        
        failed = []
        for i, (t, a) in enumerate(tracks, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(tracks)}] {a} - {t}")
            print('='*60)
            result = download_track(t, a, out_dir, ask=False)
            if not result["success"]:
                failed.append(result)
        
        write_failed_log(failed, out_dir, name)
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")

def process_csv(csv_path):
    """Process CSV file"""
    csv_path = clean_path(csv_path)
    if not os.path.exists(csv_path):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} File not found")
        return
    
    tracks = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        # Strip BOM and whitespace from column names
        if reader.fieldnames:
            reader.fieldnames = [col.strip().strip('\ufeff') for col in reader.fieldnames]
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Detected CSV columns: {', '.join(reader.fieldnames)}")
        
        row_count = 0
        for row in reader:
            row_count += 1
            
            # Debug: dump first row completely
            if row_count == 1:
                print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} First row contents:")
                for key, value in row.items():
                    print(f"  '{key}' = '{value}'")
            
            # Try multiple column name variations for track
            track = (row.get('Track Name') or 
                    row.get('Track name') or  # TuneMyMusic
                    row.get('track') or 
                    row.get('Track') or 
                    row.get('name') or
                    row.get('Name'))
            
            # Try multiple column name variations for artist
            # Use strip() to handle empty strings
            artist = (row.get('Artist Name(s)', '').strip() or
                     row.get('Artist Name', '').strip() or
                     row.get('Artist name', '').strip() or  # TuneMyMusic
                     row.get('Artist', '').strip() or 
                     row.get('artist', '').strip() or
                     None)
            
            # Handle TuneMyMusic format where artist is in track name
            if track and not artist and ' - ' in track:
                # Track name format: "Artist - Song Title"
                parts = track.split(' - ', 1)
                artist = parts[0].strip()
                track = parts[1].strip()
                
                # Clean up YouTube suffixes from track name
                cleanup_patterns = [
                    "(Official Video)", "(Official Audio)", "(Official Music Video)",
                    "[Official Video]", "[Official Audio]", "[Official Music Video]",
                    "(Lyrics)", "[Lyrics]", "(Lyric Video)", "[Lyric Video]",
                    "(Official Lyric Video)", "[Official Lyric Video]",
                    "(Audio)", "[Audio]", "(Visualizer)", "[Visualizer]",
                    "(Official Visualizer)", "[Official Visualizer]",
                    "(Music Video)", "[Music Video]", "(HD)", "[HD]",
                    "(4K)", "[4K]", "(Live)", "[Live]"
                ]
                
                for pattern in cleanup_patterns:
                    track = track.replace(pattern, "").strip()
                
                # Remove featuring artists for better Spotify matching
                import re
                feat_patterns = [
                    r'\s+ft\.?\s+.*',
                    r'\s+feat\.?\s+.*',
                    r'\s+featuring\s+.*',
                    r'\s+\(ft\.?.*?\)',
                    r'\s+\[ft\.?.*?\]',
                    r'\s+\(feat\.?.*?\)',
                    r'\s+\[feat\.?.*?\]',
                    r'\s+\[with\s+.*?\]',
                ]
                
                for pattern in feat_patterns:
                    track = re.sub(pattern, '', track, flags=re.IGNORECASE).strip()
                
                if row_count <= 3:
                    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Parsed from track: '{artist}' - '{track}'")
            
            if track and artist:
                tracks.append((track.strip(), artist.strip()))
            else:
                if row_count <= 3:  # Show first 3 failed rows
                    print(f"{Fore.YELLOW}[DEBUG]{Style.RESET_ALL} Row {row_count} skipped - Track: '{track}', Artist: '{artist}'")
    
    if not tracks:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No valid tracks in CSV")
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} CSV must have columns for track and artist")
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Supported column names:")
        print(f"  Track: 'Track Name', 'track', 'Track', 'name', 'Name', 'Track name'")
        print(f"  Artist: 'Artist', 'artist', 'Artist Name', 'Artist name', 'Artist Name(s)'")
        return
    
    csv_name = os.path.splitext(os.path.basename(csv_path))[0]
    out_dir = os.path.join(DIRS["CSV"], csv_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # Fetch metadata for preview
    print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Fetching metadata for {len(tracks)} tracks...")
    tracks_with_meta = []
    for i, (t, a) in enumerate(tracks, 1):
        print(f"\r{Fore.CYAN}[{i}/{len(tracks)}]{Style.RESET_ALL} Checking: {t[:30]}...", end='', flush=True)
        meta = spotify_meta(t, a)
        tracks_with_meta.append((t, a, meta))
    
    print()  # New line
    
    # Show preview
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"CSV PREVIEW - {csv_name}")
    print(f"{'='*60}{Style.RESET_ALL}")
    for i, (t, a, meta) in enumerate(tracks_with_meta, 1):
        if meta:
            print(f"{Fore.GREEN}[{i}]{Style.RESET_ALL} {meta['artist']} - {meta['track']} ({meta['album']}, {meta['year']})")
        else:
            print(f"{Fore.RED}[{i}]{Style.RESET_ALL} {a} - {t} [NO METADATA]")
    
    remove = input(f"\n{Fore.CYAN}Remove tracks (comma-separated, Enter for none): {Style.RESET_ALL}").strip()
    if remove:
        try:
            bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
            tracks_with_meta = [item for i, item in enumerate(tracks_with_meta) if i not in bad]
        except:
            pass
    
    if not tracks_with_meta:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No tracks remaining")
        return
    
    if input(f"\n{Fore.CYAN}Download {len(tracks_with_meta)} tracks? [Y/N]: {Style.RESET_ALL}").strip().lower() != "y":
        return
    
    print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Downloading to: {out_dir}\n")
    
    # Download
    failed = []
    for i, (t, a, meta) in enumerate(tracks_with_meta, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(tracks_with_meta)}] {a} - {t}")
        print('='*60)
        
        if meta:
            # Has Spotify metadata - use the smart download
            url = find_best_youtube(t, a, int(meta["duration"]))
            if url:
                result = download_audio(url, t, a, out_dir, meta)
            else:
                result = {"success": False, "reason": "No YouTube match", "track": t, "artist": a}
        else:
            # No Spotify metadata - try direct YouTube search and download
            print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} No Spotify metadata, searching YouTube directly...")
            try:
                search_query = f"ytsearch1:{t} {a} audio"
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                    info = ydl.extract_info(search_query, download=False)
                    if info and 'entries' in info and info['entries']:
                        video_url = info['entries'][0]['webpage_url']
                        result = download_url(video_url, out_dir)
                    else:
                        result = {"success": False, "reason": "No YouTube results", "track": t, "artist": a}
            except Exception as e:
                result = {"success": False, "reason": f"Search failed: {str(e)}", "track": t, "artist": a}
        
        if not result["success"]:
            failed.append(result)
    
    write_failed_log(failed, out_dir, csv_name)

def process_urls_txt(txt_path):
    """Process TXT file with URLs"""
    txt_path = clean_path(txt_path)
    if not os.path.exists(txt_path):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} File not found")
        return
    
    urls = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and url.startswith("http"):
                urls.append(url)
    
    if not urls:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No URLs found")
        return
    
    txt_name = os.path.splitext(os.path.basename(txt_path))[0]
    out_dir = os.path.join(DIRS["URLS_TXT"], txt_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # Extract video info for preview
    print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Extracting info from {len(urls)} URLs...")
    video_info = []
    for i, url in enumerate(urls, 1):
        print(f"\r{Fore.CYAN}[{i}/{len(urls)}]{Style.RESET_ALL} Processing...", end='', flush=True)
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "Unknown")
                
                # Parse track/artist
                if " - " in title:
                    parts = title.split(" - ", 1)
                    artist, track = parts[0].strip(), parts[1].strip()
                else:
                    track, artist = title, "Unknown"
                
                # Clean up
                for suffix in ["(Official Video)", "(Official Audio)", "(Lyrics)", "[Official Video]", "[Official Audio]", "[Lyrics]"]:
                    track = track.replace(suffix, "").strip()
                    artist = artist.replace(suffix, "").strip()
                
                video_info.append((url, artist, track))
        except:
            video_info.append((url, "Unknown", "Failed to extract"))
    
    print()  # New line
    
    # Show full preview
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"TXT PREVIEW - {txt_name} ({len(video_info)} URLs)")
    print(f"{'='*60}{Style.RESET_ALL}")
    for i, (url, artist, track) in enumerate(video_info, 1):
        print(f"{Fore.WHITE}[{i}] {artist} - {track}{Style.RESET_ALL}")
    
    remove = input(f"\n{Fore.CYAN}Remove URLs (comma-separated numbers, Enter for none): {Style.RESET_ALL}").strip()
    if remove:
        try:
            bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
            video_info = [v for i, v in enumerate(video_info) if i not in bad]
            print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Removed {len(bad)} URLs, {len(video_info)} remaining")
        except:
            pass
    
    if not video_info:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No URLs remaining")
        return
    
    if input(f"\n{Fore.CYAN}Download {len(video_info)} videos? [Y/N]: {Style.RESET_ALL}").strip().lower() != "y":
        return
    
    print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Downloading to: {out_dir}\n")
    
    # Download each URL
    failed = []
    for i, (url, artist, track) in enumerate(video_info, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(video_info)}] {artist} - {track}")
        print('='*60)
        result = download_url(url, out_dir)
        if isinstance(result, dict) and not result["success"]:
            failed.append(result)
    
    write_failed_log(failed, out_dir, txt_name)
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(urls)}] {url}")
        print('='*60)
        result = download_url(url, out_dir)
        if isinstance(result, dict) and not result.get("success"):
            failed.append(result)
    
    write_failed_log(failed, out_dir, txt_name)

def download_spotify_playlist(playlist_id):
    """Download Spotify playlist"""
    if not sp:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Spotify not configured")
        return
    
    try:
        results = sp.playlist_tracks(playlist_id)
        tracks = [(item["track"]["name"], item["track"]["artists"][0]["name"]) 
                  for item in results["items"] if item["track"]]
        
        playlist = sp.playlist(playlist_id)
        name = playlist["name"]
        
        out_dir = os.path.join(DIRS["PLAYLIST"], clean_name(name))
        os.makedirs(out_dir, exist_ok=True)
        
        # Show full preview
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"SPOTIFY PLAYLIST PREVIEW - {name} ({len(tracks)} tracks)")
        print(f"{'='*60}{Style.RESET_ALL}")
        for i, (t, a) in enumerate(tracks, 1):
            print(f"{Fore.GREEN}[{i}]{Style.RESET_ALL} {a} - {t}")
        
        remove = input(f"\n{Fore.CYAN}Remove tracks (comma-separated, Enter for none): {Style.RESET_ALL}").strip()
        if remove:
            try:
                bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
                tracks = [t for i, t in enumerate(tracks) if i not in bad]
                print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Removed {len(bad)} tracks, {len(tracks)} remaining")
            except:
                pass
        
        if not tracks:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No tracks remaining")
            return
        
        if input(f"\n{Fore.CYAN}Download {len(tracks)} tracks? [Y/N]: {Style.RESET_ALL}").strip().lower() != "y":
            return
        
        print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Downloading to: {out_dir}\n")
        
        failed = []
        for i, (t, a) in enumerate(tracks, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(tracks)}] {a} - {t}")
            print('='*60)
            result = download_track(t, a, out_dir, ask=False)
            if not result["success"]:
                failed.append(result)
        
        write_failed_log(failed, out_dir, name)
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")

def download_youtube_playlist(playlist_url):
    """Download YouTube playlist"""
    try:
        import io
        import contextlib
        
        stderr_buffer = io.StringIO()
        with contextlib.redirect_stderr(stderr_buffer):
            with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "no_warnings": True, "logger": yt_logger(), "no_color": True}) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if not info or not info.get("entries"):
                    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Playlist empty/private")
                    return
                
                name = info.get("title", "YouTube Playlist")
                entries = info["entries"]
                
                print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {name} ({len(entries)} videos)")
                print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Parsing video titles...")
                
                # Extract and parse video information
                videos = []
                for i, entry in enumerate(entries, 1):
                    if entry:
                        print(f"\r{Fore.CYAN}[{i}/{len(entries)}]{Style.RESET_ALL} Processing...", end='', flush=True)
                        video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                        video_title = entry.get("title", "Unknown")
                        
                        # Parse artist and track
                        title = video_title
                        # Remove common suffixes first
                        for suffix in ["(Official Video)", "(Official Audio)", "(Official Music Video)", 
                                      "[Official Video]", "[Official Audio]", "(Lyrics)", "[Lyrics]",
                                      "(Audio)", "[Audio]", "(Visualizer)", "[Visualizer]"]:
                            title = title.replace(suffix, "").strip()
                        
                        # Parse format: "Artist - Track" or "Track - Artist"
                        if " - " in title:
                            parts = title.split(" - ", 1)
                            artist, track = parts[0].strip(), parts[1].strip()
                        elif ": " in title:
                            parts = title.split(": ", 1)
                            artist, track = parts[0].strip(), parts[1].strip()
                        else:
                            track, artist = title, "Unknown"
                        
                        videos.append({"url": video_url, "title": video_title, "artist": artist, "track": track})
                
                print()  # New line
            
            # Show full preview with parsed names
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"YOUTUBE PLAYLIST PREVIEW - {name} ({len(videos)} videos)")
            print(f"{'='*60}{Style.RESET_ALL}")
            for i, video in enumerate(videos, 1):
                print(f"{Fore.WHITE}[{i}] {video['artist']} - {video['track']}{Style.RESET_ALL}")
            
            remove = input(f"\n{Fore.CYAN}Videos to remove (comma-separated, Enter for none): {Style.RESET_ALL}").strip()
            if remove:
                try:
                    bad = {int(x.strip())-1 for x in remove.split(",") if x.strip().isdigit()}
                    videos = [v for i, v in enumerate(videos) if i not in bad]
                    print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Removed {len(bad)} videos, {len(videos)} remaining")
                except:
                    pass
            
            if not videos:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} No videos remaining")
                return
            
            if input(f"\n{Fore.CYAN}Download {len(videos)} videos? [Y/N]: {Style.RESET_ALL}").strip().lower() != "y":
                return
            
            out_dir = os.path.join(DIRS["YT_PLAYLIST"], clean_name(name))
            os.makedirs(out_dir, exist_ok=True)
            
            print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Downloading to: {out_dir}\n")
            
            # Download each video
            failed = []
            
            for i, video in enumerate(videos, 1):
                print(f"\n{'='*60}")
                print(f"[{i}/{len(videos)}] {video['artist']} - {video['track']}")
                print('='*60)
                
                result = download_url(video['url'], out_dir)
                if isinstance(result, dict) and not result.get("success"):
                    failed.append({"title": video['title'], "url": video['url'], "reason": result.get("reason", "Unknown")})
            
            # Write failed log
            if failed:
                log_file = os.path.join(out_dir, f"_FAILED_DOWNLOADS_{clean_name(name)}.txt")
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"Failed Downloads - {name}\n")
                    f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total: {len(failed)}\n")
                    f.write("="*60 + "\n\n")
                    
                    for item in failed:
                        f.write(f"Title: {item['title']}\n")
                        f.write(f"URL: {item['url']}\n")
                        f.write(f"Reason: {item['reason']}\n")
                        f.write("-"*60 + "\n")
                
                print(f"\n{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {len(failed)} failed")
                print(f"{Fore.CYAN}[LOG]{Style.RESET_ALL} {log_file}")
            else:
                print(f"\n{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} All downloads completed!")
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")

# ======================== SETTINGS ============================
# ======================= SETTINGS ============================

def save_config():
    """Save config to file"""
    config = {
        "LIBRARY_PATH": BASE,
        "SPOTIFY_CLIENT_ID": os.getenv("SPOTIFY_CLIENT_ID", ""),
        "SPOTIFY_CLIENT_SECRET": os.getenv("SPOTIFY_CLIENT_SECRET", ""),
        "GENIUS_TOKEN": os.getenv("GENIUS_TOKEN", "")
    }
    
    with open("reel_config.txt", 'w') as f:
        for k, v in config.items():
            f.write(f"{k}={v}\n")
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Config saved")

def load_config():
    """Load config from file"""
    if not os.path.exists("reel_config.txt"):
        return None
    
    config = {}
    with open("reel_config.txt", 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                config[k] = v
    return config

def settings_menu():
    """Settings menu"""
    while True:
        print(f"\n{Fore.CYAN}=== SETTINGS ==={Style.RESET_ALL}")
        print(f"1. Change library path (current: {BASE})")
        print(f"2. Configure Spotify API")
        print(f"3. Configure Genius API")
        print(f"4. Back")
        
        choice = input(f"{Fore.CYAN}Select: {Style.RESET_ALL}").strip()
        
        if choice == "1":
            path = input("New path: ").strip()
            if path:
                set_dirs(path)
                save_config()
                print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Updated")
        
        elif choice == "2":
            print("\nGet credentials: https://developer.spotify.com/dashboard")
            cid = input("Client ID: ").strip()
            secret = input("Client Secret: ").strip()
            if cid and secret:
                os.environ["SPOTIFY_CLIENT_ID"] = cid
                os.environ["SPOTIFY_CLIENT_SECRET"] = secret
                global sp
                sp = init_spotify()
                save_config()
                print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Updated")
        
        elif choice == "3":
            print("\nGet token: https://genius.com/api-clients")
            token = input("Access Token: ").strip()
            if token:
                os.environ["GENIUS_TOKEN"] = token
                global genius
                genius = init_genius()
                save_config()
                print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Updated")
        
        elif choice == "4":
            break

# =========================== MENU ============================

def menu():
    """Main menu"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}╔════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.WHITE}              REEL v2.0                 {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    print(f"{Fore.LIGHTGREEN_EX}1.{Fore.WHITE} Search & Download Track")
    print(f"{Fore.LIGHTGREEN_EX}2.{Fore.WHITE} Download from URL")
    print(f"{Fore.LIGHTCYAN_EX}3.{Fore.WHITE} CSV Import")
    print(f"{Fore.LIGHTCYAN_EX}4.{Fore.WHITE} URLs from TXT")
    print(f"{Fore.LIGHTMAGENTA_EX}5.{Fore.WHITE} Spotify Album")
    print(f"{Fore.LIGHTMAGENTA_EX}6.{Fore.WHITE} Spotify Playlist")
    print(f"{Fore.LIGHTMAGENTA_EX}7.{Fore.WHITE} YouTube Playlist")
    print(f"{Fore.LIGHTYELLOW_EX}8.{Fore.WHITE} Settings")
    print(f"{Fore.RED}9.{Fore.WHITE} Exit\n")
    
    try:
        c = input(f"{Fore.CYAN}Select [1-9]: {Style.RESET_ALL}").strip()
        
        if c == "1":
            track = input("Track: ").strip()
            artist = input("Artist: ").strip()
            if track and artist:
                download_track(track, artist)
        
        elif c == "2":
            url = input("URL: ").strip()
            if url:
                # Extract and show preview first
                try:
                    import io
                    import contextlib
                    
                    stderr_buffer = io.StringIO()
                    with contextlib.redirect_stderr(stderr_buffer):
                        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "logger": yt_logger(), "no_color": True}) as ydl:
                            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Extracting info...")
                            info = ydl.extract_info(url, download=False)
                            title = info.get("title", "Unknown")
                            duration = info.get("duration", 0)
                            uploader = info.get("uploader", "Unknown")
                            
                            # Parse track/artist from title
                            if " - " in title:
                                parts = title.split(" - ", 1)
                                artist, track = parts[0].strip(), parts[1].strip()
                            else:
                                track, artist = title, "Unknown"
                            
                            # Clean up common suffixes
                            cleanup_patterns = [
                                "(Official Video)", "(Official Audio)", "(Official Music Video)",
                                "[Official Video]", "[Official Audio]", "[Official Music Video]",
                                "(Lyrics)", "[Lyrics]", "(Lyric Video)", "[Lyric Video]",
                                "(Official Lyric Video)", "[Official Lyric Video]",
                                "(Audio)", "[Audio]", "(Visualizer)", "[Visualizer]",
                                "(Official Visualizer)", "[Official Visualizer]",
                                "(Music Video)", "[Music Video]", "(HD)", "[HD]",
                                "(4K)", "[4K]", "(Live)", "[Live]"
                            ]
                            
                            for pattern in cleanup_patterns:
                                track = track.replace(pattern, "").strip()
                                artist = artist.replace(pattern, "").strip()
                            
                            # Show preview
                            print(f"\n{Fore.CYAN}{'='*60}")
                            print(f"URL PREVIEW")
                            print(f"{'='*60}{Style.RESET_ALL}")
                            print(f"{Fore.GREEN}Track:{Style.RESET_ALL} {track}")
                            print(f"{Fore.GREEN}Artist:{Style.RESET_ALL} {artist}")
                            print(f"{Fore.GREEN}Duration:{Style.RESET_ALL} {duration//60}:{duration%60:02d}")
                            print(f"{Fore.GREEN}Source:{Style.RESET_ALL} {uploader}")
                            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                            
                            if input(f"\n{Fore.CYAN}Download this track? [Y/N]: {Style.RESET_ALL}").strip().lower() == "y":
                                download_url(url)
                except Exception as e:
                    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Could not extract info: {e}")
                    print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Try downloading anyway? [Y/N]")
                    if input().strip().lower() == "y":
                        download_url(url)
        
        elif c == "3":
            path = input("CSV path: ").strip()
            if path:
                process_csv(path)
        
        elif c == "4":
            path = input("TXT path: ").strip()
            if path:
                process_urls_txt(path)
        
        elif c == "5":
            aid = input("Album ID/URL or search name: ").strip()
            if aid:
                # Extract ID from URL if needed
                if "album/" in aid:
                    aid = aid.split("album/")[1].split("?")[0]
                    download_spotify_album(aid)
                else:
                    # Search by name
                    artist = input("Artist: ").strip()
                    album_id = search_spotify_album(aid, artist)
                    if album_id:
                        download_spotify_album(album_id)
        
        elif c == "6":
            pid = input("Playlist ID/URL: ").strip()
            if pid:
                # Extract ID from URL if needed
                if "playlist/" in pid:
                    pid = pid.split("playlist/")[1].split("?")[0]
                download_spotify_playlist(pid)
        
        elif c == "7":
            url = input("Playlist URL: ").strip()
            if url:
                download_youtube_playlist(url)
        
        elif c == "8":
            settings_menu()
        
        elif c == "9":
            print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Exiting... Goodbye!")
            raise SystemExit(0)
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[CANCELLED]{Style.RESET_ALL}")
    except SystemExit:
        raise  # Re-raise SystemExit to actually exit
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")

# =========================== MAIN ============================

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f" {Fore.WHITE}REEL - Starting...")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    config = load_config()
    if config:
        if config.get("LIBRARY_PATH"):
            set_dirs(config["LIBRARY_PATH"])
        if config.get("SPOTIFY_CLIENT_ID"):
            os.environ["SPOTIFY_CLIENT_ID"] = config["SPOTIFY_CLIENT_ID"]
            os.environ["SPOTIFY_CLIENT_SECRET"] = config.get("SPOTIFY_CLIENT_SECRET", "")
            sp = init_spotify()
        if config.get("GENIUS_TOKEN"):
            os.environ["GENIUS_TOKEN"] = config["GENIUS_TOKEN"]
            genius = init_genius()
    
    if not sp:
        print(f"\n{Fore.YELLOW}⚠️  Spotify API not configured!{Style.RESET_ALL}")
        print("Get credentials: https://developer.spotify.com/dashboard")
        print("Then go to Settings (Option 8)\n")
    
    try:
        while True:
            menu()
    except (KeyboardInterrupt, SystemExit):
        print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
        sys.exit(0)
