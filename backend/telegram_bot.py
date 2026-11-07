"""
Telegram Bot Engine for All-in-One Downloader Mini App
Bot: @loadrip_bot

Features:
- Configures bot command shortcuts (/start, /platforms, /download, /help, /about)
- Sets bot profile description & about text on Telegram
- Interactive inline keyboards with shortcuts and categorized platform lists
- Direct link detection: paste any link in chat to get an instant download launcher
- Supports both Webhook (production) and Long-Polling (local testing)
"""

import asyncio
import logging
import os
import re
import time
import uuid
from typing import Any, Optional
import httpx

from downloader_service import detect_platform, PLATFORM_PATTERNS, download_media_file

logger = logging.getLogger("TelegramBot")

TELEGRAM_API_BASE = "https://api.telegram.org"
TEMP_SERVED_FILES: dict[str, dict] = {}


# Comprehensive list of platforms categorized for user introduction
PLATFORM_DIRECTORY = """
🌐 **ALL-IN-ONE DOWNLOADER — SUPPORTED PLATFORMS (1000+)**

🎬 **Video Platforms (Up to 4K / 1080p / 60fps):**
• **YouTube** — Videos, Shorts, Premieres (up to 4K UHD)
• **Instagram** — Reels, Video Posts, Stories
• **TikTok** — Full HD, 100% Watermark-Free
• **Twitter / X** — HD Videos & Animated GIFs
• **Facebook** — Public Videos & Reels
• **Reddit** — Embedded & v.redd.it videos with audio merged
• **Vimeo** — High bitrate 1080p/4K
• **Dailymotion** — HD Web videos
• **Twitch** — Highlight Clips & VODs
• **Bilibili** — HD Video streams
• **Likee, Loom, Snapchat, LinkedIn, Tumblr** & more

🎵 **Music & Audio (320kbps MP3 / WAV Lossless):**
• **SoundCloud** — Tracks, Sets & Playlists
• **YouTube Music** — 320kbps Studio-grade extraction
• **Bandcamp, Mixcloud, Audiomack**

📸 **Photo Albums & Galleries (Full Resolution):**
• **Pinterest** — Pins & Multi-Photo story boards
• **Instagram** — Multi-Image swipe carousels
• **Twitter / X** — Multi-Photo posts in original quality
• **Reddit** — Multi-image gallery posts

☁️ **Cloud Storage Drives:**
• **TeraBox** — High-speed direct link extraction
• **DiskWala & MDisk** — Direct media bypass
"""


class TelegramBotService:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.webapp_url = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
        self.bot_username = "loadrip_bot"
        self.bot_first_name = "AllinOneloader"
        self.required_channel = os.getenv("REQUIRED_CHANNEL", "@toolboxkit").strip()
        self.required_channel_url = os.getenv("REQUIRED_CHANNEL_URL", "https://t.me/toolboxkit").strip()
        self._polling_task: Optional[asyncio.Task] = None
        self._is_polling = False

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    async def _api_call(self, method: str, data: Optional[dict[str, Any]] = None) -> Optional[dict]:
        if not self.token:
            return None
        url = f"{TELEGRAM_API_BASE}/bot{self.token}/{method}"
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, json=data or {})
                res_data = res.json()
                if not res_data.get("ok"):
                    logger.warning(f"Telegram API {method} response: {res_data.get('description')}")
                return res_data
        except asyncio.CancelledError:
            raise
        except BaseException as e:
            logger.error(f"Telegram API request failed ({method}): {e}")
            return None

    def get_webapp_url(self, target_url: str = "") -> str:
        """Returns the WebApp URL or fallback with optional query param."""
        tunnel_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tunnel_url.txt"))
        if os.path.exists(tunnel_file):
            try:
                with open(tunnel_file, "r") as f:
                    t_url = f.read().strip()
                    if t_url.startswith("https://"):
                        self.webapp_url = t_url
            except Exception:
                pass

        base = self.webapp_url or "https://all-in-one-downloader.fly.dev"
        if target_url:
            import urllib.parse
            return f"{base}?url={urllib.parse.quote(target_url)}"
        return base

    async def configure_bot_profile_and_commands(self):
        """Sets bot commands, profile description, and chat menu button."""
        # 1. Register Command Menu Shortcuts
        commands = [
            {"command": "start", "description": "🚀 Launch Downloader Mini App"},
            {"command": "platforms", "description": "🌐 1000+ Supported Platforms List"},
            {"command": "download", "description": "⚡ Quick Link Download"},
            {"command": "help", "description": "📖 How to use & download guide"},
            {"command": "about", "description": "ℹ️ Features, Formats & 4K Quality"},
        ]
        await self._api_call("setMyCommands", {"commands": commands})

        # 2. Set Bot Description (Seen before tapping Start)
        description_text = (
            "⚡ All-in-One Universal Media Downloader\n\n"
            "Download 4K Videos, 320kbps MP3 Audio, and High-Resolution Photo Albums directly inside Telegram!\n\n"
            "Supported Platforms:\n"
            "• YouTube (4K & Shorts)\n"
            "• Instagram (Reels & Carousels)\n"
            "• TikTok (Watermark-free)\n"
            "• Pinterest (Multi-photo boards)\n"
            "• Twitter / X (HD & Photos)\n"
            "• TeraBox & DiskWala\n"
            "• SoundCloud & 1000+ more"
        )
        await self._api_call("setMyDescription", {"description": description_text})

        # 3. Set Short Description (Bio)
        short_desc = "Universal 4K Video, 320kbps MP3 & Photo Downloader for 1000+ platforms."
        await self._api_call("setMyShortDescription", {"short_description": short_desc})

        # 4. Set Chat Menu Button
        if self.webapp_url:
            await self._api_call("setChatMenuButton", {
                "menu_button": {
                    "type": "web_app",
                    "text": "⚡ Downloader",
                    "web_app": {"url": self.get_webapp_url()}
                }
            })

    async def update_bot_avatar(self, image_path: str = ""):
        """Sets or updates the bot's profile avatar on Telegram."""
        if not self.token:
            return
        if not image_path:
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "static", "banners", "video_banner.jpg"),
                os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "banners", "video_banner.jpg"),
            ]
            for p in possible_paths:
                if os.path.isfile(p):
                    image_path = p
                    break
        if not image_path or not os.path.isfile(image_path):
            return

        try:
            import json
            url = f"{TELEGRAM_API_BASE}/bot{self.token}/setMyProfilePhoto"
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(image_path, "rb") as f:
                    files = {"img": ("avatar.jpg", f, "image/jpeg")}
                    data = {"photo": json.dumps({"type": "static", "photo": "attach://img"})}
                    res = await client.post(url, data=data, files=files)
                    if res.status_code == 200 and res.json().get("ok"):
                        logger.info("✅ Bot profile photo updated successfully!")
        except Exception as e:
            logger.warning(f"Could not update bot profile photo: {e}")

    async def is_channel_member(self, user_id: int | str) -> bool:
        """Check if user has joined the required channel (@toolboxkit)."""
        if not self.token or not user_id or not self.required_channel:
            return True
        try:
            url = f"{TELEGRAM_API_BASE}/bot{self.token}/getChatMember"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json={
                    "chat_id": self.required_channel,
                    "user_id": int(user_id)
                })
                res_data = res.json()
                if res_data.get("ok"):
                    status = res_data.get("result", {}).get("status")
                    return status in ("creator", "administrator", "member", "restricted")
                
                desc = res_data.get("description", "")
                if "member list is inaccessible" in desc or "chat not found" in desc:
                    logger.warning(
                        f"⚠️ Cannot check channel member: {desc}. "
                        f"Please ensure @{self.bot_username} is added as an Administrator in {self.required_channel}."
                    )
                    # Don't block users if bot hasn't been granted admin rights yet
                    return True
                return False
        except Exception as e:
            logger.error(f"Error checking channel membership for {user_id}: {e}")
            return True

    async def send_join_channel_prompt(self, chat_id: int | str, user_id: int | str, message_id: Optional[int] = None):
        """Send or edit message with mandatory channel join requirement."""
        text = (
            "🔒 **Channel Membership Required**\n\n"
            "To use **All-in-One Downloader**, you must join our official Telegram channel first:\n\n"
            f"👉 **Channel:** {self.required_channel}\n\n"
            "1️⃣ Tap **'📢 Join Channel'** below.\n"
            "2️⃣ Tap **'✅ I Have Joined'** to verify and unlock the Downloader!"
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": f"📢 Join {self.required_channel}", "url": self.required_channel_url}],
                [{"text": "✅ I Have Joined (Verify)", "callback_data": f"verify_join_{user_id}"}]
            ]
        }
        if message_id:
            await self._api_call("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            })
        else:
            await self._api_call("sendMessage", {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            })

    async def _send_welcome(self, chat_id: int | str, first_name: str, message_id: Optional[int] = None):
        """Send or edit main welcome launcher message."""
        welcome_text = (
            f"👋 **Hey {first_name}! Welcome to All-in-One Downloader**\n\n"
            "The most powerful media downloader on Telegram, designed with the sleek **ViralScope** interface.\n\n"
            "**What you can download:**\n"
            "• 🎬 **Ultra HD Video:** 4K, 1080p, 720p (MP4)\n"
            "• 🎵 **Studio Audio:** 320kbps MP3 & Lossless WAV\n"
            "• 📸 **Photo Albums:** Multi-image Pinterest boards & IG carousels\n"
            "• ⚡ **Watermark-Free:** TikTok & Reels in original quality\n\n"
            "👇 Tap **Open Downloader** below to launch the Mini App:"
        )

        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "🚀 Open Downloader Mini App",
                        "web_app": {"url": self.get_webapp_url()}
                    }
                ],
                [
                    {"text": "🌐 1000+ Platforms", "callback_data": "view_platforms"},
                    {"text": "📖 How to Use", "callback_data": "view_help"}
                ],
                [
                    {"text": "ℹ️ Quality & Formats", "callback_data": "view_about"}
                ]
            ]
        }

        if message_id:
            await self._api_call("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": welcome_text,
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            })
        else:
            await self._api_call("sendMessage", {
                "chat_id": chat_id,
                "text": welcome_text,
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            })

    async def init_bot(self, base_url: str = ""):
        """Initialize bot, verify credentials, configure profile, and choose webhook vs polling."""
        if not self.token:
            return

        if base_url:
            self.webapp_url = base_url.rstrip("/")

        # Verify bot
        me = await self._api_call("getMe")
        if me and me.get("ok"):
            self.bot_username = me["result"].get("username", self.bot_username)
            self.bot_first_name = me["result"].get("first_name", self.bot_first_name)
            logger.info(f"🤖 Connected to Telegram Bot: @{self.bot_username} ({self.bot_first_name})")
        else:
            logger.error("❌ Invalid TELEGRAM_BOT_TOKEN provided.")
            return

        # Setup commands, description, menu button, avatar
        await self.configure_bot_profile_and_commands()
        await self.update_bot_avatar()

        # Decide between Webhook and Long-Polling
        if self.webapp_url.startswith("https://"):
            webhook_url = f"{self.webapp_url}/api/telegram/webhook"
            res = await self._api_call("setWebhook", {
                "url": webhook_url,
                "drop_pending_updates": True,
                "allowed_updates": ["message", "callback_query"]
            })
            if res and res.get("ok"):
                logger.info(f"✅ Telegram Webhook registered: {webhook_url}")
            else:
                logger.warning(f"⚠️ Webhook registration fallback to polling: {res}")
                self.start_polling()
        else:
            logger.info("ℹ️ No public HTTPS WEBAPP_URL set — Starting Telegram Long-Polling for local testing...")
            self.start_polling()

    def start_polling(self):
        """Starts background long-polling task."""
        if self._is_polling:
            return
        self._is_polling = True
        self._polling_task = asyncio.create_task(self._polling_loop())

    async def _polling_loop(self):
        """Long-polling update loop for instant local testing without open ports."""
        # Delete existing webhook so polling works
        await self._api_call("deleteWebhook", {"drop_pending_updates": False})
        logger.info(f"🚀 Telegram Long-Polling active for @{self.bot_username}! You can test in Telegram now.")

        offset = 0
        while self._is_polling:
            try:
                updates_res = await self._api_call("getUpdates", {
                    "offset": offset,
                    "timeout": 20,
                    "allowed_updates": ["message", "callback_query"]
                })
                if updates_res and updates_res.get("ok"):
                    for update in updates_res.get("result", []):
                        offset = update["update_id"] + 1
                        asyncio.create_task(self.handle_update(update))
                else:
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except BaseException as e:
                logger.error(f"Polling loop exception: {e}")
                await asyncio.sleep(3)

    async def handle_update(self, update: dict):
        """Process incoming Telegram messages and callback queries."""
        # Handle Callback Queries (Button clicks)
        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb.get("id")
            cb_data = cb.get("data", "")
            chat_id = cb.get("message", {}).get("chat", {}).get("id")
            message_id = cb.get("message", {}).get("message_id")
            first_name = cb.get("from", {}).get("first_name", "there")
            from_user_id = cb.get("from", {}).get("id")

            if cb_data.startswith("verify_join_"):
                uid = cb_data.replace("verify_join_", "")
                is_mem = await self.is_channel_member(uid)
                if is_mem:
                    await self._api_call("answerCallbackQuery", {
                        "callback_query_id": cb_id,
                        "text": "✅ Membership verified! Welcome.",
                        "show_alert": False
                    })
                    await self._send_welcome(chat_id, first_name, message_id=message_id)
                else:
                    await self._api_call("answerCallbackQuery", {
                        "callback_query_id": cb_id,
                        "text": f"⚠️ You haven't joined {self.required_channel} yet!\n\nPlease tap the Join button first, then tap Verify.",
                        "show_alert": True
                    })
                return

            await self._api_call("answerCallbackQuery", {"callback_query_id": cb_id})

            if cb_data == "view_platforms":
                await self._send_platforms_list(chat_id)
            elif cb_data == "view_help":
                await self._send_help_guide(chat_id)
            elif cb_data == "view_about":
                await self._send_about(chat_id)
            return

        message = update.get("message")
        if not message:
            return

        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()
        first_name = message.get("from", {}).get("first_name", "there")
        user_id = message.get("from", {}).get("id")

        if not chat_id or not text:
            return

        # ── Mandatory Channel Membership Check ──────────────────
        if user_id:
            is_mem = await self.is_channel_member(user_id)
            if not is_mem:
                await self.send_join_channel_prompt(chat_id, user_id)
                return

        # ── Command: /start ──────────────────────────────────────
        if text.startswith("/start"):
            await self._send_welcome(chat_id, first_name)
            return

        # ── Command: /platforms ──────────────────────────────────
        if text.startswith("/platforms"):
            await self._send_platforms_list(chat_id)
            return

        # ── Command: /help ───────────────────────────────────────
        if text.startswith("/help"):
            await self._send_help_guide(chat_id)
            return

        # ── Command: /about ──────────────────────────────────────
        if text.startswith("/about"):
            await self._send_about(chat_id)
            return

        # ── Command: /download ───────────────────────────────────
        if text.startswith("/download"):
            await self._api_call("sendMessage", {
                "chat_id": chat_id,
                "text": "Paste any media link directly in this chat or tap below to open the search bar:",
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "⚡ Open Search Bar", "web_app": {"url": self.get_webapp_url()}}
                    ]]
                }
            })
            return

        # ── Direct URL Detection in Chat ────────────────────────
        url_match = re.search(r'(https?://[^\s]+)', text)
        if url_match:
            detected_url = url_match.group(1)
            platform_info = detect_platform(detected_url)
            p_name = platform_info.get("name", "Media")

            # 1. Send immediate acknowledgment
            status_res = await self._api_call("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    f"⚡ **{p_name} link received!**\n\n"
                    f"⏳ Downloading file to send directly into this chat...\n"
                    f"🔗 `{detected_url[:50]}...`"
                ),
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "⚡ Open 4K / MP3 Downloader", "web_app": {"url": self.get_webapp_url(detected_url)}}]
                    ]
                }
            })
            status_msg_id = (status_res or {}).get("result", {}).get("message_id")

            # 2. Trigger asynchronous direct-to-chat download
            asyncio.create_task(
                self._process_chat_download(chat_id, detected_url, p_name, status_msg_id)
            )
            return

        # Default fallback
        await self._api_call("sendMessage", {
            "chat_id": chat_id,
            "text": "Send me any video, music, or photo link from YouTube, Instagram, TikTok, Pinterest, Twitter, etc., or tap below to launch the Mini App:",
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🚀 Open Downloader Mini App", "web_app": {"url": self.get_webapp_url()}}
                ]]
            }
        })

    async def _process_chat_download(self, chat_id: int, url: str, platform_name: str, status_msg_id: Optional[int] = None):
        """Background worker that downloads media and sends the file directly into chat."""
        try:
            # Run blocking download in worker thread
            file_path, filename, content_type = await asyncio.to_thread(
                download_media_file, url=url, media_type="video", quality="720"
            )

            # Send file to chat
            await self.send_file_to_chat(
                chat_id=chat_id,
                file_path=file_path,
                filename=filename,
                title=filename,
                media_type="video"
            )

            # Update status message if available
            if status_msg_id:
                await self._api_call("editMessageText", {
                    "chat_id": chat_id,
                    "message_id": status_msg_id,
                    "text": (
                        f"✅ **{platform_name} Download Complete!**\n\n"
                        f"Your media file has been sent above 👆\n"
                        f"Tap below if you want 4K UHD, 320kbps MP3, or photo carousels:"
                    ),
                    "parse_mode": "Markdown",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "⚡ Open Mini App (4K / MP3)", "web_app": {"url": self.get_webapp_url(url)}}]
                        ]
                    }
                })
        except Exception as e:
            logger.error(f"Chat download worker error for {url}: {e}", exc_info=True)
            err_msg = str(e)
            if "verify" in err_msg.lower() or "captcha" in err_msg.lower():
                user_msg = (
                    "⚠️ TeraBox Verification Required\n\n"
                    "TeraBox triggered a security verification check for this file.\n"
                    "Please open the Mini App below or verify your login:"
                )
            else:
                # Strip special chars from error message to avoid Markdown parse errors
                safe_err = re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', err_msg[:200])
                user_msg = f"❌ Download failed: {safe_err}"

            if status_msg_id:
                await self._api_call("editMessageText", {
                    "chat_id": chat_id,
                    "message_id": status_msg_id,
                    "text": user_msg,
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "🚀 Open Downloader Mini App", "web_app": {"url": self.get_webapp_url(url)}}]
                        ]
                    }
                })
            else:
                await self._api_call("sendMessage", {
                    "chat_id": chat_id,
                    "text": user_msg,
                })

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """Escape special characters for Telegram MarkdownV2 parse mode."""
        # Characters that need escaping in MarkdownV2
        escape_chars = r'\_*[]()~`>#+-=|{}.!'
        return re.sub(r'([' + re.escape(escape_chars) + r'])', r'\\\1', text)

    async def send_file_to_chat(
        self,
        chat_id: int | str,
        file_path: str,
        filename: str = "",
        title: str = "",
        media_type: str = "video",
    ):
        """Send downloaded media directly into user's Telegram chat."""
        if not self.token or not chat_id:
            return

        if not os.path.exists(file_path):
            logger.error(f"Cannot send file {file_path}: File does not exist")
            return

        file_size = os.path.getsize(file_path)
        size_mb = round(file_size / (1024 * 1024), 2)
        display_title = title or filename or "Media File"
        clean_name = filename or os.path.basename(file_path)

        # Telegram Bot API standard upload limit is 50MB
        if file_size > 50 * 1024 * 1024:
            logger.info(f"File size {size_mb} MB exceeds Telegram 50MB direct upload limit.")
            file_token = str(uuid.uuid4())[:12]
            TEMP_SERVED_FILES[file_token] = {
                "path": file_path,
                "name": clean_name,
                "created_at": time.time()
            }
            dl_url = f"{self.get_webapp_url()}/api/downloader/direct/{file_token}"
            safe_title = self._escape_markdown(display_title)
            msg_text = (
                f"📹 {safe_title}\n\n"
                f"📦 Size: {size_mb} MB\n\n"
                f"ℹ️ Telegram has a 50MB bot upload limit\\. "
                f"Tap the button below to download the full\\-length file directly to your device:"
            )
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"📥 Save Full File ({size_mb} MB)", "url": dl_url}],
                    [{"text": "⚡ Open Downloader App", "web_app": {"url": self.get_webapp_url()}}]
                ]
            }
            await self._api_call("sendMessage", {
                "chat_id": chat_id,
                "text": msg_text,
                "parse_mode": "MarkdownV2",
                "reply_markup": keyboard
            })
            return

        # Upload file directly via multipart form — use plain text caption (no parse_mode)
        # to avoid Markdown entity parse errors from filenames with special chars
        caption = f"⚡ {display_title}\n\n✨ Downloaded via @loadrip_bot"
        caption = caption[:1024]

        method = "sendVideo" if media_type == "video" else "sendAudio" if media_type == "audio" else "sendPhoto" if media_type == "image" else "sendDocument"
        field_name = "video" if media_type == "video" else "audio" if media_type == "audio" else "photo" if media_type == "image" else "document"

        api_url = f"{TELEGRAM_API_BASE}/bot{self.token}/{method}"
        try:
            await self._api_call("sendChatAction", {
                "chat_id": chat_id,
                "action": "upload_video" if media_type == "video" else "upload_document"
            })

            async with httpx.AsyncClient(timeout=120.0) as client:
                # Read file bytes once to allow multiple upload attempts
                file_bytes = open(file_path, "rb").read()

                data = {
                    "chat_id": str(chat_id),
                    "caption": caption,
                    # No parse_mode — plain text captions are safest
                }

                # Try primary method (sendVideo / sendAudio / sendPhoto / sendDocument)
                import io
                res = await client.post(
                    api_url,
                    data=data,
                    files={field_name: (clean_name, io.BytesIO(file_bytes))}
                )
                res_json = res.json()

                if not res_json.get("ok") and method != "sendDocument":
                    # Fallback to sendDocument (works for any file type)
                    logger.warning(f"{method} failed ({res_json.get('description')}), retrying as sendDocument...")
                    fallback_url = f"{TELEGRAM_API_BASE}/bot{self.token}/sendDocument"
                    res = await client.post(
                        fallback_url,
                        data=data,
                        files={"document": (clean_name, io.BytesIO(file_bytes))}
                    )
                    res_json = res.json()

                if res_json.get("ok"):
                    logger.info(f"✅ Successfully sent {clean_name} ({size_mb} MB) to Telegram chat {chat_id}")
                else:
                    logger.error(f"Failed to send media to chat: {res_json}")
        except Exception as e:
            logger.error(f"Error sending file to Telegram chat: {e}", exc_info=True)

    async def _send_platforms_list(self, chat_id: int):
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🚀 Launch Downloader", "web_app": {"url": self.get_webapp_url()}}
                ],
                [
                    {"text": "📖 How to Use", "callback_data": "view_help"}
                ]
            ]
        }
        await self._api_call("sendMessage", {
            "chat_id": chat_id,
            "text": PLATFORM_DIRECTORY,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })

    async def _send_help_guide(self, chat_id: int):
        help_text = (
            "📖 **HOW TO USE ALL-IN-ONE DOWNLOADER**\n\n"
            "**Method 1: Using the Telegram Mini App (Recommended)**\n"
            "1. Tap **'⚡ Downloader'** in the bottom-left of your chat, or the button below.\n"
            "2. Paste any post, video, or album URL.\n"
            "3. Select your quality (4K, 1080p, 720p, 320kbps MP3, or Original Photo).\n"
            "4. Tap **Download**!\n\n"
            "**Method 2: Direct Chat Fast-Download**\n"
            "• Just copy a link from YouTube, Instagram, or TikTok and send it right into this chat.\n"
            "• The bot instantly analyzes it and returns a 1-click download button.\n\n"
            "**Shortcuts:**\n"
            "• `/start` — Main Menu & Mini App\n"
            "• `/platforms` — View all 1000+ supported sites\n"
            "• `/download` — Fast downloader prompt\n"
            "• `/about` — Format & Quality information"
        )
        keyboard = {
            "inline_keyboard": [[
                {"text": "🚀 Open Downloader Mini App", "web_app": {"url": self.get_webapp_url()}}
            ]]
        }
        await self._api_call("sendMessage", {
            "chat_id": chat_id,
            "text": help_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })

    async def _send_about(self, chat_id: int):
        about_text = (
            "ℹ️ **ABOUT ALL-IN-ONE DOWNLOADER**\n\n"
            "• **Engine:** Powered by high-speed async yt-dlp & FFmpeg muxing\n"
            "• **Max Video Quality:** 4K UHD (3840x2160) @ 60fps\n"
            "• **Max Audio Quality:** 320kbps High-Bitrate MP3 & Master WAV\n"
            "• **Photo Engine:** Lossless original resolution with Devanagari/Unicode title sanitization\n"
            "• **Cost:** 100% Free, zero watermarks, zero subscription\n\n"
            "Created for creator speed, mobile fluidity, and effortless downloads."
        )
        keyboard = {
            "inline_keyboard": [[
                {"text": "🚀 Launch Downloader", "web_app": {"url": self.get_webapp_url()}}
            ]]
        }
        await self._api_call("sendMessage", {
            "chat_id": chat_id,
            "text": about_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })


bot_service = TelegramBotService()
