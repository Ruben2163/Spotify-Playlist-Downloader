# Spotify Playlist to MP3

## Installation Guide

### 1. Install Python Dependencies


```bash
git clone https://github.com/ruben2163/spotify-playlist-downloader
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
