# 🎵 Spotify Playlist Downloader

A cross-platform GUI application to download Spotify playlists and albums as MP3 files with metadata and artwork. Works on Windows, macOS, and Linux.

## ✨ Features

- **Cross-platform**: Windows, macOS, Linux support
- **Spotify Integration**: Download playlists and albums directly from Spotify URLs
- **High Quality Audio**: Download at 128, 192, 256, or 320 kbps
- **Metadata & Artwork**: Automatic tagging with track info and album artwork
- **Demo Mode**: Test the app without Spotify credentials
- **Batch Processing**: Handles large playlists efficiently
- **User-friendly GUI**: Clean, intuitive interface with progress indicators

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
python setup.py
```

### Option 2: Manual Setup
1. Install Python 3.8+
2. Install dependencies: `pip install -r requirements.txt`
3. Install ffmpeg (see platform instructions below)
4. Set up Spotify API credentials (see below)
5. Run: `python main.py`

## 🔧 Platform-Specific Installation

### Windows
```bash
# Install Python from python.org
# Install ffmpeg:
# Option 1: Download from https://ffmpeg.org/download.html
# Option 2: Use chocolatey: choco install ffmpeg

# Run setup
python setup.py
```

### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ffmpeg
brew install ffmpeg

# Run setup
python setup.py
```

### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip ffmpeg

# Run setup
python3 setup.py
```

### Linux (CentOS/RHEL/Fedora)
```bash
# CentOS/RHEL
sudo yum install python3-pip ffmpeg

# Fedora
sudo dnf install python3-pip ffmpeg

# Run setup
python3 setup.py
```

## 🔑 Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Click "Create App"
3. Fill in app details:
   - App name: "My Playlist Downloader"
   - App description: "Personal use"
4. Copy your **Client ID** and **Client Secret**
5. Edit the `.env` file:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
DEFAULT_DOWNLOAD_DIR=downloads
```

## 📱 How to Use

1. **Launch the app**: `python main.py` or double-click `run.bat` (Windows)
2. **Get Spotify credentials** (see instructions above)
3. **Paste a Spotify URL**:
   - Playlist: `https://open.spotify.com/playlist/...`
   - Album: `https://open.spotify.com/album/...`
4. **Choose quality**: 128-320 kbps
5. **Select download folder**
6. **Click "Start Download"**

### Demo Mode
- Check "Use demo playlist" to test without Spotify credentials
- Downloads 2 sample tracks with YouTube thumbnails

## 🛠️ Troubleshooting

### Common Issues

**"ffmpeg not found"**
- Windows: Download from ffmpeg.org and add to PATH
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg` (Ubuntu) or equivalent

**"Spotify client not configured"**
- Check your `.env` file has correct credentials
- Make sure there are no extra spaces in the values

**"No tracks found"**
- Verify the Spotify URL is correct
- Check if the playlist/album is public
- Try demo mode first

**Download fails**
- Check your internet connection
- Some tracks may not be available on YouTube
- Try reducing the quality setting

### Platform-Specific Issues

**Windows:**
- If you get "python not found", add Python to your PATH
- Use `python.exe` instead of `python` if needed

**macOS:**
- If you get permission errors, try `python3` instead of `python`
- You may need to allow the app in Security & Privacy settings

**Linux:**
- Use `python3` instead of `python`
- You may need `sudo` for system-wide package installation

## 📁 File Structure

```
spotify-playlist-downloader/
├── main.py              # Main application entry point
├── gui.py               # GUI interface
├── downloader.py        # Core download logic
├── config.py            # Configuration management
├── setup.py             # Cross-platform setup script
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── downloads/           # Default download folder
└── README.md           # This file
```

## 🔒 Legal Notice

This tool is for personal use only. Please respect copyright laws and Spotify's Terms of Service. Only download content you have the right to access.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on your platform
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run `python setup.py` to verify your setup
3. Check that all dependencies are installed
4. Verify your Spotify credentials are correct

For more help, open an issue on GitHub with:
- Your operating system
- Python version
- Error messages
- Steps to reproduce the issue