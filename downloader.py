import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
from PyQt5.QtCore import pyqtSignal, QObject
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DEFAULT_DOWNLOAD_DIR
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from functools import partial
import backoff
import time


# Signal emitter to connect logic and GUI
class SignalHandler(QObject):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal()

signals = SignalHandler()

# Setup Spotify client
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

def download_from_youtube(query, quality, output_dir):
    ydl_opts = {
        'format': 'bestaudio/best[ext=m4a]',  # Prefer m4a format
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(quality),
        }],
        'quiet': True,
        'noplaylist': True,
        'concurrent_fragment_downloads': 10,
        'retries': 3,
        'fragment_retries': 3,
        'ignoreerrors': True,
        'socket_timeout': 10,
        'buffersize': 1024 * 16,
        'http_chunk_size': 1024 * 1024,
        'extractor_retries': 3,
        'file_access_retries': 3,
        'force_generic_extractor': False,
        'updatetime': False,
        'nocheckcertificate': True,
        'allow_unplayable_formats': True,
        'legacy_server_connect': True,
        'extract_flat': False,
        'youtube_include_dash_manifest': True,
        'no_warnings': True
    }
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def download_with_retry():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                signals.log_signal.emit(f"Downloading: {query}")
                ydl.download([f"ytsearch:{query}"])
                return True
            except Exception as e:
                signals.log_signal.emit(f"Failed: {query} — {e}")
                raise

    return download_with_retry()

def get_playlist_tracks(playlist_url):
    if not sp:
        raise ValueError("Spotify client is not configured")
    results = sp.playlist_tracks(playlist_url)
    tracks = []
    while results:
        for item in results['items']:
            track = item['track']
            name = track['name']
            artist = track['artists'][0]['name']
            tracks.append(f"{name} {artist}")
        results = sp.next(results) if results['next'] else None
    return tracks

# Demo tracks for offline test
DEMO_TRACKS = [
    "Hypnotize The Notorious B.I.G.",
    "Still D.R.E. Dr. Dre Snoop Dogg",
    "X Gon Give it to ya DMX",
    "99 Problems JAY-Z",
    "Gold Digger Kanye West Jamie Foxx",
    "Gin and Juice Snoop Dogg"
]


def process_demo_playlist(quality, output_dir):
    start = time.time()
    signals.log_signal.emit("Using demo playlist...")
    for track in DEMO_TRACKS:
        download_from_youtube(track, quality, output_dir)
    signals.done_signal.emit()
    end = time.time()
    print(end-start)

class BatchDownloader:
    def __init__(self, num_chunks=3, batch_size=5):
        self.num_chunks = num_chunks
        self.batch_size = batch_size
        self.chunk_times = {}
        
    def split_into_chunks(self, tracks):
        chunk_size = len(tracks) // self.num_chunks
        return [tracks[i:i + chunk_size] for i in range(0, len(tracks), chunk_size)]
        
    def process_chunk(self, chunk, quality, output_dir, chunk_id):
        start_time = time.time()
        signals.log_signal.emit(f"Processing chunk {chunk_id + 1}")
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            result = list(executor.map(
                lambda track: download_from_youtube(track, quality, output_dir),
                chunk
            ))
        elapsed = time.time() - start_time
        self.chunk_times[chunk_id] = elapsed
        print(f"Chunk {chunk_id + 1} completed in {elapsed:.2f} seconds")
        return result

def process_spotify_playlist(playlist_url, quality, output_dir):
    try:
        total_start = time.time()
        signals.log_signal.emit("Fetching playlist from Spotify...")
        tracks = get_playlist_tracks(playlist_url)
        signals.log_signal.emit(f"Found {len(tracks)} tracks.")
        
        batch_downloader = BatchDownloader(num_chunks=3, batch_size=5)
        chunks = batch_downloader.split_into_chunks(tracks)
        
        with ThreadPoolExecutor(max_workers=batch_downloader.num_chunks) as chunk_executor:
            futures = [
                chunk_executor.submit(
                    batch_downloader.process_chunk, 
                    chunk, 
                    quality, 
                    output_dir, 
                    i
                ) for i, chunk in enumerate(chunks)
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    signals.log_signal.emit(f"Chunk Error: {str(e)}")
        
        total_time = time.time() - total_start
        print(f"\nDownload Statistics:")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average chunk time: {sum(batch_downloader.chunk_times.values())/len(batch_downloader.chunk_times):.2f} seconds")
        print(f"Songs per minute: {(len(tracks)/(total_time/60)):.1f}")
                    
    except Exception as e:
        signals.log_signal.emit(f"Error: {e}")
    finally:
        signals.done_signal.emit()
