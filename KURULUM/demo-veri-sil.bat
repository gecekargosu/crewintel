@echo off
chcp 65001 >nul
title CREWINTEL - Demo Veri Sil
cd /d "%~dp0.."

echo Bu islem SADECE demo verilerini siler.
echo Gercek personel/gemi kayitlariniza dokunulmaz.
echo.
choice /c EH /m "Devam edilsin mi"
if errorlevel 2 exit /b 0

docker compose exec -T backend python -m app.db.demo --purge
if errorlevel 1 (
  echo [HATA] Silme basarisiz. Program calisiyor mu?
  pause
  exit /b 1
)
echo.
echo Demo veriler silindi.
timeout /t 4 >nul
exit /b 0
