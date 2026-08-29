@echo off
chcp 65001 >nul
title UMAY Admin - Kurulum
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║        UMAY ADMIN - KURULUM BASLATIYOR       ║
echo  ║                                              ║
echo  ║  Bu kurulum su islemleri yapacak:            ║
echo  ║  1. Docker Desktop kurulacak                 ║
echo  ║  2. Git kurulacak                            ║
echo  ║  3. Python kurulacak                         ║
echo  ║  4. Java JDK kurulacak                       ║
echo  ║  5. CREWINTEL indirilecek ve baslatilacak    ║
echo  ║  6. Telefon uygulamasi (APK) hazirlanacak    ║
echo  ║                                              ║
echo  ║  ~10-15 dakika surebilir                     ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  OneNOT: Bu islemi YONETICI olarak calistirmaniz lazim!
echo.
echo  Devam etmek icin herhangi bir tusa basin...
pause >nul

echo.
echo PowerShell yonetici olarak baslatiliyor...
echo.

:: PowerShell'i yonetici olarak calistir
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0setup.ps1\"' -Verb RunAs"

echo.
echo Kurulum tamamlandi!
echo.
pause
