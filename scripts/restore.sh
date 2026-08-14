#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# CREWINTEL — Restore Scripti
#
# Kullanım:
#   ./scripts/restore.sh backups/20260818_023000
#
# Ne yapar:
#   1. Seçilen yedekteki DB dump'ını geri yükler (önce mevcut veriyi DROP eder!)
#   2. Storage klasörünü container'a geri kopyalar
#   3. Backend'i yeniden başlatır
#
# ⚠️  DİKKAT: Restore, mevcut veritabanını SİLER ve yedekle değiştirir.
#     Önce ./scripts/backup.sh ile güncel yedek aldığından emin ol.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [ "$#" -lt 1 ]; then
  echo "Kullanım: ./scripts/restore.sh <yedek_klasörü>" >&2
  echo "Mevcut yedekler:" >&2
  ls -1dt "$PROJECT_DIR"/backups/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9] 2>/dev/null || echo "  (yok)"
  exit 1
fi

BACKUP_PATH="$1"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-crewintel-postgres}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-crewintel-backend}"
POSTGRES_USER="${POSTGRES_USER:-crewintel}"
POSTGRES_DB="${POSTGRES_DB:-crewintel}"
STORAGE_CONTAINER_PATH="${STORAGE_CONTAINER_PATH:-/app/storage}"

DB_DUMP="$BACKUP_PATH/crewintel_db.dump"
STORAGE_SRC="$BACKUP_PATH/storage"

[ -f "$DB_DUMP" ] || { echo "HATA: $DB_DUMP bulunamadı." >&2; exit 1; }
[ -d "$STORAGE_SRC" ] || { echo "HATA: $STORAGE_SRC bulunamadı." >&2; exit 1; }

echo "⚠️  '$BACKUP_PATH' yedeği geri yüklenecek. Bu işlem MEVCUT VERİYİ SİLER."
read -r -p "Emin misin? (evet yaz): " CONFIRM
[ "$CONFIRM" = "evet" ] || { echo "İptal edildi."; exit 1; }

echo "Veritabanı geri yükleniyor (mevcut veri silinir)..."
docker exec -i "$POSTGRES_CONTAINER" \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-privileges \
  < "$DB_DUMP"

echo "Storage geri yükleniyor..."
docker cp "$STORAGE_SRC/." "$BACKEND_CONTAINER:$STORAGE_CONTAINER_PATH"

echo "Backend yeniden başlatılıyor..."
docker restart "$BACKEND_CONTAINER"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] RESTORE TAMAMLANDI"
