FROM python:3.11-slim

# Install system dependencies (ffmpeg is required by yt-dlp to extract MP3 audio)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy dependency definitions and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py .
COPY static/ static/
COPY cookies.txt .

# Environment defaults
ENV PORT=5000
ENV PRODUCTION=true

# Expose port
EXPOSE 5000

# Start server using gunicorn with support for dynamic host port variables.
# --timeout 0 lifts gunicorn's 30s default, which a download+transcode blows
# through, and gthread keeps concurrent requests from blocking each other.
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} --timeout 0 --worker-class gthread --threads 4 server:app"]
