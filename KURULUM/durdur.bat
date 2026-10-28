@echo off
chcp 65001 >nul
title CREWINTEL - Durdur
cd /d "%~dp0.."

echo CREWINTEL durduruluyor (veriler korunur)...
docker compose stop
echo.
echo Durduruldu. Tekrar acmak icin baslat.bat dosyasina cift tiklayin.
timeout /t 4 >nul
exit /b 0
