# ========================================================
# All-in-One Downloader Mini App — Unified Dockerfile
# Fly.io / Container Deployment
# ========================================================

# Stage 1: Build React 19 Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend + Static Host
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies:
# - ffmpeg: Required by yt-dlp for video merging (4K/1080p video + audio) & audio conversion (MP3/WAV)
# - curl & ca-certificates: Required for secure HTTPS extraction & health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./

# Copy compiled frontend SPA from Stage 1 into static mount
COPY --from=frontend-builder /build/dist ./static

# Ensure temp directory exists
RUN mkdir -p /tmp/viralscope_downloads

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

# Launch unified server (Fly.io binds to 0.0.0.0:8080)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

