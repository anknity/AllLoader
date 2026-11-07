"""
ViralScope AI — Universal Media Downloader Service

Supports: YouTube, Instagram, Pinterest, TikTok, Twitter/X, Facebook,
          TeraBox, Reddit, Vimeo, Dailymotion, SoundCloud, Twitch,
          Bilibili, Likee, Snapchat, LinkedIn, Tumblr & 1000+ more.

Features:
- Multi-platform URL detection & branded metadata
- Multi-image post & gallery extraction (Pinterest carousel, Twitter multi-photo, etc.)
- Native TeraBox metadata & share-link extraction
- MP4 video download up to 4K (2160p) with FFmpeg muxing
- 320kbps MP3 / WAV lossless audio extraction
- Full-resolution uncompressed image download
- Unicode & Hindi (Devanagari) title sanitization
- Platform-specific player client routing for YouTube
"""

import io
import json
import logging
import os
import re
import subprocess
import tempfile
from typing import Optional
from urllib.parse import urlparse

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

# ── Platform Detection ────────────────────────────────────────

PLATFORM_PATTERNS: list[tuple[str, str, str, list[str]]] = [
    # (id, display_name, color_hex, domain_substrings)
    ("youtube",     "YouTube",      "#FF0000", ["youtube.com", "youtu.be", "youtube-nocookie.com", "music.youtube.com"]),
    ("instagram",   "Instagram",    "#E1306C", ["instagram.com", "instagr.am"]),
    ("tiktok",      "TikTok",       "#000000", ["tiktok.com", "vm.tiktok.com"]),
    ("twitter",     "Twitter / X",  "#1DA1F2", ["twitter.com", "x.com", "t.co"]),
    ("facebook",    "Facebook",     "#1877F2", ["facebook.com", "fb.watch", "fb.com"]),
    ("pinterest",   "Pinterest",    "#E60023", ["pinterest.com", "pin.it"]),
    ("terabox",     "TeraBox",      "#2B7DE9", [
        "terabox.com", "teraboxapp.com", "1024tera.com", "1024terabox.com",
        "terabox.app", "terasharelink.com", "teraboxlink.com", "freeterabox.com", "tibibox.com"
    ]),
    ("diskwala",    "DiskWala",     "#2563EB", ["diskwala.com", "www.diskwala.com"]),
    ("mdisk",       "MDisk",        "#10B981", ["mdisk.me", "mdiskshortner.link", "mdisk.pro"]),
    ("reddit",      "Reddit",       "#FF4500", ["reddit.com", "redd.it", "v.redd.it"]),
    ("vimeo",       "Vimeo",        "#1AB7EA", ["vimeo.com"]),
    ("dailymotion", "Dailymotion",  "#0066DC", ["dailymotion.com", "dai.ly"]),
    ("soundcloud",  "SoundCloud",   "#FF5500", ["soundcloud.com"]),
    ("twitch",      "Twitch",       "#9146FF", ["twitch.tv", "clips.twitch.tv"]),
    ("bilibili",    "Bilibili",     "#00A1D6", ["bilibili.com", "b23.tv"]),
    ("likee",       "Likee",        "#00E676", ["likee.video", "like.video", "l.likee.video"]),
    ("snapchat",    "Snapchat",     "#FFFC00", ["snapchat.com", "story.snapchat.com"]),
    ("linkedin",    "LinkedIn",     "#0A66C2", ["linkedin.com"]),
    ("tumblr",      "Tumblr",       "#35465C", ["tumblr.com"]),
    ("ok",          "OK.ru",        "#EE8208", ["ok.ru"]),
    ("rutube",      "Rutube",       "#1B1B1B", ["rutube.ru"]),
    ("threads",     "Threads",      "#000000", ["threads.net"]),
    ("loom",        "Loom",         "#625DF5", ["loom.com"]),
]


def detect_platform(url: str) -> dict:
    """Detect the platform from a URL and return metadata using strict domain matching."""
    url_lower = url.lower().strip()

    try:
        parsed = urlparse(url_lower if "://" in url_lower else f"https://{url_lower}")
        host = (parsed.hostname or "").lower()
    except Exception:
        host = ""

    for pid, name, color, domains in PLATFORM_PATTERNS:
        for domain in domains:
            if host == domain or host.endswith("." + domain):
                return {"id": pid, "name": name, "color": color}

    return {"id": "other", "name": "Web Media", "color": "#6B7280"}


# ── TeraBox Dedicated Extractor ───────────────────────────────

def extract_terabox_info(url: str) -> dict:
    """
    Extract file metadata, thumbnails, duration, resolution, and format info
    directly from TeraBox / 1024TeraBox share links without yt-dlp.
    """
    cookie = os.getenv("TERABOX_COOKIE", "")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    if cookie:
        headers["Cookie"] = cookie

    try:
        with httpx.Client(follow_redirects=True, timeout=20.0) as client:
            res = client.get(url, headers=headers)
            html = res.text
            final_url = str(res.url)

            title = "TeraBox Shared File"
            size = 0
            duration = 0
            width = 0
            height = 0
            thumbnail = ""
            fs_id = ""
            uploader = "TeraBox User"

            match = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});", html)
            if match:
                try:
                    state = json.loads(match.group(1))
                    share = state.get("pinia", {}).get("share", {})
                    share_info = share.get("shareInfo", {})
                    uploader = (
                        share_info.get("username")
                        or share_info.get("share_username")
                        or uploader
                    )

                    current_file = (
                        share.get("currentFile")
                        or (share.get("initialFiles", [{}])[0])
                        or (share.get("shareFiles", [{}])[0])
                        or {}
                    )
                    if current_file:
                        title = current_file.get("server_filename") or title
                        size = int(current_file.get("size") or 0)
                        duration = int(current_file.get("duration") or 0)
                        width = int(current_file.get("width") or 0)
                        height = int(current_file.get("height") or 0)
                        fs_id = str(current_file.get("fs_id") or "")
                        thumbs = current_file.get("thumbs", {})
                        thumbnail = (
                            thumbs.get("url3")
                            or thumbs.get("url2")
                            or thumbs.get("url1")
                            or thumbs.get("icon")
                            or ""
                        )
                except Exception as e:
                    logger.warning(f"Error parsing TeraBox INITIAL_STATE: {e}")

            if not fs_id or title == "TeraBox Shared File":
                surl = ""
                if "surl=" in final_url:
                    surl = final_url.split("surl=")[-1].split("&")[0]
                elif "/s/" in final_url:
                    surl = final_url.split("/s/")[-1].split("?")[0].strip("/")

                if surl:
                    api_url = f"https://www.terabox.app/share/list?app_id=250528&shorturl={surl}&root=1"
                    try:
                        resp = client.get(api_url, headers={"Referer": final_url, "User-Agent": headers["User-Agent"]})
                        if resp.status_code == 200:
                            api_data = resp.json()
                            files = api_data.get("list", [])
                            if files:
                                f = files[0]
                                title = f.get("server_filename") or title
                                size = int(f.get("size") or size)
                                duration = int(f.get("duration") or duration)
                                width = int(f.get("width") or width)
                                height = int(f.get("height") or height)
                                fs_id = str(f.get("fs_id") or fs_id)
                                thumbs = f.get("thumbs", {})
                                thumbnail = (
                                    thumbnail
                                    or thumbs.get("url3")
                                    or thumbs.get("url2")
                                    or thumbs.get("url1")
                                    or ""
                                )
                    except Exception as e:
                        logger.warning(f"Error querying TeraBox share/list: {e}")

    except Exception as e:
        logger.error(f"TeraBox metadata extraction failed: {e}")
        raise ValueError(f"Could not connect to TeraBox server: {str(e)}")

    h = height or 720
    size_mb = round(size / (1024 * 1024), 1) if size else 0

    image_qualities = []
    gallery_images = []
    if thumbnail:
        image_qualities.append({
            "format_id": "image-orig",
            "resolution": "Original Poster" + (f" ({width}x{height})" if width and height else ""),
            "width": width,
            "height": height,
            "ext": "jpg",
            "filesize_mb": 0,
            "url": thumbnail,
            "quality_label": "High-Definition Cover Art & Poster",
        })
        gallery_images.append({
            "id": "img_0",
            "index": 1,
            "url": thumbnail,
            "preview_url": thumbnail,
            "resolution": "Original Poster",
            "ext": "jpg",
            "title": title,
        })

    return {
        "id": fs_id or "terabox_media",
        "title": title,
        "channel": uploader,
        "duration_seconds": duration,
        "duration_formatted": format_seconds(duration),
        "view_count": 0,
        "like_count": 0,
        "thumbnail": thumbnail,
        "platform": {"id": "terabox", "name": "TeraBox", "color": "#2B7DE9"},
        "webpage_url": final_url,
        "description": f"TeraBox Cloud File • Size: {size_mb} MB" + (f" • {width}x{height}" if width and height else ""),
        "is_image_only": False,
        "is_multi_image": False,
        "gallery_images": gallery_images,
        "video_qualities": [
            {
                "format_id": "best",
                "resolution": f"{h}p" if h else "Best",
                "height": h,
                "ext": "mp4",
                "filesize_mb": size_mb,
            }
        ],
        "audio_qualities": [
            {"format": "mp3", "bitrate": "320kbps", "quality_label": "320 kbps (High Quality MP3)"},
        ],
        "image_qualities": image_qualities,
    }


def download_terabox_file(
    url: str,
    media_type: str = "video",
    quality: str = "720",
    image_url: Optional[str] = None,
) -> tuple[str, str, str]:
    """
    Download a TeraBox file using configured session credentials or throw clear instructions.
    """
    if media_type == "image":
        return download_image_file(url, quality, platform_id="terabox", image_url=image_url)

    cookie = os.getenv("TERABOX_COOKIE", "").strip() or os.getenv("COOKIE_JSON", "").strip()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    if cookie:
        if not cookie.startswith("ndus=") and "=" not in cookie:
            cookie = f"ndus={cookie}"
        headers["Cookie"] = cookie

    try:
        with httpx.Client(follow_redirects=True, timeout=25.0) as client:
            res = client.get(url, headers=headers)
            html = res.text
            final_url = str(res.url)
            headers["Referer"] = final_url

            surl = ""
            if "surl=" in final_url:
                surl = final_url.split("surl=")[-1].split("&")[0]
            elif "/s/" in final_url:
                surl = final_url.split("/s/")[-1].split("?")[0].strip("/")

            match = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});", html)
            if not match:
                raise ValueError("Could not parse TeraBox webpage state.")

            state = json.loads(match.group(1))
            share_info = state.get("pinia", {}).get("share", {}).get("shareInfo", {})
            shareid = share_info.get("shareid")
            uk = share_info.get("uk")
            sign = share_info.get("sign")
            timestamp = share_info.get("timestamp")

            api_url = f"https://www.terabox.app/share/list?app_id=250528&shorturl={surl}&root=1"
            list_resp = client.get(api_url, headers=headers)
            list_data = list_resp.json()
            files = list_data.get("list", [])
            if not files:
                raise ValueError("No files found in this TeraBox share link.")

            file_item = files[0]
            fs_id = file_item.get("fs_id")
            video_title = file_item.get("server_filename") or "terabox_download"
            dlink = file_item.get("dlink")

            temp_dir = tempfile.mkdtemp(prefix="viralscope_tb_")
            ext = os.path.splitext(video_title)[1].lstrip(".") or ("mp4" if media_type == "video" else "mp3")
            out_file = os.path.join(temp_dir, f"terabox_media.{ext}")

            # ── 1. High-Speed Direct Stream Extraction via FFmpeg ──────
            # This completely bypasses the 'need verify_v2' captcha wall
            if fs_id and shareid and media_type in ("video", "audio"):
                res_types = ["M3U8_AUTO_1080", "M3U8_AUTO_720", "M3U8_AUTO_480", "M3U8_AUTO_360"]
                if quality in ("1080", "1080p"):
                    res_types = ["M3U8_AUTO_1080", "M3U8_AUTO_720", "M3U8_AUTO_480"]
                elif quality in ("720", "720p"):
                    res_types = ["M3U8_AUTO_720", "M3U8_AUTO_480", "M3U8_AUTO_1080"]
                elif quality in ("480", "480p"):
                    res_types = ["M3U8_AUTO_480", "M3U8_AUTO_720", "M3U8_AUTO_360"]

                cookie_str = headers.get("Cookie", "")
                ffmpeg_headers = f"User-Agent: {headers['User-Agent']}\r\n"
                if cookie_str:
                    ffmpeg_headers += f"Cookie: {cookie_str}\r\n"
                ffmpeg_headers += f"Referer: https://www.terabox.com/\r\n"

                for rtype in res_types:
                    stream_url = (
                        f"https://www.terabox.app/share/streaming"
                        f"?app_id=250528&web=1&channel=dubox&clienttype=0"
                        f"&shorturl={surl}&shareid={shareid}&uk={uk}&sign={sign}&timestamp={timestamp}"
                        f"&fid={fs_id}&type={rtype}"
                    )
                    
                    try:
                        # Quick check if playlist is valid
                        chk = client.get(stream_url, headers=headers, timeout=10.0)
                        if chk.status_code == 200 and "#EXTM3U" in chk.text:
                            logger.info(f"🚀 Direct TeraBox stream playlist acquired ({rtype}). Downloading via FFmpeg...")
                            
                            ffmpeg_cmd = [
                                "ffmpeg", "-y",
                                "-headers", ffmpeg_headers,
                                "-extension_picky", "0",
                                "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
                                "-i", stream_url,
                            ]

                            if media_type == "audio":
                                out_file = os.path.join(temp_dir, f"terabox_audio.mp3")
                                ffmpeg_cmd.extend(["-vn", "-acodec", "libmp3lame", "-b:a", "320k", out_file])
                                ext = "mp3"
                            else:
                                ffmpeg_cmd.extend(["-c", "copy", "-bsf:a", "aac_adtstoasc", out_file])

                            p = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                            if p.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 1024:
                                logger.info(f"✅ TeraBox download complete: {out_file} ({os.path.getsize(out_file)} bytes)")
                                safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_title).strip()[:50] or "terabox_file"
                                final_filename = f"{safe_title}.{ext}"
                                content_type = "video/mp4" if ext == "mp4" else "audio/mpeg" if ext == "mp3" else "application/octet-stream"
                                return out_file, final_filename, content_type
                            else:
                                logger.warning(f"FFmpeg stream download attempt failed for {rtype}: {p.stderr[:300]}")
                    except Exception as stream_err:
                        logger.warning(f"Error checking TeraBox stream {rtype}: {stream_err}")

            # ── 2. Fallback to Direct dlink if available ────────────────
            if not dlink and fs_id and shareid:
                dl_url = f"https://www.terabox.app/share/download?app_id=250528&shorturl={surl}&sign={sign}&timestamp={timestamp}&shareid={shareid}&uk={uk}&primaryid={shareid}&fid_list=%5B{fs_id}%5D"
                dl_res = client.get(dl_url, headers=headers)
                dl_json = dl_res.json()
                dlink = dl_json.get("dlink")

            if dlink:
                with client.stream("GET", dlink, headers={"User-Agent": headers["User-Agent"], "Referer": final_url}) as r:
                    r.raise_for_status()
                    with open(out_file, "wb") as f:
                        for chunk in r.iter_bytes(chunk_size=65536):
                            f.write(chunk)

                safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_title).strip()[:50] or "terabox_file"
                final_filename = f"{safe_title}.{ext}"
                content_type = "video/mp4" if ext == "mp4" else "application/octet-stream"
                return out_file, final_filename, content_type

            raise ValueError(
                "Unable to generate stream or download handle for this TeraBox file. "
                "Please ensure the file is public and accessible."
            )

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"TeraBox download error: {e}", exc_info=True)
        raise ValueError(f"TeraBox download failed: {str(e)}")


# ── Image Detection & Extraction ──────────────────────────────

def is_likely_image_url(url: str, platform_id: str = "other") -> bool:
    """
    Check if a URL specifically targets an image/photo post rather than a video.
    Strictly prevents video URLs from being falsely presented as image downloads.
    """
    clean_url = url.split("?")[0].lower().strip()

    # 1. Direct image extensions
    if clean_url.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp", ".svg", ".tiff")):
        return True

    # 2. Pinterest is primarily an image/pin gallery platform
    if platform_id == "pinterest" or "pin.it" in clean_url or "pinterest." in clean_url:
        return True

    # 3. Twitter photo links
    if platform_id == "twitter" and ("/photo/" in clean_url or "pbs.twimg.com" in clean_url):
        return True

    # 4. Known dedicated image hosts
    image_hosts = (
        "imgur.com", "i.redd.it", "flickr.com", "unsplash.com",
        "pexels.com", "ibb.co", "postimg.cc", "prnt.sc"
    )
    if any(h in clean_url for h in image_hosts):
        return True

    return False


def extract_image_post_info(url: str, platform_id: str = "other") -> dict:
    """
    Extract high-resolution image assets for image posts, Pinterest pins,
    multi-image carousel posts, Twitter photos, Instagram posts, or direct image links.
    Guaranteed NOT to falsely convert video or web pages into fake image downloads.
    """
    if not is_likely_image_url(url, platform_id):
        return {
            "title": "",
            "thumbnail": "",
            "image_qualities": [],
            "gallery_images": [],
        }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    image_qualities = []
    gallery_images = []
    title = "High-Resolution Image"
    thumbnail = ""

    # 1. Direct Image URL
    clean_url = url.split("?")[0].lower()
    if clean_url.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp")):
        try:
            with httpx.Client(follow_redirects=True, timeout=15.0) as client:
                r = client.get(url, headers=headers)
                if r.status_code == 200:
                    img = Image.open(io.BytesIO(r.content))
                    w, h = img.size
                    ext = (img.format or "jpg").lower()
                    ext = "jpg" if ext == "jpeg" else ext
                    size_mb = round(len(r.content) / (1024 * 1024), 2)
                    title = os.path.basename(clean_url) or "Direct Image"
                    image_qualities.append({
                        "format_id": "image-orig",
                        "resolution": f"Original ({w}x{h})" if w and h else "Original Ultra HD",
                        "width": w,
                        "height": h,
                        "ext": ext,
                        "filesize_mb": size_mb,
                        "url": url,
                        "quality_label": f"Lossless Original ({ext.upper()})",
                    })
                    gallery_images.append({
                        "id": "img_0",
                        "index": 1,
                        "url": url,
                        "preview_url": url,
                        "resolution": f"{w}x{h}" if w and h else "Original",
                        "ext": ext,
                        "title": title,
                    })
                    thumbnail = url
                    return {
                        "title": title,
                        "thumbnail": thumbnail,
                        "image_qualities": image_qualities,
                        "gallery_images": gallery_images,
                    }
        except Exception:
            pass

    # 2. Pinterest Pins (handles single pins, carousels & multi-image story pins)
    if platform_id == "pinterest" or "pin.it" in url or "pinterest." in url:
        try:
            with httpx.Client(follow_redirects=True, timeout=15.0) as client:
                r = client.get(url, headers=headers)
                html = r.text

                # Clean Title
                title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    title_tag = re.search(r"<title>([^<]+)</title>", html)
                    if title_tag:
                        clean = title_tag.group(1).replace("\n", " ").strip()
                        clean = re.sub(r"\s*\|\s*(Pinterest|Salva).*$", "", clean, flags=re.I).strip()
                        if clean:
                            title = clean

                # Extract all unique pin image hashes from the page
                pattern = r"https://i\.pinimg\.com/(?:originals|\d+x\d*)/([0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{32}\.(?:jpg|jpeg|png|webp))"
                matches = list(dict.fromkeys(re.findall(pattern, html)))

                for i, path in enumerate(matches):
                    orig_url = f"https://i.pinimg.com/originals/{path}"
                    preview_url = f"https://i.pinimg.com/736x/{path}"
                    ext = path.split(".")[-1]

                    gallery_images.append({
                        "id": f"img_{i}",
                        "index": i + 1,
                        "url": orig_url,
                        "preview_url": preview_url,
                        "resolution": "Original Ultra HD",
                        "ext": ext,
                        "title": f"Photo #{i + 1}",
                    })

                if gallery_images:
                    thumbnail = gallery_images[0]["preview_url"]
                    image_qualities.append({
                        "format_id": "image-orig",
                        "resolution": "Original Ultra HD (All)",
                        "width": 2160,
                        "height": 3840,
                        "ext": "jpg",
                        "filesize_mb": 0,
                        "url": gallery_images[0]["url"],
                        "quality_label": f"Album of {len(gallery_images)} Photos (Max Resolution)",
                    })
                else:
                    # Fallback to og:image if no hashes found
                    img_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                    if img_match:
                        base_img = img_match.group(1)
                        orig_img = re.sub(r"/\d+x(\d+)?/", "/originals/", base_img)
                        thumbnail = orig_img
                        image_qualities.append({
                            "format_id": "image-orig",
                            "resolution": "Original Ultra HD",
                            "width": 2160,
                            "height": 3840,
                            "ext": "jpg",
                            "filesize_mb": 0,
                            "url": orig_img,
                            "quality_label": "Original Uncompressed Pin",
                        })
                        gallery_images.append({
                            "id": "img_0",
                            "index": 1,
                            "url": orig_img,
                            "preview_url": base_img,
                            "resolution": "Original Ultra HD",
                            "ext": "jpg",
                            "title": title,
                        })

        except Exception as e:
            logger.warning(f"Pinterest image extraction error: {e}")

    # 3. Twitter / X Image Posts (single or multi-photo)
    elif platform_id == "twitter" or "x.com" in url or "twitter.com" in url:
        try:
            with httpx.Client(follow_redirects=True, timeout=15.0) as client:
                r = client.get(url, headers=headers)
                html = r.text

                # Match all pbs.twimg.com/media image IDs
                tw_matches = list(dict.fromkeys(re.findall(r'pbs\.twimg\.com/media/([a-zA-Z0-9_-]+)', html)))
                for i, img_id in enumerate(tw_matches):
                    orig_url = f"https://pbs.twimg.com/media/{img_id}?format=jpg&name=orig"
                    preview_url = f"https://pbs.twimg.com/media/{img_id}?format=jpg&name=medium"
                    gallery_images.append({
                        "id": f"img_{i}",
                        "index": i + 1,
                        "url": orig_url,
                        "preview_url": preview_url,
                        "resolution": "Original Ultra HD",
                        "ext": "jpg",
                        "title": f"Photo #{i + 1}",
                    })

                if gallery_images:
                    thumbnail = gallery_images[0]["url"]
                    image_qualities.append({
                        "format_id": "image-orig",
                        "resolution": "Original Ultra HD",
                        "width": 2048,
                        "height": 2048,
                        "ext": "jpg",
                        "filesize_mb": 0,
                        "url": gallery_images[0]["url"],
                        "quality_label": "Full Uncompressed Photo (?name=orig)",
                    })
        except Exception as e:
            logger.warning(f"Twitter image extraction error: {e}")

    return {
        "title": title,
        "thumbnail": thumbnail,
        "image_qualities": image_qualities,
        "gallery_images": gallery_images,
    }


def download_image_file(
    url: str,
    quality: str = "orig",
    platform_id: str = "other",
    image_url: Optional[str] = None,
) -> tuple[str, str, str]:
    """
    Download a high-resolution image asset directly or from a gallery item.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }

    target_img_url = url

    # If specific image_url passed from multi-image grid, use it directly
    if image_url and (image_url.startswith("http://") or image_url.startswith("https://")):
        target_img_url = image_url
    elif quality and (quality.startswith("http://") or quality.startswith("https://")):
        target_img_url = quality
    elif not url.split("?")[0].lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")):
        img_info = extract_image_post_info(url, platform_id)
        # Check if quality corresponds to an img_X in gallery_images
        found_in_gallery = False
        if img_info.get("gallery_images"):
            for g in img_info["gallery_images"]:
                if g["id"] == quality:
                    target_img_url = g["url"]
                    found_in_gallery = True
                    break

        if not found_in_gallery and img_info.get("image_qualities"):
            chosen = img_info["image_qualities"][0]
            if quality != "orig":
                for q in img_info["image_qualities"]:
                    if q["format_id"] == quality or quality in q["resolution"].lower():
                        chosen = q
                        break
            target_img_url = chosen.get("url") or target_img_url

    with httpx.Client(follow_redirects=True, timeout=25.0) as client:
        r = client.get(target_img_url, headers=headers)
        r.raise_for_status()
        content = r.content

    temp_dir = tempfile.mkdtemp(prefix="viralscope_img_")

    try:
        pil_img = Image.open(io.BytesIO(content))
        fmt = (pil_img.format or "JPEG").lower()
        w, h = pil_img.size
        ext = "jpg" if fmt in ("jpeg", "jpg") else fmt
    except Exception:
        ext = "jpg"
        w, h = (0, 0)

    out_file = os.path.join(temp_dir, f"media_image.{ext}")
    with open(out_file, "wb") as f:
        f.write(content)

    res_str = f"_{w}x{h}" if w and h else ""
    filename = f"image_download{res_str}.{ext}"
    content_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

    return out_file, filename, content_type


# ── yt-dlp Options Builder ────────────────────────────────────

def _get_base_opts(platform_id: str = "other") -> dict:
    """Build base yt-dlp options. YouTube gets special player_client routing."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 60,
        "retries": 5,
        "fragment_retries": 5,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "noplaylist": True,
    }

    if platform_id == "youtube":
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["web", "android", "ios"],
            }
        }

    if platform_id == "instagram":
        opts["http_headers"]["Referer"] = "https://www.instagram.com/"

    if platform_id == "tiktok":
        opts["http_headers"]["Referer"] = "https://www.tiktok.com/"

    return opts


# ── Video Info Extraction ─────────────────────────────────────

def extract_video_info(url: str) -> dict:
    """
    Extract video metadata, thumbnails, available video resolutions, audio formats,
    and high-resolution image / multi-image gallery assets.
    Works for YouTube, Instagram, TikTok, Pinterest, Twitter, Facebook, TeraBox, and 1000+ sites.
    """
    platform = detect_platform(url)

    # TeraBox has a dedicated native extractor
    if platform["id"] == "terabox":
        return extract_terabox_info(url)

    # DiskWala cloud file / video detection
    if platform["id"] == "diskwala":
        raise ValueError(
            "DiskWala protects video playback behind their official mobile app (com.diskwalaapp) with AppiCrypt cryptographic signatures. "
            "Direct web streaming is restricted by DiskWala. "
            "Please click 'Open Original Post' or open in the DiskWala app to watch or download."
        )

    # If it is a direct image URL, handle directly
    clean_url = url.split("?")[0].lower()
    if clean_url.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp")):
        img_data = extract_image_post_info(url, platform["id"])
        return {
            "id": "direct_image",
            "title": img_data["title"],
            "channel": "Image Host",
            "duration_seconds": 0,
            "duration_formatted": "0:00",
            "view_count": 0,
            "like_count": 0,
            "thumbnail": img_data["thumbnail"],
            "platform": platform,
            "webpage_url": url,
            "description": "Direct High-Resolution Image",
            "is_image_only": True,
            "is_multi_image": False,
            "gallery_images": img_data.get("gallery_images", []),
            "video_qualities": [],
            "audio_qualities": [],
            "image_qualities": img_data["image_qualities"],
        }

    # For Pinterest, check image extraction first because many pins are multi-image or image-only
    if platform["id"] == "pinterest" or "pin.it" in url or "pinterest." in url:
        img_data = extract_image_post_info(url, platform["id"])
        if img_data.get("gallery_images"):
            return {
                "id": "pinterest_pin",
                "title": img_data["title"],
                "channel": "Pinterest Creator",
                "duration_seconds": 0,
                "duration_formatted": "0:00",
                "view_count": 0,
                "like_count": 0,
                "thumbnail": img_data["thumbnail"],
                "platform": platform,
                "webpage_url": url,
                "description": f"Pinterest Album • {len(img_data['gallery_images'])} High-Resolution Photos",
                "is_image_only": True,
                "is_multi_image": len(img_data["gallery_images"]) > 1,
                "gallery_images": img_data["gallery_images"],
                "video_qualities": [],
                "audio_qualities": [],
                "image_qualities": img_data["image_qualities"],
            }

    import yt_dlp

    ydl_opts = _get_base_opts(platform["id"])
    ydl_opts["skip_download"] = True
    ydl_opts["extract_flat"] = False

    info = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        logger.warning(f"yt-dlp extract failed for {url} [{platform['name']}]: {e}")

    # If yt-dlp failed or returned no media, check if this is an actual image post
    if not info or not info.get("formats"):
        if is_likely_image_url(url, platform["id"]):
            img_data = extract_image_post_info(url, platform["id"])
            if img_data.get("image_qualities"):
                return {
                    "id": "image_post",
                    "title": img_data["title"],
                    "channel": platform["name"],
                    "duration_seconds": 0,
                    "duration_formatted": "0:00",
                    "view_count": 0,
                    "like_count": 0,
                    "thumbnail": img_data["thumbnail"],
                    "platform": platform,
                    "webpage_url": url,
                    "description": f"{platform['name']} High-Resolution Image Post",
                    "is_image_only": True,
                    "is_multi_image": len(img_data.get("gallery_images", [])) > 1,
                    "gallery_images": img_data.get("gallery_images", []),
                    "video_qualities": [],
                    "audio_qualities": [],
                    "image_qualities": img_data["image_qualities"],
                }

        p_name = platform.get("name") or "this site"
        raise ValueError(
            f"Could not extract video stream from {p_name}. "
            f"The video might be private, region-restricted, or requires login or mobile app access."
        )

    # If playlist/collection, take the first entry
    if info.get("_type") == "playlist" and info.get("entries"):
        entries = list(info["entries"])
        if entries:
            first_url = entries[0].get("url") or entries[0].get("webpage_url")
            if first_url:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    try:
                        info = ydl2.extract_info(first_url, download=False)
                    except Exception:
                        info = entries[0]

    formats = info.get("formats", [])

    # Build video quality list
    video_qualities = []
    seen_heights = set()
    standard_heights = {360, 480, 720, 1080, 1440, 2160}

    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec", "none")
        if not height or vcodec in ("none", None) or f.get("fps") is None:
            continue
        if height not in standard_heights or height in seen_heights:
            continue
        seen_heights.add(height)
        filesize = f.get("filesize") or f.get("filesize_approx") or 0
        video_qualities.append({
            "format_id": f.get("format_id"),
            "resolution": f"{height}p",
            "height": height,
            "ext": "mp4",
            "filesize_mb": round(filesize / (1024 * 1024), 1) if filesize else 0,
        })

    # For platforms with a single combined stream (Instagram, TikTok)
    if not video_qualities and formats:
        for f in formats:
            height = f.get("height")
            vcodec = f.get("vcodec", "")
            if height and vcodec and vcodec != "none":
                if height not in seen_heights:
                    seen_heights.add(height)
                    filesize = f.get("filesize") or f.get("filesize_approx") or 0
                    video_qualities.append({
                        "format_id": f.get("format_id"),
                        "resolution": f"{height}p",
                        "height": height,
                        "ext": "mp4",
                        "filesize_mb": round(filesize / (1024 * 1024), 1) if filesize else 0,
                    })

    # YouTube standard qualities
    if platform["id"] == "youtube":
        for h in [2160, 1440, 1080, 720, 480, 360]:
            if h not in seen_heights:
                video_qualities.append({
                    "format_id": f"auto-{h}",
                    "resolution": f"{h}p",
                    "height": h,
                    "ext": "mp4",
                    "filesize_mb": 0,
                })
    elif video_qualities:
        pass
    else:
        h = info.get("height")
        if h:
            video_qualities.append({
                "format_id": "best",
                "resolution": f"{h}p",
                "height": h,
                "ext": "mp4",
                "filesize_mb": 0,
            })

    video_qualities.sort(key=lambda x: x["height"], reverse=True)

    has_audio = any(
        f.get("acodec") and f.get("acodec") != "none"
        for f in formats
    )
    if not has_audio and formats:
        has_audio = True

    thumbnail = (
        info.get("thumbnail")
        or (info.get("thumbnails", [{}])[-1].get("url") if info.get("thumbnails") else None)
        or ""
    )

    # ── High-Resolution Image Qualities ───────────────────────────
    image_qualities = []
    gallery_images = []
    if platform["id"] == "youtube" and info.get("id"):
        yt_id = info["id"]
        image_qualities.append({
            "format_id": "image-maxres",
            "resolution": "1080p Ultra HD (1920x1080)",
            "width": 1920,
            "height": 1080,
            "ext": "jpg",
            "filesize_mb": 0,
            "url": f"https://i.ytimg.com/vi/{yt_id}/maxresdefault.jpg",
            "quality_label": "Official Full HD Master Thumbnail",
        })
        image_qualities.append({
            "format_id": "image-hq",
            "resolution": "High Quality (640x480)",
            "width": 640,
            "height": 480,
            "ext": "jpg",
            "filesize_mb": 0,
            "url": f"https://i.ytimg.com/vi/{yt_id}/hqdefault.jpg",
            "quality_label": "Standard High Quality Preview",
        })
        gallery_images.append({
            "id": "img_0",
            "index": 1,
            "url": f"https://i.ytimg.com/vi/{yt_id}/maxresdefault.jpg",
            "preview_url": f"https://i.ytimg.com/vi/{yt_id}/maxresdefault.jpg",
            "resolution": "1920x1080",
            "ext": "jpg",
            "title": "Master Cover Art",
        })
    elif thumbnail:
        image_qualities.append({
            "format_id": "image-orig",
            "resolution": "Original Ultra HD",
            "width": 1920,
            "height": 1080,
            "ext": "jpg",
            "filesize_mb": 0,
            "url": thumbnail,
            "quality_label": "High-Definition Cover Art / Poster",
        })
        gallery_images.append({
            "id": "img_0",
            "index": 1,
            "url": thumbnail,
            "preview_url": thumbnail,
            "resolution": "Ultra HD",
            "ext": "jpg",
            "title": "Cover Image",
        })

    native_imgs = extract_image_post_info(url, platform["id"])
    if native_imgs.get("gallery_images"):
        for g in native_imgs["gallery_images"]:
            if not any(item["url"] == g["url"] for item in gallery_images):
                gallery_images.append(g)

    is_image_only = len(video_qualities) == 0 and len(gallery_images) > 0

    return {
        "id": info.get("id", ""),
        "title": info.get("title") or info.get("description", "")[:80] or "Untitled Media",
        "channel": (
            info.get("uploader")
            or info.get("channel")
            or info.get("uploader_id")
            or info.get("creator")
            or "Unknown Creator"
        ),
        "duration_seconds": info.get("duration") or 0,
        "duration_formatted": format_seconds(info.get("duration") or 0),
        "view_count": info.get("view_count") or 0,
        "like_count": info.get("like_count") or 0,
        "thumbnail": thumbnail or (gallery_images[0]["preview_url"] if gallery_images else ""),
        "platform": platform,
        "webpage_url": info.get("webpage_url") or url,
        "description": (info.get("description") or "")[:300],
        "is_image_only": is_image_only,
        "is_multi_image": len(gallery_images) > 1,
        "gallery_images": gallery_images,
        "video_qualities": video_qualities,
        "audio_qualities": [
            {"format": "mp3", "bitrate": "320kbps", "quality_label": "320 kbps (High Quality MP3)"},
            {"format": "mp3", "bitrate": "192kbps", "quality_label": "192 kbps (Standard MP3)"},
            {"format": "wav", "bitrate": "lossless", "quality_label": "Lossless WAV (Studio Audio)"},
        ] if has_audio else [],
        "image_qualities": image_qualities or native_imgs.get("image_qualities", []),
    }


# ── Media Download ────────────────────────────────────────────

def download_media_file(
    url: str,
    media_type: str = "video",
    quality: str = "720",
    image_url: Optional[str] = None,
) -> tuple[str, str, str]:
    """
    Download video, audio, or high-resolution image from any supported platform.

    Returns:
        tuple of (file_path, clean_filename, content_type)
    """
    platform = detect_platform(url)

    # Image download handler
    if media_type == "image":
        return download_image_file(url, quality, platform_id=platform["id"], image_url=image_url)

    # TeraBox has a dedicated download route
    if platform["id"] == "terabox":
        return download_terabox_file(url, media_type, quality, image_url=image_url)

    import yt_dlp

    temp_dir = tempfile.mkdtemp(prefix="viralscope_dl_")
    out_template = os.path.join(temp_dir, "output_%(id)s.%(ext)s")

    ydl_opts = _get_base_opts(platform["id"])
    ydl_opts["outtmpl"] = out_template

    if media_type == "audio":
        ext = "wav" if quality == "wav" else "mp3"
        bitrate = "320" if quality == "320" else "192"

        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": ext,
            "preferredquality": bitrate,
        }]
        content_type = f"audio/{ext}"
    else:
        target_height = re.sub(r"\D", "", quality) or "720"

        if platform["id"] == "youtube":
            ydl_opts["format"] = (
                f"bestvideo[height<={target_height}]+bestaudio/"
                f"best[height<={target_height}]/best"
            )
        else:
            ydl_opts["format"] = (
                f"bestvideo[height<={target_height}]+bestaudio/"
                f"best[height<={target_height}]/"
                f"bestvideo+bestaudio/best"
            )

        ydl_opts["merge_output_format"] = "mp4"
        content_type = "video/mp4"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            if info and info.get("_type") == "playlist" and info.get("entries"):
                entries = list(info["entries"])
                if entries:
                    info = entries[0]
            video_title = (info or {}).get("title") or "media"
        except Exception as e:
            logger.error(f"yt-dlp download failed [{platform['name']}]: {e}")
            raise ValueError(f"Download from {platform['name']} failed: {str(e)}")

    files = [f for f in os.listdir(temp_dir) if not f.endswith((".part", ".ytdl"))]
    if not files:
        raise ValueError("Download completed but output file could not be found.")

    actual_file = os.path.join(temp_dir, files[0])
    actual_ext = os.path.splitext(files[0])[1].lstrip(".") or ("mp4" if media_type == "video" else "mp3")

    safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_title).strip()[:50] or "media_download"
    platform_tag = platform["id"]
    final_filename = f"{safe_title}_{platform_tag}_{quality}.{actual_ext}"

    return actual_file, final_filename, content_type


# ── Helpers ───────────────────────────────────────────────────

def format_seconds(seconds: int) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def get_supported_platforms() -> list[dict]:
    """Return list of all supported platforms with metadata for the frontend."""
    return [
        {"id": pid, "name": name, "color": color}
        for pid, name, color, _ in PLATFORM_PATTERNS
    ]
