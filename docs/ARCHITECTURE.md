# CREWINTEL — Sistem Mimari (güncel: 2026-10-06)

CREWINTEL, gemi personeli operasyonları için tek HTTP API ve üç istemci yüzeyi
(Web, Android, REST portal) etrafında tasarlanmıştır. Teknoji: **FastAPI +
SQLAlchemy/Alembic + PostgreSQL** (backend), **React/Vite + i18n** (frontend),
**Docker Compose** (dağıtım).

```text
Web (React/Vite) ─┐
Android (Kotlin) ─┼──HTTP──> FastAPI backend ──SQLAlchemy──> PostgreSQL
REST portal     ─┘            │
                              └── dosya hattı: validate → PDF'e çevir → metin/OCR çıkar → match engine
```

## 1. Servisler ve portlar (docker-compose.yml)

| Servis | Port | Görev |
|---|---|---|
| `backend` | 8000 | FastAPI uygulaması (Dockerfile: tesseract, libreoffice, poppler) |
| `frontend` | 5173 | nginx + statik Vite build; `/api/` ve `/health`'i backend'e proxy'ler |
| `postgres` | 5433 (host) / 5432 (ağ) | Ana veritabanı, kullanıcı `crewintel` |
| `social-downloader` | 8001 | yt-dlp + ffmpeg indirme servisi |
| `umay-agent` | 5001 | Umay yardımcı servisi |
| `open-webui` | — | Yerel arayüz (opsiyonel) |

Yerel geliştirme: `docker compose up -d` · frontend yeniden kurulumu:
`docker compose build frontend && docker compose up -d frontend`.

## 2. Backend (`backend/app/`)

```
app/
├── main.py            # FastAPI app, router montajı, CORS, health
├── api/routes/        # 20+ router: auth, crew, ships, contracts, documents,
│                      #   jobs, portal, ai, expiration, dashboard, messages,
│                      #   notifications, audit_logs, settings, social_downloader …
├── services/          # İş mantığı
│   ├── document_service.py     # validate_upload (18 uzantı + magic-byte,
│   │                           #   100MB limit, yanlış adlandırılmış geçerli
│   │                           #   dosyada uzantı düzeltme), store_document_file
│   │                           #   (her belge PDF'e çevrilip PDF saklanır),
│   │                           #   upload_documents / stage_batch_upload (BATCH_REGISTRY)
│   ├── document_processing.py  # extract_text (PDF/DOCX/XLSX/DOC/XLS/RTF + OCR),
│   │                           #   convert_to_pdf (LibreOffice/Pillow/fpdf2),
│   │                           #   extract_name + FILENAME_NOISE/NAME_NOISE, NUL temizliği
│   └── match_engine.py         # Aday bulma + puanlama + karar (bkz. §4)
├── models/            # SQLAlchemy: users, ships, crew_members,
│                      #   ship_crew_assignments, contracts, documents,
│                      #   document_matches, audit_logs, jobs, messages …
├── schemas/           # Pydantic DTO'lar
├── core/config.py     # Ayarlar (max_upload_size_mb=100, storage_path, CORS …)
├── db/                # engine, SessionLocal, init_db, seed
└── ../alembic/        # Şema migration'ları (elle ALTER yok)
```

**Kimlik doğrulama:** JWT (access + refresh), roller `admin/manager/hr/operator/viewer`;
`require_roles(...)`, `require_staff_read` bağımlılıkları route'larda.

## 3. Belge yükleme hattı (kritik yol)

1. **İstemci** (`frontend/src/App.jsx`): `addStagedFiles` 18 uzantıya izin verir,
   reddedileni kırmızı mesajla gösterir; `📁 Klasör Seç` (`webkitdirectory`) ve
   sürükle-bırak `webkitGetAsEntry` ile **içiçe klasörleri recursive** toplar.
2. **Doğrulama** (`validate_upload`): 100MB limit → uzantı izin listesi →
   magic-byte (OLE2/ZIP/JPEG/PNG/PDF imzaları) → içerik başka geçerli bir
   formattaysa **uzantı düzeltilir** (JPEG içeriği `.pdf` adıyla gelirse
   `*.jpg` olarak kaydedilir), hiçbir formata uymuyorsa 415.
3. **Depolama** (`store_document_file`): PDF olmayan her belge yerinde PDF'e
   çevrilir (`convert_to_pdf`: ofis→LibreOffice headless, resim→Pillow A4,
   txt→fpdf2 + Türkçe font); checksum **orijinalden** hesaplanır.
4. **Metin çıkarımı** (`extract_text`): PDF metin katmanı, DOCX (paragraf+tablo),
   XLSX (tüm hücre), eski DOC/XLS/RTF→LibreOffice, **resim OCR** (tesseract
   eng+tur) ve **taramalı PDF** (pdf2image + tesseract). Çıktıdaki `NUL` byte'ları
   temizlenir (PostgreSQL `text fields cannot contain NUL` 500 hatasını önler).
5. **Eşleştirme** → §4.
6. **Uçlar** (`api/routes/documents.py`): `POST /upload`, `POST /batch`,
   `GET /batch/{id}`, `POST /convert` (tek→PDF, çoklu→ZIP), `GET /{id}/file`,
   `GET /{id}/candidates`, `PUT /{id}/match`, `POST /{id}/approve|reject`.

Limitlar **her yerde aynı** olmalı (100MB): `document_service.MAX_UPLOAD_SIZE`,
`core/config.max_upload_size_mb`, `docker-compose MAX_UPLOAD_SIZE_MB`,
`.env.example` ×2, `installer/setup.ps1`, `frontend/nginx.conf client_max_body_size`.

## 4. Eşleştirme motoru (`services/match_engine.py`)

```
extract_name(filename, text) ─┐
EntityExtractor (passport/seaman/email/dob/phone/national_id …) ─┼─> CrewCandidateFinder
normalize(text) (kelime sınırı aralı) ─┘        │   1) güçlü identifier sorguları
                                                 │   2) tam ad / 3) fuzzy ad (0.72)
                                                 │   4) dosya adı kapsama (≥%50 token)
                                                 │   5) metinde tam ad / ad+soyad ayrı
                                                 v
                                    MatchScorer → MatchDecisionEngine → DocumentMatch
```

| Sinyal | Puan | Not |
|---|---|---|
| `passport_exact` / `seaman_book_exact` / `national_id_exact` | 100 | güçlü identifier |
| `crew_id_exact` | 95 | |
| `email_exact` | 90 | |
| `name_exact` | 90 | tek başına auto-match |
| `text_name` | 90 | **belge gövdesinde tam ad** (kelime sınırı; ters sıra kabul) |
| `name_normalized` | 65 | TR karakter normalizasyonu |
| `text_name_parts` | 45 | ad/soyad metinde ayrı ayrı → inceleme |
| `filename_full` | 50 | crew token'larının ≥%50'si dosya adında |
| `dob_exact` 50 · `filename_name` 25 · `phone_exact` 40 · `name_fuzzy` 15 | | |

Karar: **AUTO_MATCH ≥90 ve 2. adaydan ≥15 marj** → `matched`;
**≥35** → `review_required`; çelişkide skor 60'a kısılır (asla auto-match yok);
`DocumentMatch` kaydı + `audit_logs` yazılır. `dry_run=True` DB'ye yazmaz.

Gerçek ölçüm (GERMAN SKY, 187 belge, 22 personel): **58 eşleşen / 25 inceleme /
104 eşleşmeyen**; eşleşmeyenlerin %99'unda listedeki personellerden hiçbiri
anılmıyor (roster dışı) — motor değil, veri sınırı.

## 5. Frontend (`frontend/`)

- Vite + React; tek sayfa `src/App.jsx` (~5.3k satır) içinde route durumları.
- i18n: `src/i18n/locales/{tr,en,ru,ar}.ts` — yeni metin **dört dosyaya** eklenmeli.
- Derleme: `npm run lint` (oxlint), `npm run build`; deploy = frontend image build.

## 6. Diğer parçalar

- `mobile-app/` — Android istemci (`com.crewintel.mobile`), APK `mobile-app/app/build/outputs`.
- `social-downloader/` — yt-dlp + ffmpeg servisi (port 8001).
- `installer/` — Windows kurulumu (`setup.ps1`), `.env` şablonu üretir.
- `tests/` — 17 test dosyası; **284 passed / 2 skipped** (`backend/.venv/Scripts/python -m pytest tests/ -q`, sqlite in-memory).
- `docs/` — `DEVELOPMENT_LOG.md` (ana bellek + CHANGELOG), `DUZELTME_LISTESI_UPLOAD.md`
  (H1–H14 hata listesi), `system-tree/` (modül bazlı detay), `ROADMAP/`.

## 7. Veri ve çalışma durumu (2026-10-06)

- Deneme verileri silindi; GERMAN SKY gerçek verisi: **1 gemi (MV GERMAN SKY),
  22 personel, 190 belge** (ck arşivi 221 dosyanın 3 limit/uyuşmazlık hariç tamamı).
- Backend/healthy, frontend/healthy, `pytest 284 passed`, `oxlint 0 hata`.

## 8. Güvenlik çizgileri

- `.env` / `storage/` / `*.db` / `.freebuff/` gitignore'dadır; gerçek parolalar
  repoya girmez, yalnızca `.env.example` izlenir.
- Migration'lar yalnızca Alembic ile; şema elle değiştirilmez.
- Yükleme her zaman sunucuda yeniden doğrulanır (istemciye güvenilmez).
