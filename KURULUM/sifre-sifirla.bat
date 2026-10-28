@echo off
chcp 65001 >nul
title CREWINTEL - Sifre Sifirlama
cd /d "%~dp0.."

echo ==========================================================
echo   CREWINTEL - Sifre Sifirlama Araci
echo ==========================================================
echo.
echo Bu arac, programdaki bir kullanicinin sifresini sifirlar.
echo Sifrenizi unuttuysaniz bu dosyayi calistirin.
echo.

docker ps --format "{{.Names}}" | findstr /C:"crewintel-backend" >nul
if errorlevel 1 (
  echo HATA: CREWINTEL calismiyor.
  echo Once "baslat.bat" dosyasini calistirin, sonra bu araci tekrar acin.
  echo.
  pause
  exit /b 1
)

echo ---- Kayitli hesaplar ----
docker exec crewintel-backend python -m scripts.sifre_sifirla --liste
echo.
set /p HESAP="Sifresi sifirlanacak e-posta adresini yazin: "

echo.
echo Yeni sifre otomatik olusturuluyor...
echo.
docker exec crewintel-backend python -m scripts.sifre_sifirla %HESAP%

echo.
echo Yukaridaki SIFRE satirini not alin. Programa bu sifreyle giris yapabilirsiniz.
echo.
pause
