@echo off
chcp 65001 >nul
title CREWINTEL - Demo Veri Yukle
cd /d "%~dp0.."

docker info >nul 2>&1
if errorlevel 1 (
  echo [HATA] Docker Desktop kapali. Once onu acin.
  pause
  exit /b 1
)

echo Ornek veriler yukleniyor (3 gemi, 8 personel, kontratlar)...
echo Var olan gercek verilere dokunulmaz.
echo.
docker compose exec -T backend python -m app.db.demo
if errorlevel 1 (
  echo.
  echo [HATA] Demo veri yuklenemedi. Program calisiyor mu? Once baslat.bat deneyin.
  pause
  exit /b 1
)

echo.
echo Bitti. Tarayicida sayfayi yenileyin (F5).
timeout /t 5 >nul
exit /b 0
