import os
import shutil
import tempfile
import uuid
from flask import Flask, request, jsonify, send_from_directory, Response
from werkzeug.http import dump_options_header
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# Custom .env loader
def load_dotenv():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

# Load env variables initially
load_dotenv()

app = Flask(__name__, static_folder=STATIC_DIR)

# spotipy caches its API token in ./.cache by default, which fails on hosts with a
# read-only filesystem (Vercel). Point it at the scratch dir so it stays writable.
def get_cache_handler():
    cache_path = os.path.join(tempfile.gettempdir(), 'meloflow_spotipy.cache')
    return spotipy.cache_handler.CacheFileHandler(cache_path)

# yt-dlp needs somewhere to write intermediates before they are streamed back.
# A per-request dir keeps concurrent requests from colliding and is always wiped.
def make_work_dir():
    return tempfile.mkdtemp(prefix='meloflow_')

# Stream the finished MP3 and delete the work dir once the body is done.
# This is hand-rolled rather than send_file() because send_file sets
# direct_passthrough, and Werkzeug then hands the raw file object to the WSGI
# server without wrapping it in a ClosingIterator - so call_on_close callbacks
# never run and the file is orphaned. Yielding chunks lets the generator's
# finally block do the cleanup when the server closes the iterator. Leaving
# Content-Length off also keeps this a chunked response rather than a buffered
# one, which is what some serverless hosts need to stream large payloads.
def stream_mp3(mp3_filepath, download_name, work_dir):
    def generate():
        try:
            with open(mp3_filepath, 'rb') as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    headers = {
        'Content-Disposition': dump_options_header('attachment', {'filename': download_name}),
        'Cache-Control': 'no-store'
    }
    return Response(generate(), mimetype='audio/mp3', headers=headers)

def get_spotify_client():
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    if not client_id or not client_secret:
        return None
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
            cache_handler=get_cache_handler()
        )
        return spotipy.Spotify(client_credentials_manager=auth_manager)
    except Exception:
        return None

# Serve HTML frontend
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

# Serve static files (CSS, JS, assets)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)

# Get current configuration status
@app.route('/api/status', methods=['GET'])
def get_status():
    # Reload dotenv to capture any manual edits to .env file in non-prod
    load_dotenv()
    sp = get_spotify_client()
    is_prod = os.environ.get('PRODUCTION', 'false').lower() == 'true'
    return jsonify({
        'spotify_connected': sp is not None,
        'client_id_configured': bool(os.environ.get('SPOTIPY_CLIENT_ID')),
        'client_secret_configured': bool(os.environ.get('SPOTIPY_CLIENT_SECRET')),
        'settings_locked': is_prod
    })

# Save credentials and reload client
@app.route('/api/settings', methods=['POST'])
def save_settings():
    is_prod = os.environ.get('PRODUCTION', 'false').lower() == 'true'
    if is_prod:
        return jsonify({'error': 'Spotify API settings are locked on public hosted instances.'}), 403

    data = request.get_json() or {}
    client_id = data.get('client_id', '').strip()
    client_secret = data.get('client_secret', '').strip()
    
    if not client_id or not client_secret:
        return jsonify({'error': 'Both Spotify Client ID and Client Secret are required.'}), 400
        
    try:
        # Save to .env
        with open('.env', 'w') as f:
            f.write(f"SPOTIPY_CLIENT_ID={client_id}\n")
            f.write(f"SPOTIPY_CLIENT_SECRET={client_secret}\n")
            
        # Update environment variables in memory
        os.environ['SPOTIPY_CLIENT_ID'] = client_id
        os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
        
        # Test credentials
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
            cache_handler=get_cache_handler()
        )
        sp = spotipy.Spotify(client_credentials_manager=auth_manager)
        # Perform a tiny query to verify
        sp.search(q='test', limit=1)
        
        return jsonify({
            'success': True,
            'message': 'Spotify credentials saved and validated successfully!'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to validate credentials: {str(e)}'}), 400

# Direct Downloader Endpoint
@app.route('/api/download/direct', methods=['POST'])
def download_direct():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
    
    unique_id = str(uuid.uuid4())
    work_dir = make_work_dir()
    output_stem = os.path.join(work_dir, f"direct_{unique_id}")
    mp3_filepath = f"{output_stem}.mp3"
    
    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_stem}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        **(({'cookiefile': cookies_path}) if os.path.exists(cookies_path) else {})
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and extract info
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'downloaded_song')
            
        # Clean title for safe filename
        clean_title = "".join([c if c.isalnum() or c in " .-_()" else "_" for c in title])
        
        if not os.path.exists(mp3_filepath):
            shutil.rmtree(work_dir, ignore_errors=True)
            return jsonify({'error': 'Failed to generate MP3 file.'}), 500

        return stream_mp3(mp3_filepath, f"{clean_title}.mp3", work_dir)
            
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

# Spotify Downloader Endpoint
@app.route('/api/download/spotify', methods=['POST'])
def download_spotify():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'Spotify URL is required.'}), 400
        
    load_dotenv()
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Spotify API credentials are not configured or invalid.'}), 400
        
    unique_id = str(uuid.uuid4())
    work_dir = make_work_dir()
    output_stem = os.path.join(work_dir, f"spotify_{unique_id}")
    mp3_filepath = f"{output_stem}.mp3"
    
    try:
        # Fetch metadata
        track_info = sp.track(url)
        song_name = track_info['name']
        artist_name = track_info['artists'][0]['name']
        
        search_query = f"ytsearch1:{artist_name} {song_name} audio"
        
        cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{output_stem}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            **(({'cookiefile': cookies_path}) if os.path.exists(cookies_path) else {})
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        clean_filename = f"{artist_name} - {song_name}.mp3"
        clean_filename = "".join([c if c.isalnum() or c in " .-_()" else "_" for c in clean_filename])
        
        if not os.path.exists(mp3_filepath):
            shutil.rmtree(work_dir, ignore_errors=True)
            return jsonify({'error': 'Failed to generate MP3 file.'}), 500

        return stream_mp3(mp3_filepath, clean_filename, work_dir)
            
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        return jsonify({'error': f'Spotify track extraction failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Dev server only. Container/prod runs go through gunicorn (see Dockerfile).
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('PRODUCTION', 'false').lower() != 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
