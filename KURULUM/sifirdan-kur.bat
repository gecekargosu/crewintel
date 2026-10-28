@echo off
chcp 65001 >nul
title CREWINTEL - Sifirdan Kur
cd /d "%~dp0.."

echo ============================================================
echo   DIKKAT: BU ISLEM TUM VERILERI SILER
echo ============================================================
echo.
echo   Silinecekler: personel, gemiler, kontratlar, yuklenen belgeler,
echo   mesajlar, ilanlar ve kullanici hesaplari.
echo.
echo   Sadece programi bastan denemek istiyorsaniz kullanin.
echo   Verilerinizi kaybetmemek icin once 05-YEDEKLEME dosyasindaki
echo   yedek alma adimini uygulayin.
echo.
set "ONAY="
set /p ONAY=Devam etmek icin SIL yazip Enter'a basin (vazgecerseniz bos birakin): 
if /i not "%ONAY%"=="SIL" (
  echo Vazgecildi. Hicbir sey silinmedi.
  timeout /t 4 >nul
  exit /b 0
)

echo.
echo [1/4] Konteynerler durduruluyor...
docker compose down
echo [2/4] Veritabani ve belge deposu siliniyor...
docker volume rm crewintel_crewintel_postgres_data >nul 2>&1
if exist "storage" (
  rmdir /s /q "storage" 2>nul
)
echo [3/4] Eski ayar dosyasi yedekleniyor...
if exist ".env" ren ".env" ".env.eski"
echo [4/4] Yeniden kurulum baslatiliyor...
call "%~dp0kur.bat"
