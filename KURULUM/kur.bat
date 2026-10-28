@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title CREWINTEL - Kurulum
cd /d "%~dp0.."

echo ============================================================
echo   CREWINTEL - Kurulum Basliyor
echo ============================================================
echo.

rem --- 1) Docker kontrolu -------------------------------------------------
where docker >nul 2>&1
if errorlevel 1 (
  echo [HATA] Docker bulunamadi.
  echo Lutfen once Docker Desktop'i kurun: https://www.docker.com/products/docker-desktop/
  echo Kurulumdan sonra bilgisayari yeniden baslatin ve bu dosyayi tekrar calistirin.
  echo.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo [HATA] Docker Desktop kapali gorunuyor.
  echo Baslat menusunden "Docker Desktop"i acin, balina ikonu yesile donene kadar bekleyin
  echo ve bu pencereyi kapatip kur.bat dosyasina tekrar cift tiklayin.
  echo.
  pause
  exit /b 1
)
echo [OK] Docker calisiyor.
echo.

rem --- 2) .env dosyasi ----------------------------------------------------
if exist ".env" (
  echo [OK] .env dosyasi mevcut, oldugu gibi kullanilacak.
) else (
  echo [!] Ilk kurulum: ayar dosyasi olusturuluyor.
  if not exist ".env.example" (
    echo [HATA] .env.example bulunamadi. Klasor eksik indirilmis olabilir.
    pause
    exit /b 1
  )
  copy /y ".env.example" ".env" >nul

  set "ADMINPASS="
  set /p ADMINPASS=Yonetici sifresi (en az 8 karakter, bos birakirsaniz Admin1234! olur): 
  if "!ADMINPASS!"=="" set "ADMINPASS=Admin1234!"

  set "ADMINMAIL="
  set /p ADMINMAIL=Yonetici e-posta adresi (bos birakirsaniz admin@crewintel.com): 
  if "!ADMINMAIL!"=="" set "ADMINMAIL=admin@crewintel.com"

  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$p='.env'; $c=Get-Content -Raw -Encoding UTF8 $p;" ^
    "$secret=-join ((48..57)+(97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_});" ^
    "$c=$c -replace '(?m)^JWT_SECRET_KEY=.*', ('JWT_SECRET_KEY=' + $secret);" ^
    "$c=$c -replace '(?m)^ADMIN_EMAIL=.*', ('ADMIN_EMAIL=' + $env:ADMINMAIL);" ^
    "$c=$c -replace '(?m)^ADMIN_PASSWORD=.*', ('ADMIN_PASSWORD=' + $env:ADMINPASS);" ^
    "Set-Content -Encoding UTF8 -NoNewline $p $c;"

  echo [OK] .env olusturuldu.
  echo.
  echo     Giris e-postasi : !ADMINMAIL!
  echo     Giris sifresi   : !ADMINPASS!
  echo     ^(Bu bilgileri bir yere not edin.^)
  echo.
)

rem --- 3) Baslat ----------------------------------------------------------
echo [!] Program baslatiliyor. Ilk kurulumda 5-15 dakika surebilir...
echo     Bu pencereyi KAPATMAYIN.
echo.
docker compose up -d --build
if errorlevel 1 (
  echo.
  echo [HATA] Kurulum sirasinda hata olustu. Ayrintilar icin sorun-raporu.bat calistirin.
  pause
  exit /b 1
)

echo.
echo [!] Sunucunun hazir olmasi bekleniyor (en fazla 3 dakika)...
set /a TRIES=0
:WAITLOOP
set /a TRIES+=1
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://localhost:5173/ ; if ($r.StatusCode -ge 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto READY
if %TRIES% GEQ 60 goto NOTREADY
timeout /t 3 >nul
goto WAITLOOP

:NOTREADY
echo.
echo [!] Arayuz henuz yanit vermedi. Muhtemelen arka planda hala derleniyor.
echo     Kontrol: docker compose logs -f
echo     Tarayiciyi elle acabilirsiniz: http://localhost:5173
start "" http://localhost:5173
goto END

:READY
echo.
echo ============================================================
echo   KURULUM TAMAMLANDI
echo ============================================================
echo.
echo   Adres    : http://localhost:5173
echo   E-posta  : .env dosyasindaki ADMIN_EMAIL
echo   Sifre    : .env dosyasindaki ADMIN_PASSWORD
echo.
echo   Programi kapatmak icin : durdur.bat
echo   Tekrar acmak icin      : baslat.bat
echo   Demo veri yuklemek icin: demo-veri-yukle.bat
echo.
start "" http://localhost:5173

:END
echo.
pause
endlocal
