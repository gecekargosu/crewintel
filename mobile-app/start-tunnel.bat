@echo off
echo ========================================
echo   CREWINTEL - Mobil Erisim Tunnel
echo ========================================
echo.
echo ngrok baslatiliyor (port 8000)...
echo URL'yi ogrenmek icin: http://127.0.0.1:4040
echo.
echo Android uygulamasina su URL'yi gir:
echo   (ngrok URL'sini asagida goreceksiniz)
echo.
ngrok http 8000
pause
