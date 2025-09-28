#!/usr/bin/env python3
"""
YouTube Cookie Extractor for Spotify Playlist Downloader

This script helps extract cookies from your browser to bypass YouTube's bot detection.
"""

import os
import sys
from pathlib import Path

def extract_cookies_instructions():
    """Print instructions for extracting cookies from browsers."""
    print("YouTube Cookie Extraction Instructions")
    print("=" * 50)
    print()
    print("To bypass YouTube's bot detection, you need to extract cookies from your browser.")
    print("Here are the methods for different browsers:")
    print()
    
    print("📋 METHOD 1: Using Browser Extensions (Recommended)")
    print("-" * 45)
    print("1. Install 'Get cookies.txt' extension for Chrome/Firefox:")
    print("   Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid")
    print("   Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt/")
    print()
    print("2. Go to YouTube.com and sign in to your account")
    print("3. Click the extension icon and select 'Export as cookies.txt'")
    print("4. Save the file as 'youtube_cookies.txt' in this directory")
    print()
    
    print("📋 METHOD 2: Using yt-dlp's built-in browser support")
    print("-" * 50)
    print("1. Install browser-cookie3:")
    print("   pip install browser-cookie3")
    print()
    print("2. Run this command to extract cookies:")
    print("   yt-dlp --cookies-from-browser chrome youtube.com")
    print("   (Replace 'chrome' with 'firefox', 'safari', or 'edge' as needed)")
    print()
    print("3. The cookies will be saved automatically")
    print()
    
    print("📋 METHOD 3: Manual Cookie Export")
    print("-" * 35)
    print("1. Open your browser's Developer Tools (F12)")
    print("2. Go to YouTube.com and sign in")
    print("3. In Developer Tools, go to Application/Storage > Cookies > https://youtube.com")
    print("4. Copy all cookies and save them in Netscape format as 'youtube_cookies.txt'")
    print()
    
    print("🔧 Configuration")
    print("-" * 15)
    print("Once you have the cookies file:")
    print("1. Place 'youtube_cookies.txt' in this directory")
    print("2. Or set the YOUTUBE_COOKIES_FILE environment variable to point to your cookies file")
    print("3. Run the playlist downloader - it will automatically use the cookies")
    print()
    
    print("⚠️  Important Notes:")
    print("- Cookies expire periodically, so you may need to refresh them")
    print("- Keep your cookies file secure and don't share it")
    print("- The cookies file should be in Netscape format")
    print()

def check_cookies_file():
    """Check if cookies file exists and provide guidance."""
    cookies_file = Path("youtube_cookies.txt")
    
    if cookies_file.exists():
        print(f"✅ Found cookies file: {cookies_file.absolute()}")
        print(f"📏 File size: {cookies_file.stat().st_size} bytes")
        
        # Check if it's a valid cookies file
        try:
            with open(cookies_file, 'r') as f:
                content = f.read()
                if '# Netscape HTTP Cookie File' in content or 'youtube.com' in content:
                    print("✅ Cookies file appears to be valid")
                else:
                    print("⚠️  Cookies file may not be in the correct format")
        except Exception as e:
            print(f"❌ Error reading cookies file: {e}")
    else:
        print("❌ No cookies file found")
        print("📝 Please follow the instructions above to extract cookies")

def main():
    """Main function."""
    print("YouTube Cookie Extractor for Spotify Playlist Downloader")
    print("=" * 60)
    print()
    
    extract_cookies_instructions()
    check_cookies_file()
    
    print("🚀 Ready to download! Run the playlist downloader to start.")

if __name__ == "__main__":
    main()
