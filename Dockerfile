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

# Environment defaults
ENV PORT=5000
ENV PRODUCTION=true

# Expose port
EXPOSE 5000

# Start server using gunicorn with support for dynamic host port variables
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} server:app"]
