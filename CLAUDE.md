# CREWINTEL — AI / yeni geliştirici giriş rehberi

Bu klasöre bakan bir insan veya AI, aşağıdaki sırayla okuyarak **projeyi
sıfırdan tarayadan** anlayabilir. Son güncelleme: **2026-10-06**.

## Hızlı anlayış

- **Ne bu?** Gemi personeli (crew management) platformu: personel özlük, gemi
  atamaları, kontratlar, belge arşivi + OCR, belge→personel otomatik
  eşleştirme, belge geçerlilik takibi, iş ilanları/portallar, AI modülleri.
- **Teknoji:** FastAPI + SQLAlchemy/Alembic + PostgreSQL (backend),
  React/Vite + 4 dil i18n (frontend), Docker Compose, Android (Kotlin) istemci.
- **Durum:** Backend stabil, frontend fonksiyonel, testler yeşil
  (`284 passed / 2 skipped`), GERMAN SKY gerçek verisi yüklü.

## Nereden ne okunur (öncelik sırası)

| Sıra | Dosya | Ne öğretir |
|---|---|---|
| 1 | `CLAUDE.md` (bu dosya) | Komutlar, kapsam, dikkat edilecekler |
| 2 | `docs/ARCHITECTURE.md` | Sistem mimarisi: servisler, yükleme hattı, match motoru ağırlıkları |
| 3 | `docs/DEVELOPMENT_LOG.md` | Proje belleği: fazlar, API envanteri, CHANGELOG, kırmızı çizgiler |
| 4 | `docs/DUZELTME_LISTESI_UPLOAD.md` | Son düzeltme turu: H1–H14 hata kök nedenleri + doğrulamalar |
| 5 | `docs/system-tree/` | Modül bazlı detay (BACKEND, FRONTEND, DATABASE, INTEGRATIONS) |
| 6 | `docs/ROADMAP/` | Planlar ve mevcut durum matrisleri |
| 7 | `tests/` | Davranışın kaynağı — testler spec gibi okunur |

## Sık kullanılan komutlar

```bash
# Test (kök dizinden; sqlite in-memory kullanır)
backend/.venv/Scripts/python.exe -m pytest tests/ -q     # beklenti: 284 passed

# Frontend
cd frontend && npm run lint && npm run build

# Servisler
docker compose up -d
docker compose build backend frontend && docker compose up -d backend frontend
docker ps --format "{{.Names}} {{.Status}}"

# Canlı API doğrulama
curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@crewintel.example","password":"<backend/.env/seed>'}"
```

Giriş rolleri: `admin/manager/hr/operator/viewer`. Yetki bağımlılıkları
`require_roles(...)`, `require_staff_read` (route'larda).

## Sınırlar ve eşit tutulması gerekenler

- **Yükleme limiti 100MB** — 6 yerde aynı: `document_service.MAX_UPLOAD_SIZE`,
  `core/config.max_upload_size_mb`, `docker-compose.yml MAX_UPLOAD_SIZE_MB`,
  `.env.example` ×2, `installer/setup.ps1`, `frontend/nginx.conf client_max_body_size`.
- **API `limit` parametresi en fazla 200** (500 → 422).
- **Yeni arayüz metni** 4 locale dosyasına (`tr/en/ru/ar.ts`) eklenmeli.
- **Şema değişikliği** yalnızca Alembic migration ile.

## Sık yapılan hatalar (geçmişte yaşandı, tekrarlama)

1. `.txt`/`.pdf` dışı dosyalar istemcide sessizce eleniyordu → her uzantı
   genişlemesinde `ALLOWED_EXT` (App.jsx) ve `ALLOWED_UPLOAD_EXTENSIONS`
   (document_service) birlikte güncellenmeli.
2. Metinlerdeki `NUL` byte PostgreSQL'i 500 yapıyordu → `extract_text`
   sarmalayıcısı bunu temizler; yeni metin kaynakları da buradan geçmeli.
3. `mehmet cetin` ↔ `mehmet cetiner` gibi **sınırsız substring** eşleşmesi
   yanlış aday üretir → match motorunda her arama `f" {needle} "` şeklinde
   kelime sınırıyla yapılır.
4. Toplu yüklemede tek dosyanın 413/415 vermesi tüm chunk'ı düşürebilir
   (`failed_details` alanına bak).

## Depo düzeni

```
backend/      FastAPI uygulaması + Dockerfile (tesseract, libreoffice, poppler)
frontend/     Vite React uygulaması + nginx.conf
mobile-app/   Android istemci (com.crewintel.mobile)
tests/        17 dosya, pytest
docs/         Mimari, geliştirme logu, düzeltme listesi, roadmap, system-tree
installer/    Windows kurulumu (setup.ps1)
social-downloader/  yt-dlp + ffmpeg servisi
scripts/      Yardımcı scriptler
```

Gitignore'da: `.env*`, `storage/`, `*.db`, `.freebuff/`, `backups/`,
`node_modules/`, `frontend/dist/`, `mobile/`. **Gerçek parola/anahtar repoya girmez.**

## Kızıl çizgiler (docs/DEVELOPMENT_LOG.md §14)

- Migration'sız şema değişikliği yok.
- Üretim verisine/eldeki veritabanına test verisi yazılmaz.
- `.env` ve yüklenmiş belgeler (`storage/`) commit edilmez.
- Yetkisiz rol endpoint'lerine erişemez; her route'ta bağımlılık kontrolü var.
