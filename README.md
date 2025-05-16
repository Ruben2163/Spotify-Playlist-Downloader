# Spotify Playlist to MP3

-  Fetch tracks from a **Spotify playlist**
- Search and download the **best matching version from YouTube**
- Convert the video to **MP3 using FFmpeg**
- Easily use the app with a **PyQt5 GUI**


## 📦 Features

- PyQt5 GUI interface
- MP3 conversion with FFmpeg
- Multi-track download support
- Progress log window
- Spotify API integration

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://git.rubenphagura.com/SPOT-PLIST
cd SPOT-PLIST 
```
## Usage

### Install FFmpeg
You must have FFmpeg installed and available in your system PATH.

Windows: Download from https://ffmpeg.org/download.html and add it to your system's environment variables.
macOS:
```bash
brew install ffmpeg
```
Linux:
```bash
sudo apt install ffmpeg
```
## Setup Spotify API Credentials
Create a Spotify Developer app at developer.spotify.com:

Go to Dashboard → Create App
Get Client ID and Client Secret
Edit main.py and at the top edit:

SPOTIFY_CLIENT_ID = 'your_spotify_client_id'

SPOTIFY_CLIENT_SECRET = 'your_spotify_client_secret'

## Run

Run using:
```bash
python3 main.py
```
