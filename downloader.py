import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
from PyQt5.QtCore import pyqtSignal, QObject
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DEFAULT_DOWNLOAD_DIR
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from functools import partial
import backoff
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TPE1, TIT2, TALB
import requests


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

def download_from_youtube(track_info, quality, output_dir):
    ydl_opts = {
        'format': 'bestaudio/best[ext=m4a]',  # Prefer m4a format
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(quality),
        }],
        'quiet': True,
        'noplaylist': True,
        'concurrent_fragment_downloads': 10,
        'retries': 3,
        'fragment_retries': 3,
        'ignoreerrors': True,
        'socket_timeout': 10,
        'buffersize': 1024 * 16,
        'http_chunk_size': 1024 * 1024,
        'extractor_retries': 3,
        'file_access_retries': 3,
        'force_generic_extractor': False,
        'updatetime': False,
        'nocheckcertificate': True,
        'allow_unplayable_formats': True,
        'legacy_server_connect': True,
        'extract_flat': False,
        'youtube_include_dash_manifest': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def download_with_retry():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                signals.log_signal.emit(f"Downloading: {track_info['search_query']}")
                # First get search results
                search_results = ydl.extract_info(f"ytsearch:{track_info['search_query']}", download=False)
                if not search_results or not search_results.get('entries'):
                    raise Exception("No search results found")
                
                # Get the first result
                first_result = search_results['entries'][0]
                video_id = first_result.get('id')
                if not video_id:
                    raise Exception("Could not get video ID")
                
                # Get full video info using direct video URL
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(video_url, download=True)
                
                # Get the output filename
                output_file = os.path.join(output_dir, f"{info['title']}.mp3")
                
                # Add metadata
                if os.path.exists(output_file):
                    try:
                        # Remove existing ID3 tags if present
                        if os.path.exists(output_file):
                            audio = MP3(output_file)
                            audio.delete()
                            audio.save()
                        
                        # Create new ID3 tags
                        audio = MP3(output_file, ID3=ID3)
                        if audio.tags is None:
                            audio.add_tags()
                        
                        # Add title and artist
                        audio.tags.add(TIT2(encoding=3, text=track_info['name']))
                        audio.tags.add(TPE1(encoding=3, text=track_info['artist']))
                        audio.tags.add(TALB(encoding=3, text=track_info['album']))
                        
                        # Add YouTube thumbnail as album art
                        try:
                            # Try different thumbnail keys that yt-dlp might provide
                            thumbnail_url = (
                                info.get('thumbnail') or 
                                info.get('thumbnails', [{}])[-1].get('url') or
                                f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                            )
                            
                            response = requests.get(thumbnail_url, timeout=10)
                            response.raise_for_status()
                            img_data = response.content
                            
                            audio.tags.add(APIC(
                                encoding=3,
                                mime='image/jpeg',
                                type=3,
                                desc='Cover',
                                data=img_data
                            ))
                            signals.log_signal.emit(f"Added YouTube thumbnail for: {track_info['name']}")
                            
                        except Exception as e:
                            signals.log_signal.emit(f"Failed to add YouTube thumbnail for {track_info['name']}: {str(e)}")
                            
                        audio.save(v2_version=3)
                    except Exception as e:
                        signals.log_signal.emit(f"Failed to add metadata for {track_info['name']}: {str(e)}")
                
                return True
            except Exception as e:
                signals.log_signal.emit(f"Failed: {track_info['search_query']} — {e}")
                raise

    return download_with_retry()

def get_playlist_tracks(playlist_url):
    if not sp:
        raise ValueError("Spotify client is not configured")
    results = sp.playlist_tracks(playlist_url)
    tracks = []
    while results:
        for item in results['items']:
            track = item['track']
            track_info = {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'thumbnail_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'search_query': f"{track['name']} {track['artists'][0]['name']}"
            }
            tracks.append(track_info)
        results = sp.next(results) if results['next'] else None
    return tracks

# Demo tracks for offline test
DEMO_TRACKS = [
    {
        'name': "Hypnotize",
        'artist': "The Notorious B.I.G.",
        'album': "Life After Death",
        'thumbnail_url': os.path.join(os.path.dirname(__file__), 'images', 'test_cover.jpg'),
        'search_query': "Hypnotize The Notorious B.I.G."
    },
    {
        'name': "Still D.R.E.",
        'artist': "Dr. Dre ft. Snoop Dogg",
        'album': "2001",
        'thumbnail_url': os.path.join(os.path.dirname(__file__), 'images', 'test_cover.jpg'),
        'search_query': "Still D.R.E. Dr. Dre Snoop Dogg"
    },
    # ...add more tracks with the same pattern
]

def process_demo_playlist(quality, output_dir):
    start = time.time()
    signals.log_signal.emit("Using demo playlist...")
    for track in DEMO_TRACKS:
        # For local files, read the image data directly instead of downloading
        if track['thumbnail_url'] and os.path.exists(track['thumbnail_url']):
            with open(track['thumbnail_url'], 'rb') as img_file:
                track['thumbnail_data'] = img_file.read()
        download_from_youtube(track, quality, output_dir)
    signals.done_signal.emit()
    end = time.time()
    print(end-start)

class BatchDownloader:
    def __init__(self, num_chunks=3, batch_size=5):
        self.num_chunks = num_chunks
        self.batch_size = batch_size
        self.chunk_times = {}
        
    def split_into_chunks(self, tracks):
        chunk_size = len(tracks) // self.num_chunks
        return [tracks[i:i + chunk_size] for i in range(0, len(tracks), chunk_size)]
        
    def process_chunk(self, chunk, quality, output_dir, chunk_id):
        start_time = time.time()
        signals.log_signal.emit(f"Processing chunk {chunk_id + 1}")
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            result = list(executor.map(
                lambda track: download_from_youtube(track, quality, output_dir),
                chunk
            ))
        elapsed = time.time() - start_time
        self.chunk_times[chunk_id] = elapsed
        print(f"Chunk {chunk_id + 1} completed in {elapsed:.2f} seconds")
        return result

def process_spotify_playlist(playlist_url, quality, output_dir):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        total_start = time.time()
        signals.log_signal.emit("🎵 Fetching playlist from Spotify...")
        
        # Extract playlist ID from URL
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        
        try:
            tracks = get_playlist_tracks(playlist_id)
        except Exception as e:
            signals.log_signal.emit(f"❌ Failed to fetch playlist: {str(e)}")
            return
            
        signals.log_signal.emit(f"✅ Found {len(tracks)} tracks")
        
        if not tracks:
            signals.log_signal.emit("❌ No tracks found in playlist")
            return
            
        batch_downloader = BatchDownloader(num_chunks=3, batch_size=5)
        chunks = batch_downloader.split_into_chunks(tracks)
        
        with ThreadPoolExecutor(max_workers=batch_downloader.num_chunks) as chunk_executor:
            futures = [
                chunk_executor.submit(
                    batch_downloader.process_chunk, 
                    chunk, 
                    quality, 
                    output_dir, 
                    i
                ) for i, chunk in enumerate(chunks)
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    signals.log_signal.emit(f"Chunk Error: {str(e)}")
        
        total_time = time.time() - total_start
        print(f"\nDownload Statistics:")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average chunk time: {sum(batch_downloader.chunk_times.values())/len(batch_downloader.chunk_times):.2f} seconds")
        print(f"Songs per minute: {(len(tracks)/(total_time/60)):.1f}")
                    
    except Exception as e:
        signals.log_signal.emit(f"Error: {e}")
    finally:
        signals.done_signal.emit()
