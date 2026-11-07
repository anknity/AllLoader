# 📱 All-in-One Media Downloader — Mobile Mini App

A standalone, mobile-first Universal Media Downloader mini app created from ViralScope. It runs completely separated on its own ports without depending on the main ViralScope platform database.

---

## ⚡ Highlights

- **Complete Independence**: Runs on its own ports (`8001` for backend, `5174` for frontend).
- **Mobile-Optimized UX**:
  - One-tap **"Paste Link"** button using `navigator.clipboard`.
  - Telegram Mini App compatible (auto-initializes with Telegram WebApp SDK).
  - iOS & Android notch / home indicator safe area support (`viewport-fit=cover`).
  - Mobile sticky bottom action bar for effortless one-thumb downloading.
  - Responsive 2-column mobile photo album grid.
- **Universal Platform Support**:
  - **YouTube**: 360p up to **4K (2160p)** with FFmpeg muxing + audio extraction.
  - **Instagram**: Reels, posts, stories, and carousel photo sets.
  - **TikTok**: High-res watermark-free video downloads.
  - **Pinterest**: Pins and **full-resolution multi-photo carousels** with individual & batch downloads.
  - **Twitter / X**: Videos, GIFs, and uncompressed high-res images.
  - **TeraBox**: Cloud video and file downloads.
  - **Reddit, Vimeo, SoundCloud, Dailymotion, Twitch, Bilibili & 1000+ more**.
- **Same ViralScope Theme**: Styled with Outfit, Plus Jakarta Sans, `#0F0F12` dark surfaces, `#FF4D26` vibrant coral, and fluid Framer Motion animations.

---

## 🚀 How to Run

Double-click the launcher script in this folder:
```bash
start_mini_downloader.bat
```

Or run manually:

### 1. Start Backend (Port 8001)
```bash
cd backend
..\..\backend\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Start Frontend (Port 5174)
```bash
cd frontend
npm run dev
```

- **Open on PC**: `http://localhost:5174`
- **Open on Phone (Same Wi-Fi)**: `http://<YOUR_PC_IP>:5174`

