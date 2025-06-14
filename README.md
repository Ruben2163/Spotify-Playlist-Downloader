# Spotify Playlist to MP3

## Features

- PyQt5 GUI interface
- MP3 conversion with FFmpeg
- Auto-retry on failed downloads
- Progress tracking per song and chunk
- Spotify API integration

---

## Getting Started

### 1. Requirements

- Python 3.8 or higher
- FFmpeg installed and in PATH
- Spotify Developer account

### 2. Installation

```bash
git clone https://git.rubenphagura.com/Spotify-Playlist-Downloader
cd Spotify-playlist-downloader
pip install -r requirements.txt
```

## 📥 Complete Installation Guide

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg

#### Windows:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the archive
3. Add FFmpeg's bin folder to System PATH
4. Verify installation: `ffmpeg -version`

#### macOS:
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. Configure Spotify API
1. Go to https://developer.spotify.com/dashboard
2. Create a new app
3. Copy the Client ID and Client Secret
4. Create a `.env` file in project root:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here
DEFAULT_DOWNLOAD_DIR=downloads
```

### 4. Run the Application
```bash
python main.py
```

### 3. Configuration

Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
DEFAULT_DOWNLOAD_DIR=downloads
NUM_CHUNKS=3  # Optional: Number of parallel chunks
BATCH_SIZE=5  # Optional: Songs per chunk
```

### 4. Spotify Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Copy your Client ID and Client Secret
4. Paste them in your `.env` file

### Using with Spotify

1. Open the application using `python3 main.py`
2. Find your Spotify playlist URL:
   - Open Spotify
   - Right-click on a playlist
   - Select "Share" → "Copy link to playlist"
3. In the application:
   - Paste the Spotify playlist URL
   - Choose your desired MP3 quality (128-320kbps)
   - Select output directory
   - Click "Download"

The app will:
- Fetch all tracks from your Spotify playlist
- Find matching songs on YouTube
- Download and convert them to MP3
- Add metadata (title, artist, album)
- Add thumbnails from YouTube

### Performance

The downloader processes songs in parallel chunks:
- Multiple songs downloaded simultaneously
- Automatic chunk-based processing
- Real-time performance statistics:
  - Total download time
  - Per-chunk timing
  - Songs per minute rate
  - Average chunk processing time

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
