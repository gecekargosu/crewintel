@echo off
chcp 65001 >nul
title CREWINTEL - Baslat
cd /d "%~dp0.."

docker info >nul 2>&1
if errorlevel 1 (
  echo [HATA] Docker Desktop kapali. Once onu acin, sonra tekrar deneyin.
  pause
  exit /b 1
)

echo CREWINTEL baslatiliyor...
docker compose up -d
if errorlevel 1 (
  echo [HATA] Baslatma basarisiz. Ayrintilar icin sorun-raporu.bat calistirin.
  pause
  exit /b 1
)

echo Tarayici aciliyor: http://localhost:5173
timeout /t 4 >nul
start "" http://localhost:5173
exit /b 0
