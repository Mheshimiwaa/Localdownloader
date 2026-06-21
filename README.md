# 🎵 MeloFlow — Premium Audio Downloader Web Application

MeloFlow is a high-fidelity, responsive single-page web application built with a Flask API backend and a custom modern glassmorphic HTML/JS/CSS frontend. It replaces the basic Streamlit interface with a premium, sleek dark-themed dashboard.

## ✨ Features

- **Direct Media Downloader**: Paste YouTube, SoundCloud, or direct video/audio URLs to extract and download high-quality MP3 streams.
- **Spotify Track Extractor**: Paste Spotify song links. MeloFlow fetches metadata automatically via the Spotify Web API, performs a matching audio search, compiles the stream, and serves the MP3.
- **Sleek Settings Panel**: Integrated credentials setup to save and test Spotify API credentials directly from the UI into your local configuration.
- **Modern Glassmorphic Design**: Curated color palette (Spotify Green gradients, deep space purples, neon cyans) utilizing Google Fonts, smooth backdrop filters, breathing hover animations, and an interactive pure-CSS pulsing sound wave compilation progress bar.
- **Clipboard Integration**: Seamless "Paste" buttons that automatically pull URLs from the system clipboard to the search fields with one click.
- **Streamlined Downloader**: Direct download triggers that start downloading file streams automatically without redirects or page reloads.

## 📁 Project Structure

```text
SPOTIFY/
├── server.py              # Flask API Web Server & Downloader engine
├── app.py                 # (Legacy) Streamlit python script
├── .env                   # Configuration file (stores Spotify Client keys)
├── venv/                  # Python virtual environment directory
├── static/                # Frontend web application static files
│   ├── index.html         # Main dashboard layout & semantic tags
│   ├── css/
│   │   └── styles.css     # Glassmorphic UI stylesheet & animations
│   └── js/
│       └── app.js         # Client-side API fetch, clipboard, & download hooks
└── README.md              # Project documentation
```

## 🚀 Running the Web App

1. Make sure you are in the project folder:
   ```bash
   cd ~/Desktop/SPOTIFY
   ```

2. Run the Flask backend server:
   ```bash
   ./venv/bin/python server.py
   ```

3. Open your browser and navigate to:
   ```text
   http://localhost:5000
   ```

## 🟢 Spotify API Configuration

To resolve Spotify links, you need Spotify API keys:
1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and log in.
2. Click **Create app**, fill in the basic details (Redirect URI can be `http://localhost:5000`), and save.
3. Obtain your **Client ID** and **Client Secret**.
4. In MeloFlow, click the **Gear Icon** in the top right, enter your credentials, and click **Save & Validate Keys**. MeloFlow will verify them and establish the connection.
