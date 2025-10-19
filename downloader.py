from pathlib import Path
import base64
import re
import shutil
import time
import requests
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt5.QtCore import pyqtSignal, QObject
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TPE1, TIT2, TALB

import yt_dlp
import backoff
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


# ========== Utility ==========
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def save_playlist_to_csv(tracks, output_dir):
    csv_path = Path(output_dir) / "playlist.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'artist', 'album', 'thumbnail_url', 'search_query', 'downloaded'])
        writer.writeheader()
        for track in tracks:
            track['downloaded'] = False
            writer.writerow(track)
    return csv_path


def load_playlist_from_csv(csv_path):
    tracks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['downloaded'] = row['downloaded'].lower() == 'true'
            tracks.append(row)
    return tracks


def update_track_status(csv_path, track_name, downloaded=True):
    tracks = load_playlist_from_csv(csv_path)
    for track in tracks:
        if track['name'] == track_name:
            track['downloaded'] = downloaded
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'artist', 'album', 'thumbnail_url', 'search_query', 'downloaded'])
        writer.writeheader()
        writer.writerows(tracks)


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise EnvironmentError("ffmpeg not found. Please install ffmpeg and ensure it's in your system PATH.")


# ========== GUI Signals ==========
class SignalHandler(QObject):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal()
    batch_complete_signal = pyqtSignal()


signals = SignalHandler()

# ========== Spotify Setup ==========
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

# ========== Download Logic ==========
@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def download_from_youtube(track_info, quality, output_dir, csv_path=None):
    check_ffmpeg()

    output_dir = Path(output_dir).expanduser().resolve()
    sanitized_name = sanitize_filename(track_info['search_query'])

    # Skip if already downloaded
    final_name = f"{sanitized_name}.mp3"
    if (output_dir / final_name).exists():
        signals.log_signal.emit(f"⏩ Skipping already downloaded: {track_info['name']}")
        if csv_path:
            update_track_status(csv_path, track_info['name'])
        return True

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': str(output_dir / f"{sanitized_name}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(quality),
        }],
        'quiet': True,
        'noplaylist': True,
        'retries': 3,
        'ignoreerrors': True,
        'socket_timeout': 10,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        signals.log_signal.emit(f"🎵 Downloading: {track_info['search_query']}")
        search = ydl.extract_info(f"ytsearch:{track_info['search_query']}", download=False)
        if not search or not search.get('entries'):
            raise Exception("No YouTube search results found")
        result = search['entries'][0]
        video_url = f"https://www.youtube.com/watch?v={result['id']}"
        info = ydl.extract_info(video_url, download=True)

        final_name = f"{sanitize_filename(track_info['search_query'])}.mp3"
        mp3_file = output_dir / final_name

        # If file doesn't exist, try to find and rename the one yt_dlp created
        if not mp3_file.exists():
            for f in output_dir.glob("*.mp3"):
                if sanitize_filename(info['title']) in f.stem:
                    f.rename(mp3_file)
                    break
            else:
                raise FileNotFoundError(f"Expected MP3 not found or renamed: {mp3_file}")


        try:
            audio = MP3(mp3_file, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            else:
                audio.delete()
                audio.save()

            audio.tags.add(TIT2(encoding=3, text=track_info['name']))
            audio.tags.add(TPE1(encoding=3, text=track_info['artist']))
            audio.tags.add(TALB(encoding=3, text=track_info['album']))

            # Determine the correct thumbnail source (supports http(s) and local file paths)
            thumbnail_data = None
            thumbnail_mime = 'image/jpeg'
            if 'thumbnail_data' in track_info and track_info['thumbnail_data']:
                thumbnail_data = track_info['thumbnail_data']
            elif 'thumbnail_url' in track_info and track_info['thumbnail_url']:
                thumb = track_info['thumbnail_url']
                try:
                    if isinstance(thumb, str) and (thumb.startswith('http://') or thumb.startswith('https://')):
                        response = requests.get(thumb, timeout=10)
                        response.raise_for_status()
                        thumbnail_data = response.content
                        # best guess for remote images
                        if response.headers.get('Content-Type'):
                            thumbnail_mime = response.headers.get('Content-Type')
                    else:
                        thumb_path = Path(thumb)
                        if thumb_path.exists() and thumb_path.is_file():
                            with open(thumb_path, 'rb') as f:
                                thumbnail_data = f.read()
                            # Set mime from extension if possible
                            ext = thumb_path.suffix.lower()
                            if ext == '.png':
                                thumbnail_mime = 'image/png'
                            elif ext in ('.jpg', '.jpeg'):
                                thumbnail_mime = 'image/jpeg'
                        else:
                            signals.log_signal.emit(f"⚠ Artwork path not found or invalid: {thumb}")
                except Exception as e:
                    signals.log_signal.emit(f"⚠ Failed to load artwork: {e}")

            # Try falling back to YouTube thumbnail if none provided/loaded
            if not thumbnail_data and isinstance(info, dict):
                yt_thumb = info.get('thumbnail')
                if not yt_thumb:
                    thumbs = info.get('thumbnails') or []
                    if isinstance(thumbs, list) and thumbs:
                        try:
                            yt_thumb = sorted(
                                thumbs,
                                key=lambda t: ((t.get('height') or 0) * (t.get('width') or 0))
                            )[-1].get('url')
                        except Exception:
                            yt_thumb = thumbs[-1].get('url') if isinstance(thumbs[-1], dict) else None
                if yt_thumb:
                    try:
                        response = requests.get(yt_thumb, timeout=10)
                        response.raise_for_status()
                        thumbnail_data = response.content
                        if response.headers.get('Content-Type'):
                            thumbnail_mime = response.headers.get('Content-Type')
                    except Exception as e:
                        signals.log_signal.emit(f"⚠ Failed to fetch YouTube artwork: {e}")

            # Fallback to a tiny 1x1 PNG to avoid missing artwork when desired file isn't available
            if not thumbnail_data:
                try:
                    tiny_png_base64 = (
                        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAucB9Ue0mD0AAAAASUVORK5CYII='
                    )
                    thumbnail_data = base64.b64decode(tiny_png_base64)
                    thumbnail_mime = 'image/png'
                except Exception:
                    thumbnail_data = None

            if thumbnail_data:
                audio.tags.add(APIC(
                    encoding=3,
                    mime=thumbnail_mime,
                    type=3,
                    desc='Cover',
                    data=thumbnail_data
                ))
                signals.log_signal.emit(f"🖼 Added artwork to: {track_info['name']}")
            else:
                signals.log_signal.emit(f"⚠ No artwork found for: {track_info['name']}")

            audio.save(v2_version=3)

        except Exception as e:
            signals.log_signal.emit(f"❌ Metadata error for {track_info['name']}: {e}")

    return True

# ========== Spotify Playlist ==========
def get_playlist_tracks(playlist_id_or_url):
    if not sp:
        raise ValueError("Spotify client not configured.")
    results = sp.playlist_tracks(playlist_id_or_url)
    tracks = []
    while results:
        for item in results['items']:
            track = item['track']
            if not track:
                continue
            tracks.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'thumbnail_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'search_query': f"{track['name']} {track['artists'][0]['name']}"
            })
        results = sp.next(results) if results and results.get('next') else None
    return tracks


def get_album_tracks(album_id_or_url):
    if not sp:
        raise ValueError("Spotify client not configured.")
    # Fetch album for cover art and name
    album = sp.album(album_id_or_url)
    album_name = album.get('name')
    album_images = album.get('images') or []
    album_cover = album_images[0]['url'] if album_images else None

    results = sp.album_tracks(album_id_or_url)
    tracks = []
    while results:
        for item in results['items']:
            artists = item['artists']
            primary_artist = artists[0]['name'] if artists else ''
            tracks.append({
                'name': item['name'],
                'artist': primary_artist,
                'album': album_name,
                'thumbnail_url': album_cover,
                'search_query': f"{item['name']} {primary_artist}"
            })
        results = sp.next(results) if results and results.get('next') else None
    return tracks


# ========== Demo Playlist ==========
BASE_DIR = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()

DEMO_TRACKS = [
    {
        'name': "Hypnotize",
        'artist': "The Notorious B.I.G.",
        'album': "Life After Death",
        'thumbnail_url': None,  # Let YouTube thumbnail be used
        'search_query': "Hypnotize The Notorious B.I.G."
    },
    {
        'name': "Still D.R.E.",
        'artist': "Dr. Dre ft. Snoop Dogg",
        'album': "2001",
        'thumbnail_url': None,  # Let YouTube thumbnail be used
        'search_query': "Still D.R.E. Dr. Dre Snoop Dogg"
    },
]

def process_demo_playlist(quality, output_dir):
    signals.log_signal.emit("🎧 Using demo playlist")
    for track in DEMO_TRACKS:
        try:
            download_from_youtube(track, quality, output_dir)
        except Exception as e:
            signals.log_signal.emit(f"❌ Demo download error for {track.get('name', 'Unknown')}: {e}")
    signals.done_signal.emit()


# ========== Batch Download Manager ==========
class BatchDownloader:
    def __init__(self, batch_size=200, delay_minutes=5):
        self.batch_size = batch_size
        self.delay_minutes = delay_minutes
        self.chunk_times = {}

    def process_tracks(self, tracks, quality, output_dir):
        csv_path = save_playlist_to_csv(tracks, output_dir)
        remaining_tracks = load_playlist_from_csv(csv_path)
        remaining_tracks = [t for t in remaining_tracks if not t['downloaded']]
        
        total_batches = (len(remaining_tracks) + self.batch_size - 1) // self.batch_size
        signals.log_signal.emit(f"📦 Processing {len(remaining_tracks)} tracks in {total_batches} batches")

        for batch_num, i in enumerate(range(0, len(remaining_tracks), self.batch_size), 1):
            batch = remaining_tracks[i:i + self.batch_size]
            signals.log_signal.emit(f"🔄 Starting batch {batch_num}/{total_batches}")
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(download_from_youtube, track, quality, output_dir, csv_path)
                    for track in batch
                ]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        signals.log_signal.emit(f"❌ Download error: {e}")

            signals.log_signal.emit(f"✅ Completed batch {batch_num}/{total_batches}")
            signals.batch_complete_signal.emit()
            
            if batch_num < total_batches:
                delay = self.delay_minutes * 60
                signals.log_signal.emit(f"⏳ Waiting {self.delay_minutes} minutes before next batch...")
                time.sleep(delay)


# ========== Main Playlist Handler ==========
def process_spotify_playlist(playlist_or_album_url, quality, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    is_album = 'spotify.com/album/' in playlist_or_album_url or '/album/' in playlist_or_album_url
    entity = 'album' if is_album else 'playlist'
    signals.log_signal.emit(f"📡 Fetching Spotify {entity}...")

    # Extract ID from URL
    entity_id = playlist_or_album_url.split('/')[-1].split('?')[0]

    try:
        tracks = get_album_tracks(entity_id) if is_album else get_playlist_tracks(entity_id)
    except Exception as e:
        signals.log_signal.emit(f"❌ Failed to load {entity}: {e}")
        return

    if not tracks:
        signals.log_signal.emit("⚠ No tracks found.")
        return

    signals.log_signal.emit(f"✅ Found {len(tracks)} tracks")

    downloader = BatchDownloader(batch_size=200, delay_minutes=5)
    downloader.process_tracks(tracks, quality, output_dir)
    signals.done_signal.emit()
