from pathlib import Path
import re
import shutil
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt5.QtCore import pyqtSignal, QObject
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TPE1, TIT2, TALB

import yt_dlp
import backoff
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DEFAULT_DOWNLOAD_DIR


# ========== Utility ==========
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise EnvironmentError("ffmpeg not found. Please install ffmpeg and ensure it's in your system PATH.")


# ========== GUI Signals ==========
class SignalHandler(QObject):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal()


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
def download_from_youtube(track_info, quality, output_dir):
    check_ffmpeg()

    output_dir = Path(output_dir).expanduser().resolve()
    sanitized_name = sanitize_filename(track_info['search_query'])

    ydl_opts = {
        'format': 'bestaudio/best[ext=m4a]',
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

            # Determine the correct thumbnail source
            thumbnail_data = None
            if 'thumbnail_data' in track_info:
                thumbnail_data = track_info['thumbnail_data']
            elif 'thumbnail_url' in track_info and track_info['thumbnail_url']:
                try:
                    response = requests.get(track_info['thumbnail_url'], timeout=10)
                    response.raise_for_status()
                    thumbnail_data = response.content
                except Exception as e:
                    signals.log_signal.emit(f"⚠ Failed to download artwork: {e}")

            if thumbnail_data:
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
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
def get_playlist_tracks(playlist_url):
    if not sp:
        raise ValueError("Spotify client not configured.")
    results = sp.playlist_tracks(playlist_url)
    tracks = []
    while results:
        for item in results['items']:
            track = item['track']
            tracks.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'thumbnail_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'search_query': f"{track['name']} {track['artists'][0]['name']}"
            })
        results = sp.next(results) if results['next'] else None
    return tracks


# ========== Demo Playlist ==========
BASE_DIR = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()

DEMO_TRACKS = [
    {
        'name': "Hypnotize",
        'artist': "The Notorious B.I.G.",
        'album': "Life After Death",
        'thumbnail_url': str(BASE_DIR / 'images' / 'test_cover.jpg'),
        'search_query': "Hypnotize The Notorious B.I.G."
    },
    {
        'name': "Still D.R.E.",
        'artist': "Dr. Dre ft. Snoop Dogg",
        'album': "2001",
        'thumbnail_url': str(BASE_DIR / 'images' / 'test_cover.jpg'),
        'search_query': "Still D.R.E. Dr. Dre Snoop Dogg"
    },
]

def process_demo_playlist(quality, output_dir):
    signals.log_signal.emit("🎧 Using demo playlist")
    for track in DEMO_TRACKS:
        if track['thumbnail_url'] and Path(track['thumbnail_url']).exists():
            with open(track['thumbnail_url'], 'rb') as img:
                track['thumbnail_data'] = img.read()
        download_from_youtube(track, quality, output_dir)
    signals.done_signal.emit()


# ========== Batch Download Manager ==========
class BatchDownloader:
    def __init__(self, num_chunks=3, batch_size=5):
        self.num_chunks = num_chunks
        self.batch_size = batch_size
        self.chunk_times = {}

    def split_chunks(self, tracks):
        chunk_size = max(1, len(tracks) // self.num_chunks)
        return [tracks[i:i + chunk_size] for i in range(0, len(tracks), chunk_size)]

    def process_chunk(self, chunk, quality, output_dir, chunk_id):
        start = time.time()
        signals.log_signal.emit(f"🔄 Processing chunk {chunk_id + 1}")
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            results = list(executor.map(
                lambda track: download_from_youtube(track, quality, output_dir),
                chunk
            ))
        duration = time.time() - start
        self.chunk_times[chunk_id] = duration
        print(f"Chunk {chunk_id + 1} finished in {duration:.2f} sec")
        return results


# ========== Main Playlist Handler ==========
def process_spotify_playlist(playlist_url, quality, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    signals.log_signal.emit("📡 Fetching Spotify playlist...")
    playlist_id = playlist_url.split('/')[-1].split('?')[0]

    try:
        tracks = get_playlist_tracks(playlist_id)
    except Exception as e:
        signals.log_signal.emit(f"❌ Failed to load playlist: {e}")
        return

    if not tracks:
        signals.log_signal.emit("⚠ No tracks found.")
        return

    signals.log_signal.emit(f"✅ Found {len(tracks)} tracks")

    downloader = BatchDownloader(num_chunks=3, batch_size=5)
    chunks = downloader.split_chunks(tracks)

    total_start = time.time()
    with ThreadPoolExecutor(max_workers=downloader.num_chunks) as executor:
        futures = [
            executor.submit(downloader.process_chunk, chunk, quality, output_dir, i)
            for i, chunk in enumerate(chunks)
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                signals.log_signal.emit(f"Chunk error: {e}")

    total_time = time.time() - total_start
    print("\nDownload Stats")
    print(f"⏱ Total time: {total_time:.2f} sec")
    print(f"📦 Avg chunk time: {sum(downloader.chunk_times.values()) / len(downloader.chunk_times):.2f} sec")
    print(f"🎶 Songs per minute: {(len(tracks) / (total_time / 60)):.1f}")
    signals.done_signal.emit()
