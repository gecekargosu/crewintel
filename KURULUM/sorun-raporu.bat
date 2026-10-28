@echo off
chcp 65001 >nul
title CREWINTEL - Sorun Raporu
cd /d "%~dp0.."

set "RAPOR=sorun-raporu.txt"
echo CREWINTEL sorun raporu > "%RAPOR%"
echo Tarih: %DATE% %TIME% >> "%RAPOR%"
echo. >> "%RAPOR%"

echo ==== SURUMLER ==== >> "%RAPOR%"
docker --version >> "%RAPOR%" 2>&1
docker compose version >> "%RAPOR%" 2>&1
echo. >> "%RAPOR%"

echo ==== KONTEYNER DURUMU ==== >> "%RAPOR%"
docker compose ps >> "%RAPOR%" 2>&1
echo. >> "%RAPOR%"

echo ==== SON 200 SATIR LOG ==== >> "%RAPOR%"
docker compose logs --tail 200 >> "%RAPOR%" 2>&1
echo. >> "%RAPOR%"

echo ==== PORTLAR ==== >> "%RAPOR%"
netstat -ano | findstr ":5173 :8000 :5433" >> "%RAPOR%" 2>&1

echo Rapor olusturuldu: %CD%\%RAPOR%
echo.
echo Bu dosyayi teknik destek veren kisiye gonderebilirsiniz.
echo (Icerisinde sifre yoktur; sadece hata kayitlari vardir.)
notepad "%RAPOR%"
exit /b 0
