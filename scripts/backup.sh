#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# CREWINTEL — Yedekleme Scripti
#
# Ne yapar:
#   1. PostgreSQL veritabanının tam dump'ını alır (pg_dump)
#   2. Storage klasörünün kopyasını alır
#   3. Yalnızca son N yedeği saklar (varsayılan: 14), eskilerini siler
#
# Kullanım (Git Bash / Linux / WSL — Docker kurulu olmalı):
#   ./scripts/backup.sh                  → varsayılan ayarlarla yedek alır
#   KEEP=30 ./scripts/backup.sh          → son 30 yedeği sakla
#   BACKUP_DIR=/mnt/disk/backups ./scripts/backup.sh
#
# Gece otomatik çalıştırma (Linux sunucu — crontab -e):
#   0 2 * * * cd /path/to/crewintel && ./scripts/backup.sh >> logs/backup.log 2>&1
#
# Windows (Görev Zamanlayıcı) için:
#   Program:  C:\Program Files\Git\bin\bash.exe
#   Argüman:  -lc "cd /d/CREWINTEL && ./scripts/backup.sh"
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# ── Ayarlar ──────────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
KEEP="${KEEP:-14}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-crewintel-postgres}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-crewintel-backend}"
POSTGRES_USER="${POSTGRES_USER:-crewintel}"
POSTGRES_DB="${POSTGRES_DB:-crewintel}"
# Storage klasörü backend container içindeki yol
STORAGE_CONTAINER_PATH="${STORAGE_CONTAINER_PATH:-/app/storage}"

STAMP="$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="$BACKUP_DIR/$STAMP"
mkdir -p "$TARGET_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Yedek başlıyor → $TARGET_DIR"

# ── 1) PostgreSQL dump ───────────────────────────────────────────────────────
echo "PostgreSQL dump alınıyor..."
if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
  docker exec "$POSTGRES_CONTAINER" \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --format=custom --no-owner --no-privileges \
    > "$TARGET_DIR/crewintel_db.dump"
else
  echo "HATA: '$POSTGRES_CONTAINER' container'ı bulunamadı. Docker çalışıyor mu?" >&2
  exit 1
fi

# ── 2) Storage kopyası ───────────────────────────────────────────────────────
echo "Storage kopyalanıyor..."
if docker ps --format '{{.Names}}' | grep -q "^${BACKEND_CONTAINER}$"; then
  docker cp "$BACKEND_CONTAINER:$STORAGE_CONTAINER_PATH" "$TARGET_DIR/storage"
else
  echo "HATA: '$BACKEND_CONTAINER' container'ı bulunamadı." >&2
  exit 1
fi

# ── 3) Bütünlük bilgisi ──────────────────────────────────────────────────────
DB_SIZE=$(du -sh "$TARGET_DIR/crewintel_db.dump" 2>/dev/null | cut -f1)
STORAGE_SIZE=$(du -sh "$TARGET_DIR/storage" 2>/dev/null | cut -f1)
echo "DB dump: $DB_SIZE · Storage: $STORAGE_SIZE"

# ── 4) Eski yedekleri temizle ────────────────────────────────────────────────
COUNT=$(ls -1 "$BACKUP_DIR" | grep -E '^[0-9]{8}_[0-9]{6}$' | wc -l)
if [ "$COUNT" -gt "$KEEP" ]; then
  ls -1dt "$BACKUP_DIR"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9] \
    | tail -n +"$((KEEP + 1))" | xargs -r rm -rf
  echo "Eski yedekler temizlendi (son $KEEP tutuldu)."
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Yedek TAMAMLANDI → $TARGET_DIR"
