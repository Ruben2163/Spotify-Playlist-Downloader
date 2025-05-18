from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('', ['requirements.txt', '.env']),
    ('images', ['images/test_cover.jpg']),
]
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'PyQt5',
        'yt_dlp',
        'spotipy',
        'mutagen',
        'backoff',
        'requests',
        'dotenv'
    ],
    'iconfile': 'app_icon.icns',
    'plist': {
        'CFBundleName': 'Spotify to MP3',
        'CFBundleShortVersionString': '1.0',
        'CFBundleVersion': '1.0.0',
        'LSMinimumSystemVersion': '10.12',
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name="Spotify to MP3"
)
