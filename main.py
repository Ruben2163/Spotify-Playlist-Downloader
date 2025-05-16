import os
import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel
)
from PyQt5.QtCore import pyqtSignal, QObject

import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_CLIENT_ID = 'your_spotify_client_id'
SPOTIFY_CLIENT_SECRET = 'your_spotify_client_secret'
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

class SignalHandler(QObject):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal()

signals = SignalHandler()

def get_playlist_tracks(playlist_url):
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

def download_from_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            signals.log_signal.emit(f"Downloading: {query}")
            ydl.download([f"ytsearch:{query}"])
        except Exception as e:
            signals.log_signal.emit(f"Failed: {query} — {e}")

def process_playlist(playlist_url):
    try:
        signals.log_signal.emit("Fetching playlist...")
        tracks = get_playlist_tracks(playlist_url)
        signals.log_signal.emit(f"Found {len(tracks)} tracks.")

        for track in tracks:
            download_from_youtube(track)

        signals.log_signal.emit("Download complete!")
    except Exception as e:
        signals.log_signal.emit(f"Error: {e}")
    finally:
        signals.done_signal.emit()

class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Playlist to MP3 Downloader")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()

        self.label = QLabel("Enter Spotify Playlist URL:")
        layout.addWidget(self.label)

        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)

        self.start_button = QPushButton("Start Download")
        self.start_button.clicked.connect(self.start_download)
        layout.addWidget(self.start_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

        signals.log_signal.connect(self.append_log)
        signals.done_signal.connect(self.on_done)

    def append_log(self, text):
        self.log_output.append(text)

    def on_done(self):
        self.start_button.setEnabled(True)
        self.append_log("Finished")

    def start_download(self):
        playlist_url = self.url_input.text().strip()
        if not playlist_url:
            self.append_log("invalid Spotify playlist URL.")
            return

        self.log_output.clear()
        self.start_button.setEnabled(False)

        thread = threading.Thread(target=process_playlist, args=(playlist_url,))
        thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloaderApp()
    window.show()
    sys.exit(app.exec_())
