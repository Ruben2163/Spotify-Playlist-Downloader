#!/usr/bin/env python3
"""
Spotify Playlist Downloader - Setup Script
Cross-platform installer for Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_requirements():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_ffmpeg():
    """Check if ffmpeg is available"""
    import shutil
    if shutil.which("ffmpeg"):
        print("✅ ffmpeg found in PATH")
        return True
    else:
        print("⚠️  ffmpeg not found in PATH")
        return False

def get_ffmpeg_instructions():
    """Get platform-specific ffmpeg installation instructions"""
    system = platform.system().lower()
    
    instructions = {
        'windows': """
🔧 To install ffmpeg on Windows:
1. Download from: https://ffmpeg.org/download.html#build-windows
2. Extract to C:\\ffmpeg
3. Add C:\\ffmpeg\\bin to your PATH environment variable
4. Restart your terminal/command prompt

Alternative: Use chocolatey: choco install ffmpeg
""",
        'darwin': """
🔧 To install ffmpeg on macOS:
1. Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
2. Install ffmpeg: brew install ffmpeg

Alternative: Download from https://evermeet.cx/ffmpeg/
""",
        'linux': """
🔧 To install ffmpeg on Linux:
Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg
CentOS/RHEL: sudo yum install ffmpeg
Fedora: sudo dnf install ffmpeg
Arch: sudo pacman -S ffmpeg
"""
    }
    
    return instructions.get(system, "Please install ffmpeg from https://ffmpeg.org/download.html")

def create_env_template():
    """Create .env template if it doesn't exist"""
    env_path = Path(".env")
    if not env_path.exists():
        print("\n📝 Creating .env template...")
        env_content = """# Spotify API Credentials
# Get these from: https://developer.spotify.com/dashboard/applications
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here

# Default download directory (optional)
DEFAULT_DOWNLOAD_DIR=downloads
"""
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ Created .env template")
        print("⚠️  Please edit .env with your Spotify API credentials")
    else:
        print("✅ .env file already exists")

def create_launcher_scripts():
    """Create platform-specific launcher scripts"""
    system = platform.system().lower()
    
    if system == 'windows':
        # Create Windows batch file
        with open('run.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('python main.py\n')
            f.write('pause\n')
        print("✅ Created run.bat launcher")
    
    # Create cross-platform Python launcher
    with open('run.py', 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('import sys\n')
        f.write('from main import *\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    app = QApplication(sys.argv)\n')
        f.write('    window = DownloaderApp()\n')
        f.write('    window.show()\n')
        f.write('    sys.exit(app.exec_())\n')
    
    # Make executable on Unix systems
    if system != 'windows':
        os.chmod('run.py', 0o755)
    
    print("✅ Created run.py launcher")

def main():
    """Main setup function"""
    print("🎵 Spotify Playlist Downloader Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Check ffmpeg
    ffmpeg_available = check_ffmpeg()
    if not ffmpeg_available:
        print(get_ffmpeg_instructions())
    
    # Create .env template
    create_env_template()
    
    # Create launcher scripts
    create_launcher_scripts()
    
    print("\n" + "=" * 40)
    print("🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env with your Spotify API credentials")
    print("2. Install ffmpeg if not already installed")
    print("3. Run the app:")
    if platform.system().lower() == 'windows':
        print("   - Double-click run.bat, or")
        print("   - Run: python main.py")
    else:
        print("   - Run: python main.py, or")
        print("   - Run: ./run.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)