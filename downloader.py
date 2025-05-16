import os
import yt_dlp
from PyQt5.QtCore import pyqtSignal, QObject
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DEFAULT_DOWNLOAD_DIR
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(quality),
        }],
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            signals.log_signal.emit(f"🔎 Downloading: {query}")
            ydl.download([f"ytsearch:{query}"])
        except Exception as e:
            signals.log_signal.emit(f"❌ Failed: {query} — {e}")

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
    "Blinding Lights The Weeknd",
    "Levitating Dua Lipa"
]

def process_demo_playlist(quality, output_dir):
    signals.log_signal.emit("🎧 Using demo playlist...")
    for track in DEMO_TRACKS:
        download_from_youtube(track, quality, output_dir)
    signals.done_signal.emit()

def process_spotify_playlist(playlist_url, quality, output_dir):
    try:
        signals.log_signal.emit("📡 Fetching playlist from Spotify...")
        tracks = get_playlist_tracks(playlist_url)
        signals.log_signal.emit(f"🎶 Found {len(tracks)} tracks.")
        for track in tracks:
            download_from_youtube(track, quality, output_dir)
    except Exception as e:
        signals.log_signal.emit(f"❌ Error: {e}")
    finally:
        signals.done_signal.emit()
