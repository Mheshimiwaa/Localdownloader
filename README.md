# 🎵 MeloFlow — Premium Audio Downloader Web Application

MeloFlow is a responsive single-page web application with a Flask API backend and a
glassmorphic HTML/JS/CSS frontend. Paste a link, get an MP3.

## ✨ Features

- **Direct Media Downloader**: Paste YouTube, SoundCloud, or direct audio/video URLs to extract and download MP3 audio.
- **Spotify Track Extractor**: Paste a Spotify link. MeloFlow reads the metadata via the Spotify Web API, finds a matching audio stream, and serves the MP3.
- **Sleek Settings Panel**: Save and validate Spotify API credentials from the UI.
- **Modern Glassmorphic Design**: Spotify-green/deep-purple palette, backdrop filters, and a pure-CSS pulsing progress bar.
- **Clipboard Integration**: One-click paste buttons.

## 📁 Project Structure

```text
Localdownloader/
├── server.py              # Flask API server & downloader engine
├── app.py                 # (Legacy) Streamlit script, unused
├── Dockerfile             # Container image for local use / other hosts
├── Dockerfile.vercel      # Same image, auto-detected by Vercel
├── .dockerignore
├── requirements.txt
├── static/                # Frontend
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
└── README.md
```

## 🚀 Running Locally

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python server.py
```

Then open <http://localhost:5000>. `ffmpeg` must be on your `PATH` for MP3
extraction to work (`brew install ffmpeg` / `apt install ffmpeg`).

### Docker

```bash
docker build -t meloflow .
docker run -p 5000:5000 meloflow
```

## 🟢 Spotify API Configuration

1. Create an app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Grab the **Client ID** and **Client Secret**.
3. In MeloFlow, click the gear icon, paste them, and hit **Save & Validate Keys**.

On hosted deployments `PRODUCTION=true` locks this panel — set the credentials as
environment variables instead:

```bash
docker run -e PRODUCTION=true -e SPOTIPY_CLIENT_ID=... -e SPOTIPY_CLIENT_SECRET=... -p 5000:5000 meloflow
```

## ▲ Deploying to Vercel

Vercel builds `Dockerfile.vercel` and runs it as a container function, which is what
you want here because yt-dlp needs an `ffmpeg` binary that Vercel's native runtimes
don't provide.

1. Push the repo to GitHub.
2. At [vercel.com/new](https://vercel.com/new), import **Mheshimiwaa/Localdownloader**.
3. Accept the detected framework preset. Vercel finds `Dockerfile.vercel` at the
   repo root and handles the rest — no build command or output directory needed.
4. Add `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` under **Settings → Environment Variables**.
5. Deploy. Every push to the default branch redeploys.

To keep it private, enable **Settings → Deployment Protection → Vercel Authentication**.
Only accounts you invite can reach it, and it's included on the Hobby plan.

Test the same build locally first with `vercel dev` (needs Docker running).

## ⚠️ Known Limitations

**YouTube blocks datacenter IPs.** yt-dlp resolves YouTube metadata fine from a
server, but the media CDN returns `403 Forbidden` for requests from cloud IPs. A
Vercel deployment will hit this, as will most hosts. Direct audio/video URLs
(SoundCloud, direct MP3s, etc.) are unaffected. Self-hosting from a home
connection works. Working around the YouTube side needs PO-token support
(`bgutil-ytdlp-pot-provider`), which is a moving target.

**Response size.** MP3s are streamed in chunks so no buffering limit applies, but
on serverless hosts the scratch filesystem is capped at 500 MB. Downloads are
cleaned up as soon as the client disconnects.
