$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "        CREWINTEL PROJECT STATUS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

function Check-Status {
    param(
        [string]$Name,
        [bool]$Ok
    )

    if ($Ok) {
        Write-Host ("{0,-30} [ OK ]" -f $Name) -ForegroundColor Green
    }
    else {
        Write-Host ("{0,-30} [FAIL]" -f $Name) -ForegroundColor Red
    }
}

# -------------------------------------------------
# DOCKER
# -------------------------------------------------

$backend = docker inspect -f "{{.State.Running}}" crewintel-backend 2>$null
$postgres = docker inspect -f "{{.State.Running}}" crewintel-postgres 2>$null
$frontend = docker inspect -f "{{.State.Running}}" crewintel-frontend 2>$null

Check-Status "Backend container" ($backend -eq "true")
Check-Status "PostgreSQL container" ($postgres -eq "true")
Check-Status "Frontend container" ($frontend -eq "true")

# -------------------------------------------------
# BACKEND HEALTH
# -------------------------------------------------

$health = $null
try {
    $health = Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 5
} catch {}

Check-Status "Backend /health" ($null -ne $health)

$dbHealth = $null
try {
    $dbHealth = Invoke-RestMethod "http://localhost:8000/health/database" -TimeoutSec 5
} catch {}

Check-Status "Database health API" ($null -ne $dbHealth)

# -------------------------------------------------
# API ENDPOINTS
# -------------------------------------------------

$apis = @(
    @{ Name = "Crew API"; Url = "http://localhost:8000/api/crew/" },
    @{ Name = "Ships API"; Url = "http://localhost:8000/api/ships/" },
    @{ Name = "Assignments API"; Url = "http://localhost:8000/api/assignments/" },
    @{ Name = "Contracts API"; Url = "http://localhost:8000/api/contracts/" },
    @{ Name = "Documents API"; Url = "http://localhost:8000/api/documents/" },
    @{ Name = "Expiration API"; Url = "http://localhost:8000/api/expiration/summary" },
    @{ Name = "Audit API"; Url = "http://localhost:8000/api/audit-logs/" }
)

Write-Host ""
Write-Host "[ API STATUS ]" -ForegroundColor Yellow

foreach ($api in $apis) {
    $result = $null

    try {
        $result = Invoke-RestMethod $api.Url -TimeoutSec 5
    } catch {}

    Check-Status $api.Name ($null -ne $result)
}

# -------------------------------------------------
# EXPIRATION
# -------------------------------------------------

$expiration = $null

try {
    $expiration = Invoke-RestMethod "http://localhost:8000/api/expiration/summary" -TimeoutSec 5
} catch {}

Write-Host ""
Write-Host "[ EXPIRATION ]" -ForegroundColor Yellow

if ($null -ne $expiration) {
    Write-Host ("Expired                  : {0}" -f $expiration.expired)
    Write-Host ("Urgent                   : {0}" -f $expiration.urgent)
    Write-Host ("Approaching              : {0}" -f $expiration.approaching)
    Write-Host ("Valid                    : {0}" -f $expiration.valid)
    Write-Host ("No expiry date           : {0}" -f $expiration.no_date)
    Write-Host ("Total documents          : {0}" -f $expiration.total)
}
else {
    Write-Host "Expiration service unavailable." -ForegroundColor Red
}

# -------------------------------------------------
# DOCUMENTS
# -------------------------------------------------

$documents = $null

try {
    $documents = @(Invoke-RestMethod "http://localhost:8000/api/documents/" -TimeoutSec 5)
} catch {}

Write-Host ""
Write-Host "[ DOCUMENT ARCHIVE ]" -ForegroundColor Yellow

if ($null -ne $documents) {
    Write-Host ("Documents in archive     : {0}" -f $documents.Count)

    $matched = @($documents | Where-Object { $_.match_status -eq "matched" }).Count
    $unmatched = @($documents | Where-Object { $_.match_status -eq "unmatched" }).Count

    Write-Host ("Matched                  : {0}" -f $matched)
    Write-Host ("Unmatched                : {0}" -f $unmatched)
}
else {
    Write-Host "Document API unavailable." -ForegroundColor Red
}

# -------------------------------------------------
# AUDIT
# -------------------------------------------------

$audit = $null

try {
    $audit = @(Invoke-RestMethod "http://localhost:8000/api/audit-logs/" -TimeoutSec 5)
} catch {}

Write-Host ""
Write-Host "[ AUDIT ]" -ForegroundColor Yellow

if ($null -ne $audit) {
    Write-Host ("Audit events             : {0}" -f $audit.Count)

    if ($audit.Count -gt 0) {
        $last = $audit[0]

        Write-Host ("Last action              : {0}" -f $last.action)
        Write-Host ("Last entity              : {0}" -f $last.entity)
        Write-Host ("Last message             : {0}" -f $last.message)
    }
}
else {
    Write-Host "Audit API unavailable." -ForegroundColor Red
}

# -------------------------------------------------
# MIGRATIONS
# -------------------------------------------------

Write-Host ""
Write-Host "[ DATABASE MIGRATIONS ]" -ForegroundColor Yellow

$migrations = Get-ChildItem ".\backend\alembic\versions" -File -Filter "*.py" |
    Where-Object { $_.Name -notmatch "__pycache__" }

Write-Host ("Migration files          : {0}" -f $migrations.Count)

foreach ($migration in $migrations) {
    Write-Host ("  + {0}" -f $migration.Name)
}

# -------------------------------------------------
# IMPORTANT FILES
# -------------------------------------------------

Write-Host ""
Write-Host "[ CORE FILES ]" -ForegroundColor Yellow

$coreFiles = @(
    ".\backend\app\main.py",
    ".\backend\app\models\crew_member.py",
    ".\backend\app\models\document.py",
    ".\backend\app\schemas\document.py",
    ".\backend\app\services\document_processing.py",
    ".\backend\app\services\document_service.py",
    ".\backend\app\services\expiration_service.py",
    ".\backend\app\services\audit.py",
    ".\backend\app\api\routes\documents.py",
    ".\backend\app\api\routes\expiration.py",
    ".\backend\app\api\routes\audit_logs.py"
)

foreach ($file in $coreFiles) {
    Check-Status $file (Test-Path $file)
}

# -------------------------------------------------
# PYTHON COMPILE CHECK
# -------------------------------------------------

Write-Host ""
Write-Host "[ PYTHON SYNTAX ]" -ForegroundColor Yellow

$compileOutput = python -m py_compile `
    .\backend\app\main.py `
    .\backend\app\api\routes\documents.py `
    .\backend\app\api\routes\expiration.py `
    .\backend\app\services\document_processing.py `
    .\backend\app\services\document_service.py `
    .\backend\app\services\expiration_service.py 2>&1

Check-Status "Core Python compile" ($LASTEXITCODE -eq 0)

# -------------------------------------------------
# FINAL STATUS
# -------------------------------------------------

$allContainersOk = (
    $backend -eq "true" -and
    $postgres -eq "true" -and
    $frontend -eq "true"
)

$backendOk = ($null -ne $health)
$dbOk = ($null -ne $dbHealth)

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

if ($allContainersOk -and $backendOk -and $dbOk) {
    Write-Host "          SYSTEM STATUS: OPERATIONAL" -ForegroundColor Green
}
else {
    Write-Host "          SYSTEM STATUS: CHECK REQUIRED" -ForegroundColor Red
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
