@echo off
title Deploy All-in-One Downloader to Fly.io
echo ========================================================
echo       Deploy Mini App to Fly.io (Single Container)
echo ========================================================
echo.

where flyctl >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] flyctl is not installed or not in PATH!
    echo.
    echo To install Fly CLI on Windows, run this in PowerShell:
    echo   iwr https://fly.io/install.ps1 -useb ^| iex
    echo.
    echo After installation, reopen this script.
    pause
    exit /b 1
)

echo Checking Fly.io login status...
flyctl auth whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo You need to log in to Fly.io first.
    echo Running 'flyctl auth login'...
    flyctl auth login
)

echo.
echo ========================================================
echo  Step 1: Building Frontend for Production
echo ========================================================
cd /d %~dp0frontend
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b 1
)

echo.
echo Copying frontend build to backend static folder...
cd /d %~dp0
xcopy /E /I /Y "frontend\dist" "backend\static" >nul

echo.
echo ========================================================
echo  Step 2: Deploying to Fly.io
echo ========================================================
flyctl deploy --remote-only

echo.
echo ========================================================
echo  Deployment Complete!
echo ========================================================
flyctl status
echo.
pause

