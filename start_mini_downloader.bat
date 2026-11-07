@echo off
title All-in-One Downloader Mini App + Cloudflare Gateway
echo ========================================================
echo       All-in-One Media Downloader - Mobile Mini App
echo ========================================================
echo.
echo Starting Unified Backend & Telegram Bot (Port 8001)...
start "Downloader Backend & Bot" cmd /k "cd /d %~dp0backend && ..\..\backend\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001"

timeout /t 2 >nul

echo Starting Cloudflare Tunnel Gateway...
start "Cloudflare Gateway" cmd /k "cd /d %~dp0 && ..\backend\venv\Scripts\python.exe start_cloudflare_tunnel.py"

echo.
echo ========================================================
echo  ✅ Local API & UI: http://localhost:8001
echo  ☁️ Cloudflare Gateway auto-connects to @loadrip_bot!
echo ========================================================
echo.
