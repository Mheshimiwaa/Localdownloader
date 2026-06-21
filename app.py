import streamlit as st
import yt_dlp
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Initialize Spotify client using credentials handled automatically from environment or .env
try:
    auth_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(client_credentials_manager=auth_manager)
except Exception:
    sp = None

# Base configuration for audio extraction
def get_ydl_opts(output_filename="song"):
    return {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_filename}.%(ext)s', 
    }

st.title("🎵 OpenSource Web Downloader")

# Create Two Clean Segments (Tabs)
tab1, tab2 = st.tabs(["🚀 YouTube / Direct Links", "🟢 Spotify Integration"])

# --- SEGMENT 1: DIRECT LINKS ---
with tab1:
    st.subheader("Direct Media Downloader")
    direct_url = st.text_input("Paste YouTube / SoundCloud URL:", key="direct_input")
    
    if st.button("Process Direct Link", key="direct_btn"):
        if direct_url:
            st.write("Downloading audio stream...")
            try:
                with yt_dlp.YoutubeDL(get_ydl_opts("direct_song")) as ydl:
                    ydl.download([direct_url])
                
                if os.path.exists("direct_song.mp3"):
                    with open("direct_song.mp3", "rb") as file:
                        st.download_button(
                            label="💾 Download MP3 to your Device",
                            data=file.read(),
                            file_name="downloaded_song.mp3",
                            mime="audio/mp3"
                        )
                    os.remove("direct_song.mp3")
                    st.success("Extraction complete!")
            except Exception as e:
                st.error(f"Error handling video stream: {e}")

# --- SEGMENT 2: SPOTIFY TRACKS ---
with tab2:
    st.subheader("Spotify Track Extractor")
    if not sp:
        st.warning("Spotify API credentials not detected. Please ensure your .env file contains SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET.")
    else:
        spotify_url = st.text_input("Paste Spotify Song URL:", key="spotify_input")
        
        if st.button("Search & Convert Track", key="spotify_btn"):
            if spotify_url:
                st.write("Extracting track metadata from Spotify...")
                try:
                    # Parse out track information
                    track_info = sp.track(spotify_url)
                    song_name = track_info['name']
                    artist_name = track_info['artists'][0]['name']
                    
                    # Create clean query for YouTube matching
                    search_query = f"ytsearch1:{artist_name} {song_name} audio"
                    st.info(f"Found: **{song_name}** by *{artist_name}*. Matching on audio platforms...")
                    
                    # Download using the search string query instead of the DRM link
                    with yt_dlp.YoutubeDL(get_ydl_opts("spotify_song")) as ydl:
                        ydl.download([search_query])
                        
                    if os.path.exists("spotify_song.mp3"):
                        with open("spotify_song.mp3", "rb") as file:
                            st.download_button(
                                label=f"💾 Download {song_name}.mp3",
                                data=file.read(),
                                file_name=f"{artist_name} - {song_name}.mp3",
                                mime="audio/mp3"
                            )
                        os.remove("spotify_song.mp3")
                        st.success("Track successfully converted!")
                
                except Exception as e:
                    st.error(f"Could not retrieve or match Spotify metadata: {e}")