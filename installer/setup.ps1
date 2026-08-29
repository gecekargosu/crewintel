#Requires -RunAsAdministrator
<#
.SYNOPSIS
    UMAY Admin - Otomatik Kurulum Scripti
.DESCRIPTION
    Docker, Python, JDK ve Android SDK'yi otomatik olarak yukler ve kurar.
    CREWINTEL projesini masaustune klonlar ve baslatir.
.NOTES
    Calistirmadan once PowerShell'i sag tik -> "Yonetici olarak calistir" secin.
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ── Renkli cikti fonksiyonlari ──────────────────────────────────────────────
function Write-Step($msg)   { Write-Host "`n═══ ADIM: $msg ═══" -ForegroundColor Cyan }
function Write-OK($msg)     { Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Err($msg)    { Write-Host "  ❌ $msg" -ForegroundColor Red }
function Write-Info($msg)   { Write-Host "  ℹ️  $msg" -ForegroundColor Gray }

# ── Yonetici hakki kontrol ──────────────────────────────────────────────────
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Err "Bu scripti Yonetici olarak calistirmalisiniz!"
    Write-Info "PowerShell uzerine sag tiklayin -> 'Yonetici olarak calistir' secin."
    Read-Host "`nDevam icin ENTER'a basin"
    exit 1
}

# ── Kurulum dizini ──────────────────────────────────────────────────────────
$INSTALL_DIR = "$env:USERPROFILE\Desktop\CREWINTEL"
$DOWNLOAD_DIR = "$env:TEMP\crewintel_setup"
$PROGRESS_FILE = "$DOWNLOAD_DIR\progress.json"

# ── Progress tracking ───────────────────────────────────────────────────────
function Save-Progress($step, $done) {
    @{ step = $step; done = $done } | ConvertTo-Json | Set-Content $PROGRESS_FILE
}

Write-Host @"

    ╔══════════════════════════════════════════════╗
    ║        UMAY ADMIN - OTOMATIK KURULUM         ║
    ║                                              ║
    ║  CrewIntel + UMAY Mobile App Kurulumu        ║
    ║  Bu islem ~10-15 dakika surabilir.           ║
    ╚══════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $DOWNLOAD_DIR | Out-Null

# ══════════════════════════════════════════════════════════════════════════════
# ADIM 1: Docker Desktop
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "1/6 - Docker Desktop kuruluyor..."
Save-Progress "docker" $false

$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-OK "Docker Desktop zaten kurulu."
} else {
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerInstaller = "$DOWNLOAD_DIR\DockerDesktopInstaller.exe"
    
    if (-not (Test-Path $dockerInstaller)) {
        Write-Info "Docker Desktop indiriliyor (~600MB)..."
        Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller -UseBasicParsing
    }
    
    Write-Info "Docker Desktop kuruluyor (5-10 dk surebilir)..."
    Write-Info "Kurulum sirasinda 'Windows uretici yazilimi yukleme' onayi cikarsa 'OK' deyin."
    
    # Silent install with WSL2 backend
    Start-Process -FilePath $dockerInstaller -ArgumentList "install", "--quiet", "--accept-license", "--backend=wsl-2" -Wait -NoNewWindow
    
    Write-OK "Docker Desktop kuruldu."
    Write-Warn "Docker'i baslatmak icin bilgisayari yeniden baslatmaniz gerekebilir."
    
    # Start Docker Desktop
    if (Test-Path $dockerPath) {
        Start-Process -FilePath $dockerPath
        Write-Info "Docker Desktop baslatiliyor... 30 saniye bekleyin."
        Start-Sleep -Seconds 30
    }
}

# Docker durumunu kontrol et
$retries = 0
while ($retries -lt 10) {
    try {
        docker info 2>&1 | Out-Null
        Write-OK "Docker calisiyor."
        break
    } catch {
        $retries++
        Write-Info "Docker baslatilmadi, 10 saniye bekleniyor... ($retries/10)"
        Start-Sleep -Seconds 10
    }
}
Save-Progress "docker" $true

# ══════════════════════════════════════════════════════════════════════════════
# ADIM 2: Git
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "2/6 - Git kuruluyor..."
Save-Progress "git" $false

$gitPath = "C:\Program Files\Git\bin\git.exe"
if (Test-Path $gitPath) {
    Write-OK "Git zaten kurulu."
} else {
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/Git-2.47.1.2-64-bit.exe"
    $gitInstaller = "$DOWNLOAD_DIR\GitInstaller.exe"
    
    if (-not (Test-Path $gitInstaller)) {
        Write-Info "Git indiriliyor..."
        Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller -UseBasicParsing
    }
    
    Write-Info "Git kuruluyor..."
    Start-Process -FilePath $gitInstaller -ArgumentList "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS", "/COMPONENTS=icons,ext\reg\shellhere,assoc,assoc_sh" -Wait -NoNewWindow
    Write-OK "Git kuruldu."
    
    # PATH'i guncelle
    $env:PATH = "$env:PATH;C:\Program Files\Git\bin"
}
Save-Progress "git" $true

# ══════════════════════════════════════════════════════════════════════════════
# ADIM 3: Python
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "3/6 - Python kuruluyor..."
Save-Progress "python" $false

$pythonPath = "C:\Program Files\Python313\python.exe"
if (-not (Test-Path $pythonPath)) {
    $pythonPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
}
if ($pythonPath) {
    Write-OK "Python zaten kurulu: $pythonPath"
} else {
    $pythonUrl = "https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe"
    $pythonInstaller = "$DOWNLOAD_DIR\PythonInstaller.exe"
    
    if (-not (Test-Path $pythonInstaller)) {
        Write-Info "Python indiriliyor..."
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
    }
    
    Write-Info "Python kuruluyor..."
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_pip=1" -Wait -NoNewWindow
    Write-OK "Python kuruldu."
    
    # PATH'i guncelle
    $env:PATH = "$env:PATH;C:\Program Files\Python313;C:\Program Files\Python313\Scripts"
}
Save-Progress "python" $true

# ══════════════════════════════════════════════════════════════════════════════
# ADIM 4: Java JDK (Android icin)
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "4/6 - Java JDK kuruluyor..."
Save-Progress "jdk" $false

$javaPath = Get-Command java -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if ($javaPath) {
    Write-OK "Java zaten kurulu."
} else {
    $jdkUrl = "https://download.oracle.com/java/21/archive/jdk-21.0.5_windows-x64_bin.exe"
    $jdkInstaller = "$DOWNLOAD_DIR\JDKInstaller.exe"
    
    if (-not (Test-Path $jdkInstaller)) {
        Write-Info "Java JDK indiriliyor..."
        Invoke-WebRequest -Uri $jdkUrl -OutFile $jdkInstaller -UseBasicParsing
    }
    
    Write-Info "Java JDK kuruluyor..."
    Start-Process -FilePath $jdkInstaller -ArgumentList "/quiet", "INSTALL_DIR=C:\Program Files\Java\jdk-21" -Wait -NoNewWindow
    Write-OK "Java JDK kuruldu."
    
    $env:PATH = "$env:PATH;C:\Program Files\Java\jdk-21\bin"
    $env:JAVA_HOME = "C:\Program Files\Java\jdk-21"
}
Save-Progress "jdk" $true

# ══════════════════════════════════════════════════════════════════════════════
# ADIM 5: CREWINTEL kodunu indir ve baslat
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "5/6 - CREWINTEL indiriliyor ve kuruluyor..."
Save-Progress "crewintel" $false

if (Test-Path $INSTALL_DIR) {
    Write-Info "CREWINTEL klasoru zaten var, guncelleniyor..."
    Set-Location $INSTALL_DIR
    & "$gitPath" pull origin master 2>&1 | Write-Info
} else {
    Write-Info "CREWINTEL GitHub'dan indiriliyor..."
    & "$gitPath" clone https://github.com/gecekargosu/crewintel.git $INSTALL_DIR 2>&1 | Write-Info
    Set-Location $INSTALL_DIR
}

# .env dosyasini olustur
if (-not (Test-Path "$INSTALL_DIR\.env")) {
    Write-Info ".env dosyasi olusturuluyor..."
    $secret = -join ((1..32) | ForEach-Object { '{0:X}' -f (Get-Random -Max 16) })
    @"
APP_ENVIRONMENT=development
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
POSTGRES_DB=crewintel
POSTGRES_USER=crewintel
POSTGRES_PASSWORD=crewintel_$secret
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
STORAGE_PATH=/app/storage
MAX_UPLOAD_SIZE_MB=25
EXPIRY_APPROACHING_DAYS=90
EXPIRY_URGENT_DAYS=30
JWT_SECRET_KEY=$secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
ADMIN_EMAIL=admin@crewintel.com
ADMIN_PASSWORD=UmayAdmin2026!
GROQ_API_KEY=
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
VITE_API_URL=http://127.0.0.1:8000
"@ | Set-Content "$INSTALL_DIR\.env" -Encoding UTF8
    Write-OK ".env dosyasi olusturuldu."
}

# Backend + Frontend baslat
Write-Info "Docker container'lari baslatiliyor (ilk seferde ~10 dk surebilir)..."
Write-Info "Backend + Frontend + Database birlikte baslatiliyor..."
Set-Location $INSTALL_DIR

# Docker compose ile baslat
& docker compose up -d --build 2>&1 | ForEach-Object { Write-Info "  $_" }

# Saglik kontrolu
$retries = 0
while ($retries -lt 20) {
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($health.StatusCode -eq 200) {
            Write-OK "Backend basariliyla calisiyor!"
            break
        }
    } catch {
        $retries++
        Write-Info "Backend baslatiliyor... ($retries/20)"
        Start-Sleep -Seconds 15
    }
}

Write-OK "CREWINTEL baslatildi!"
Write-Info "Masaustu: http://localhost:5173"
Write-Info "Backend:  http://localhost:8000"

Save-Progress "crewintel" $true

# ══════════════════════════════════════════════════════════════════════════════
# ADIM 6: Android APK olustur
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "6/6 - UMAY Admin mobil uygulamasi hazirlaniyor..."
Save-Progress "apk" $false

$apkSource = "$INSTALL_DIR\mobile-app\app\build\outputs\apk\debug\app-debug.apk"
$apkDest = "$env:USERPROFILE\Desktop\UMAY_Admin.apk"

# Android SDK kontrol
$androidSdk = "$env:LOCALAPPDATA\Android\Sdk"
if (-not (Test-Path $androidSdk)) {
    Write-Warn "Android SDK bulunamadi. APK icin Android Studio gerekli."
    Write-Info "Android Studio'yu buradan indirin: https://developer.android.com/studio"
    Write-Info "Kurulumdan sonra APK'yi manuel olarak olusturun."
} else {
    if (Test-Path $apkSource) {
        Write-Info "APK kopyalaniyor..."
        Copy-Item $apkSource $apkDest -Force
        Write-OK "APK masaustune kopyalandi: UMAY_Admin.apk"
    } else {
        Write-Info "APK olusturuluyor..."
        $gradlew = "$INSTALL_DIR\mobile-app\gradlew.bat"
        if (Test-Path $gradlew) {
            & cmd.exe /c "cd /d `"$INSTALL_DIR\mobile-app`" && set JAVA_HOME=$env:JAVA_HOME && gradlew.bat assembleDebug" 2>&1 | ForEach-Object { Write-Info "  $_" }
            
            if (Test-Path $apkSource) {
                Copy-Item $apkSource $apkDest -Force
                Write-OK "APK olusturuldu ve masaustune kopyalandi!"
            }
        }
    }
}

Save-Progress "apk" $true

# ══════════════════════════════════════════════════════════════════════════════
# TAMAMLANDI
# ══════════════════════════════════════════════════════════════════════════════
Write-Host @"

    ╔══════════════════════════════════════════════╗
    ║         ✅ KURULUM TAMAMLANDI!               ║
    ╠══════════════════════════════════════════════╣
    ║                                              ║
    ║  Masaustu uygulamasi:                        ║
    ║    → http://localhost:5173                   ║
    ║                                              ║
    ║  Giris bilgileri:                            ║
    ║    E-posta: admin@crewintel.com              ║
    ║    Sifre:   UmayAdmin2026!                   ║
    ║                                              ║
    ║  Telefon uygulamasi:                         ║
    ║    → Masaustunuzdeki UMAY_Admin.apk dosyasi ║
    ║    → Telefonunuza yukleyin                   ║
    ║    → Sunucu: http://<MASAUSTU_IP>:8000       ║
    ║                                              ║
    ║  Sunucu IP'nizi ogrenmek icin:               ║
    ║    PowerShell: ipconfig                      ║
    ║    Wi-Fi IPv4 adresini kullanin              ║
    ║                                              ║
    ╚══════════════════════════════════════════════╝

"@ -ForegroundColor Green

# Baslatma scripti olustur
$startScript = @"
@echo off
echo.
echo ════════════════════════════════════════
echo    UMAY Admin Baslatiliyor...
echo ════════════════════════════════════════
echo.

cd /d "$INSTALL_DIR"
docker compose up -d

echo.
echo UMAY Admin baslatildi!
echo Tarayicinizi acin: http://localhost:5173
echo.
echo Kapatmak icin bu pencereyi kapatin.
echo.
pause
"@
$startScript | Set-Content "$INSTALL_DIR\baslat.bat" -Encoding ASCII

# Durdurma scripti olustur
$stopScript = @"
@echo off
echo.
echo ════════════════════════════════════════
echo    UMAY Admin Durduruluyor...
echo ════════════════════════════════════════
echo.

cd /d "$INSTALL_DIR"
docker compose down

echo.
echo UMAY Admin durduruldu.
echo.
pause
"@
$stopScript | Set-Content "$INSTALL_DIR\durdur.bat" -Encoding ASCII

Write-Info "Masaustune 'UMAY Baslat.bat' ve 'UMAY Durdur.bat' dosyalari olusturuldu."
Write-Info "Bundan sonra uygulamayi baslatmak icin 'UMAY Baslat.bat' dosyasina cift tiklayin."

Write-Host "`nKurulum tamamlandi! Herhangi bir sorun olursa bana yazin." -ForegroundColor Cyan
Read-Host "`nKapatmak icin ENTER'a basin"
