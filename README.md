# Spotify Playlist to MP3

-  Fetch tracks from a **Spotify playlist**
- Search and download the **best matching version from YouTube**
- Convert the video to **MP3 using FFmpeg**
- Easily use the app with a **PyQt5 GUI**

## 📦 Features

- PyQt5 GUI interface
- Concurrent downloads for maximum speed
- MP3 conversion with FFmpeg
- Auto-retry on failed downloads
- Progress tracking per song
- Spotify API integration

---

## 🚀 Getting Started

### 1. Requirements

- Python 3.8 or higher
- FFmpeg installed and in PATH
- Spotify Developer account

### 2. Installation

```bash
git clone https://git.rubenphagura.com/SPOT-PLIST
cd SPOT-PLIST
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
DEFAULT_DOWNLOAD_DIR=downloads
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

## Run

Run using:
```bash
python3 main.py
```
