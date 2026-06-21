import os
import io
import uuid
import glob
from flask import Flask, request, jsonify, send_file, send_from_directory
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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

app = Flask(__name__, static_folder='static')

def get_spotify_client():
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    if not client_id or not client_secret:
        return None
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        return spotipy.Spotify(client_credentials_manager=auth_manager)
    except Exception:
        return None

# Serve HTML frontend
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Serve static files (CSS, JS, assets)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

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
            client_secret=client_secret
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
    output_filename = f"direct_{unique_id}"
    mp3_filepath = f"{output_filename}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and extract info
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'downloaded_song')
            
        # Clean title for safe filename
        clean_title = "".join([c if c.isalnum() or c in " .-_()" else "_" for c in title])
        
        if os.path.exists(mp3_filepath):
            with open(mp3_filepath, 'rb') as f:
                file_data = io.BytesIO(f.read())
            os.remove(mp3_filepath)
            
            return send_file(
                file_data,
                mimetype='audio/mp3',
                as_attachment=True,
                download_name=f"{clean_title}.mp3"
            )
        else:
            return jsonify({'error': 'Failed to generate MP3 file.'}), 500
            
    except Exception as e:
        # Cleanup
        if os.path.exists(mp3_filepath):
            os.remove(mp3_filepath)
        for temp_file in glob.glob(f"{output_filename}.*"):
            try:
                os.remove(temp_file)
            except Exception:
                pass
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
    output_filename = f"spotify_{unique_id}"
    mp3_filepath = f"{output_filename}.mp3"
    
    try:
        # Fetch metadata
        track_info = sp.track(url)
        song_name = track_info['name']
        artist_name = track_info['artists'][0]['name']
        
        search_query = f"ytsearch1:{artist_name} {song_name} audio"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{output_filename}.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        clean_filename = f"{artist_name} - {song_name}.mp3"
        clean_filename = "".join([c if c.isalnum() or c in " .-_()" else "_" for c in clean_filename])
        
        if os.path.exists(mp3_filepath):
            with open(mp3_filepath, 'rb') as f:
                file_data = io.BytesIO(f.read())
            os.remove(mp3_filepath)
            
            return send_file(
                file_data,
                mimetype='audio/mp3',
                as_attachment=True,
                download_name=clean_filename
            )
        else:
            return jsonify({'error': 'Failed to generate MP3 file.'}), 500
            
    except Exception as e:
        # Cleanup
        if os.path.exists(mp3_filepath):
            os.remove(mp3_filepath)
        for temp_file in glob.glob(f"{output_filename}.*"):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        return jsonify({'error': f'Spotify track extraction failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Streamlit runs on 8501, let's run Flask on 5000 (default)
    app.run(host='0.0.0.0', port=5000, debug=True)
