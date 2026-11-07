"""
All-in-One Media Downloader — Unified Mini App Server

Hosts:
1. FastAPI High-Speed Media Extraction & Download APIs (/api/downloader/...)
2. Telegram Bot Webhook & Mini App Handler (/api/telegram/webhook)
3. Compiled React 19 Frontend SPA (Single Container / Fly.io Ready)
"""

import logging
import os
import re
import urllib.parse
from contextlib import asynccontextmanager
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from downloader_service import (
    download_media_file,
    extract_video_info,
    detect_platform,
    PLATFORM_PATTERNS,
)
from telegram_bot import bot_service, TEMP_SERVED_FILES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MiniDownloader")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Telegram Bot if token provided
    webapp_url = os.getenv("WEBAPP_URL", "")
    if bot_service.is_configured:
        logger.info("Initializing Telegram Bot integration...")
        await bot_service.init_bot(base_url=webapp_url)
    else:
        logger.info("Running without Telegram bot token (TELEGRAM_BOT_TOKEN not set).")
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title="All-in-One Media Downloader Mini App",
    description="Universal Media Downloader & Telegram Mini App",
    version="2.1.0",
    lifespan=lifespan,
)

# Allow CORS for local dev, mobile browsers, and Telegram WebApps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# ── Request Models ─────────────────────────────────────────────
class DownloaderInfoRequest(BaseModel):
    url: str = Field(..., description="Media URL from any supported platform")


class DownloaderDownloadRequest(BaseModel):
    url: str = Field(..., description="Media URL")
    media_type: str = Field("video", description="'video', 'audio', or 'image'")
    quality: str = Field("720", description="Resolution (2160, 1080, 720) or audio (320, wav) or image (orig)")
    image_url: Optional[str] = Field(None, description="Direct URL of a photo from a multi-image album")
    telegram_user_id: Optional[int] = Field(None, description="Telegram User ID to send the file directly into chat")


# ── API Routes ─────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "All-in-One Downloader Mini App",
        "version": "2.1.0",
        "telegram_bot": bot_service.is_configured,
    }


@app.get("/api/downloader/platforms")
async def get_platforms():
    return [
        {"id": pid, "name": name, "color": color, "domains": domains}
        for pid, name, color, domains in PLATFORM_PATTERNS
    ]


@app.get("/api/downloader/direct/{file_token}")
async def serve_direct_file(file_token: str):
    """Direct streaming endpoint for large files that exceed Telegram bot upload limits."""
    item = TEMP_SERVED_FILES.get(file_token)
    if not item or not os.path.exists(item["path"]):
        raise HTTPException(status_code=404, detail="Download file has expired or is not available.")

    file_path = item["path"]
    filename = item["name"]
    encoded_filename = urllib.parse.quote(filename)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}',
        },
    )


@app.post("/api/downloader/info")
async def api_info(request: DownloaderInfoRequest):
    clean_url = request.url.strip()
    if not clean_url:
        raise HTTPException(status_code=400, detail="Please provide a valid media URL.")

    try:
        return extract_video_info(clean_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Downloader info error for {clean_url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process media link: {str(e)}")


@app.post("/api/downloader/download")
async def api_download(request: DownloaderDownloadRequest):
    clean_url = request.url.strip()
    if not clean_url:
        raise HTTPException(status_code=400, detail="Missing URL parameter.")

    try:
        file_path, filename, content_type = download_media_file(
            url=clean_url,
            media_type=request.media_type,
            quality=request.quality,
            image_url=request.image_url,
        )

        # ASCII filename fallback for Content-Disposition header
        ascii_filename = re.sub(r'[^\x00-\x7F]+', '_', filename).strip('_')
        if not ascii_filename:
            ext = "jpg" if request.media_type == "image" else "mp4" if request.media_type == "video" else "mp3"
            ascii_filename = f"media_download_{request.quality}.{ext}"

        encoded_filename = urllib.parse.quote(filename)

        # If user is in Telegram, also dispatch direct send to their chat!
        if request.telegram_user_id and bot_service.is_configured:
            import asyncio
            task = asyncio.create_task(
                bot_service.send_file_to_chat(
                    chat_id=request.telegram_user_id,
                    file_path=file_path,
                    filename=ascii_filename,
                    title=filename,
                    media_type=request.media_type,
                )
            )
            # Log any silent task failures
            task.add_done_callback(
                lambda t: logger.error(f"Chat send task failed: {t.exception()}")
                if t.done() and not t.cancelled() and t.exception() else None
            )

        return FileResponse(
            path=file_path,
            filename=ascii_filename,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Download execution error for {clean_url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# ── Telegram Webhook Handler ───────────────────────────────────
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    if not bot_service.is_configured:
        return JSONResponse({"status": "bot_not_configured"}, status_code=200)

    try:
        update = await request.json()
        await bot_service.handle_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error handling Telegram webhook update: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}


# ── Static Frontend SPA Serving ────────────────────────────────
# Locate the compiled Vite frontend dist
static_dirs = [
    os.path.join(os.path.dirname(__file__), "static"),
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"),
]

dist_path = None
for s_dir in static_dirs:
    if os.path.isdir(s_dir) and os.path.exists(os.path.join(s_dir, "index.html")):
        dist_path = os.path.abspath(s_dir)
        break

if dist_path:
    logger.info(f" Serving compiled Mini App frontend from: {dist_path}")

    # Mount assets and banners
    assets_dir = os.path.join(dist_path, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    banners_dir = os.path.join(dist_path, "banners")
    if os.path.isdir(banners_dir):
        app.mount("/banners", StaticFiles(directory=banners_dir), name="banners")

    # Serve index.html on root and SPA catch-all
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API or Health routes
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not Found")

        target_file = os.path.join(dist_path, full_path)
        if os.path.isfile(target_file):
            return FileResponse(target_file)

        return FileResponse(os.path.join(dist_path, "index.html"))
else:
    logger.warning("⚠️ No frontend 'dist' folder found. Serving API-only mode.")

    @app.get("/")
    async def root_fallback():
        return {
            "service": "All-in-One Downloader API",
            "message": "Frontend build not detected. Build with 'npm run build' inside frontend.",
            "health": "/health",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080 if os.getenv("FLY_APP_NAME") else 8001))
    logger.info(f"🚀 Starting All-in-One Downloader Mini App on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
