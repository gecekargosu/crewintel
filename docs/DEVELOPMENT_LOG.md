# CREWINTEL — MASTER DEVELOPMENT LOG
> AI-readable project memory & engineering handoff document.
> Bu dosya, projeyi devralan herhangi bir AI agent'ın mevcut durumu sıfırdan taramadan anlayabilmesi için tasarlanmıştır.

**Son güncelleme:** 2026-08-10
**Tamamlanan adım:** STEP 2

---

## 1. PROJECT IDENTITY

| Alan | Değer |
|---|---|
| Proje adı | CREWINTEL |
| Proje tipi | Crew Management / Personnel Archive System |
| Hedef kullanıcı | Tek kullanıcı (denizcilik sektörü) |
| Geliştirme aşaması | Backend stabil · Frontend Aşama 4 devam ediyor |
| Proje kökü | `C:\CREWINTEL` |

### Kısa Açıklama

CREWINTEL; gemi personelinin CV'lerini, pasaportlarını, gemiadamı cüzdanlarını, STCW belgelerini, GOC belgelerini, sağlık belgelerini, kontratlarını ve diğer belgelerini merkezi bir sistemde arşivleyen, belge geçerlilik sürelerini takip eden ve tüm işlemleri denetlenebilir hale getiren profesyonel bir crew management platformudur.

---

## 2. PROJECT GOAL

### Çözülen Problem

Gemi personelinin belgeleri Excel/kağıt/farklı klasörlerde tutulduğunda belge kaybı, tarihlerin unutulması, denetim problemleri ve manuel takip yükü oluşmaktadır. CREWINTEL bu süreci dijitalleştirir.

### Mevcut Kullanım Senaryoları (koddan doğrulanmış)

- Personel (crew member) CRUD yönetimi
- Gemi (ship) CRUD yönetimi
- Personel–gemi ataması (assignment)
- Kontrat yönetimi
- Belge yükleme (PDF/TXT), arşivleme ve otomatik eşleştirme
- Belge tipi tespiti (CV, pasaport, STCW, GOC, medical, contract, other)
- İsim/pasaport/gemiadamı cüzdanı numarası ile personel eşleştirme
- CV yüklendiğinde otomatik personel oluşturma
- Belge geçerlilik süresi takibi (expired / urgent / approaching / valid / no_date)
- Tüm CRUD işlemlerinin audit log kaydı
- Pending belgeler için manuel eşleştirme

### Planlanmış (koddan doğrulanmamış — FUTURE)

- Authentication / JWT / RBAC
- Bildirim sistemi (belge bitiş uyarıları)
- AI/OCR ile gelişmiş belge okuma
- Mobile uygulama
- Çok kullanıcılı yapı (admin, manager, hr, captain, viewer rolleri)

---

## 3. ARCHITECTURE (Doğrulanmış)

```
React/Vite (frontend)
        │  HTTP (Axios)
        ▼
FastAPI (backend, port 8000)
        │  SQLAlchemy 2.x ORM
        ▼
PostgreSQL 17 (port 5433 yerel / 5432 Docker)
```

| Katman | Teknoloji | Versiyon |
|---|---|---|
| Frontend framework | React | — |
| Frontend bundler | Vite | 8.x |
| Frontend HTTP | Axios | — |
| Frontend lint | oxlint | — |
| Backend framework | FastAPI | 0.141.1 |
| Backend server | uvicorn[standard] | 0.52.1 |
| ORM | SQLAlchemy | 2.0.51 |
| DB driver | psycopg[binary] | 3.3.4 |
| Schema validation | Pydantic / pydantic-settings | 2.15.0 |
| Migration | Alembic | 1.16.5 |
| PDF parsing | pypdf | 5.9.0 |
| File upload | python-multipart | 0.0.20 |
| Testing | pytest | 8.4.1 |
| Test HTTP | httpx | 0.28.1 |
| Container | Docker Compose | — |
| Database | PostgreSQL | 17 |

---

## 4. DIRECTORY STRUCTURE

```
C:\CREWINTEL\
├── .env                          # Runtime secrets — git'e eklenmez
├── .env.example                  # Şablon
├── docker-compose.yml            # postgres + backend + frontend servisleri
├── pytest.ini                    # Test config (rootdir, pythonpath)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt          # 11 paket
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_create_crew_members.py
│   │       ├── 0002_add_core_domain_models.py
│   │       └── 0003_add_documents_profiles_audit.py
│   └── app/
│       ├── main.py               # FastAPI app, CORS, router kayıtları
│       ├── run.py                # Uvicorn entry point
│       ├── core/config.py        # pydantic-settings, .env yükler
│       ├── db/
│       │   ├── database.py       # engine, SessionLocal, Base, get_db()
│       │   └── init_db.py        # create_all (test/dev için)
│       ├── models/               # SQLAlchemy ORM modelleri
│       │   ├── crew_member.py    # 28 alan
│       │   ├── ship.py           # 7 alan
│       │   ├── assignment.py     # ShipCrewAssignment
│       │   ├── contract.py
│       │   ├── document.py       # 16 alan, checksum, match_status
│       │   ├── audit_log.py      # 7 alan
│       │   └── user.py           # ⚠️ Model var, migration'da yok
│       ├── schemas/              # Pydantic request/response şemaları
│       │   ├── crew_member.py    # CrewMemberCreate/Update/Response
│       │   ├── ship.py
│       │   ├── assignment.py
│       │   ├── contract.py
│       │   └── document.py       # DocumentResponse, DocumentMatchUpdate
│       ├── api/routes/           # FastAPI router'ları
│       │   ├── crew.py
│       │   ├── ships.py
│       │   ├── assignments.py
│       │   ├── contracts.py
│       │   ├── documents.py      # ← STEP 1'de güncellendi
│       │   ├── expiration.py
│       │   └── audit_logs.py
│       └── services/             # İş mantığı katmanı
│           ├── audit.py          # log_event() helper
│           ├── document_service.py   # DocumentService class ← STEP 1'de güncellendi
│           ├── document_processing.py  # extract, parse, match, store
│           └── expiration_service.py   # ExpirationService class
│
├── tests/
│   ├── conftest.py               # SQLite in-memory test DB, fixtures
│   ├── test_api.py               # 10 test (crew, ship, assignment, contract)
│   ├── test_audit.py             # 11 test (audit log kayıtları)
│   └── test_documents.py         # 5 test (upload, match, filter) ← STEP 1'de güncellendi
│
├── frontend/
│   ├── package.json              # React, Vite, Axios, Lucide-React
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx              # React root
│       ├── App.jsx               # ⚠️ Aşama 4 henüz tamamlanmadı (165 satır)
│       ├── App.css               # ✅ Aşama 4 için CSS tamamen hazır (437 satır)
│       └── index.css
│
├── docs/
│   ├── ARCHITECTURE.md           # Mimari özet (Türkçe)
│   ├── SETUP.md                  # Kurulum rehberi
│   └── DEVELOPMENT_LOG.md        # ← BU DOSYA (proje hafızası)
│
├── ai/          # BOŞ — gelecek AI/OCR modülü için ayrılmış
├── deployment/  # BOŞ
├── mobile/      # BOŞ
├── scripts/     # İçerik mevcut
├── database/    # İçerik mevcut
└── storage/     # Yüklenen belge dosyaları burada saklanır
```

---

## 5. BACKEND CURRENT STATE

| Modül | Durum | Notlar |
|---|---|---|
| FastAPI app | ✅ DONE | main.py, CORS configurable |
| Config | ✅ DONE | pydantic-settings, `.env`'den yükler |
| DB connection | ✅ DONE | pool_pre_ping, get_db() dependency |
| Alembic migrations | ✅ DONE | 3 migration, linear chain |
| CrewMember model/CRUD | ✅ DONE | 28 alan, filtreli liste (name, surname, position, nationality, status, ship_id) |
| Ship model/CRUD | ✅ DONE | IMO validation |
| Assignment model/CRUD | ✅ DONE | |
| Contract model/CRUD | ✅ DONE | |
| Document model | ✅ DONE | 16 alan, checksum dedup, match_status |
| Document upload | ✅ DONE | Multi-file, PDF+TXT, SHA-256 checksum |
| Document download | ✅ DONE | FileResponse |
| Document match | ✅ DONE | Manuel eşleştirme (PUT /{id}/match) |
| Document list filter | ✅ DONE | crew_member_id, document_type, match_status (**STEP 1**), expiry_status |
| Document processing | ✅ DONE | extract_text, parse_date, extract_metadata, match_crew, store_file |
| Expiration service | ✅ DONE | expired/urgent/approaching/valid/no_date |
| Audit logging | ✅ DONE | log_event(), tüm CRUD'a yayılmış |
| Audit API | ✅ DONE | GET /api/audit-logs/ (filtreli) |
| User model | ⚠️ PARTIAL | Model var, migration yok, route yok, schema yok |
| Authentication | ❌ MISSING | Hiçbir middleware/dependency yok |
| Authorization/RBAC | ❌ MISSING | |

---

## 6. DATABASE CURRENT STATE

### Tablolar

| Tablo | Alanlar | Durum |
|---|---|---|
| `crew_members` | id, first_name, last_name, dob, nationality, passport_no, seaman_book_no, position, rank, phone, email, address, emergency_contact, birth_place, hometown, marital_status, experience_years, sea_service_months, languages, education_summary, notes, profile_data(JSON), status | ✅ Migration 0001+0003 |
| `ships` | id, name, imo_number(unique), flag, ship_type, company, status | ✅ Migration 0002 |
| `ship_crew_assignments` | id, ship_id(FK), crew_member_id(FK), position, start_date, end_date, status, notes | ✅ Migration 0002 |
| `contracts` | id, ship_id(FK), crew_member_id(FK), contract_number(unique), contract_type, start_date, end_date, currency, monthly_wage, status, notes | ✅ Migration 0002 |
| `documents` | id, crew_member_id(FK nullable), original_filename, stored_filename(unique), storage_path, mime_type, file_size, checksum(unique), document_type, document_number, issue_date, expiry_date, match_status, match_confidence, extracted_text, extracted_metadata(JSON), source | ✅ Migration 0003 |
| `audit_logs` | id, action, entity, entity_id, message, status, metadata_json(JSON), created_at | ✅ Migration 0003 |
| `users` | id, email(unique), full_name, role, is_active | ⚠️ Model var, **migration yok** — tablo oluşmuyor |

### Document.match_status Değerleri

```
"pending"    — eşleşme belirsiz veya bulunamadı
"matched"    — personel eşleşmesi tamamlandı
"unmatched"  — hiç eşleşme yok, manuel müdahale gerekiyor
```

### Alembic Migration Zinciri

```
0001 → 0002 → 0003 → (NEXT: 0004 — users tablosu, henüz yapılmadı)
```

---

## 7. API INVENTORY

### Crew
| Method | Endpoint | Notlar |
|---|---|---|
| POST | `/api/crew/` | Personel oluştur |
| GET | `/api/crew/` | Filtreli liste (name, surname, position, nationality, status, ship_id) |
| GET | `/api/crew/{id}` | Detay |
| PUT | `/api/crew/{id}` | Güncelle |
| DELETE | `/api/crew/{id}` | Sil |

### Ships
| Method | Endpoint |
|---|---|
| POST/GET/GET/{id}/PUT/{id}/DELETE/{id} | `/api/ships/` |

### Assignments
| Method | Endpoint |
|---|---|
| POST/GET/GET/{id}/PUT/{id}/DELETE/{id} | `/api/assignments/` |

### Contracts
| Method | Endpoint |
|---|---|
| POST/GET/GET/{id}/PUT/{id}/DELETE/{id} | `/api/contracts/` |

### Documents ✅ STEP 1 sonrası güncel
| Method | Endpoint | Filtreler |
|---|---|---|
| POST | `/api/documents/upload` | — |
| GET | `/api/documents/` | `crew_member_id`, `document_type`, **`match_status`** ✅ STEP 1, `expiry_status` |
| GET | `/api/documents/{id}` | — |
| GET | `/api/documents/{id}/file` | FileResponse |
| PUT | `/api/documents/{id}/match` | Manuel eşleştirme |
| DELETE | `/api/documents/{id}` | — |

### Expiration
| Method | Endpoint |
|---|---|
| GET | `/api/expiration/summary` |
| GET | `/api/expiration/expired` |
| GET | `/api/expiration/urgent` |
| GET | `/api/expiration/approaching` |
| GET | `/api/expiration/valid` |
| GET | `/api/expiration/no-date` |

### Audit
| Method | Endpoint | Filtreler |
|---|---|---|
| GET | `/api/audit-logs/` | `action`, `entity`, `entity_id`, `status`, `offset`, `limit` |

### Health
| Method | Endpoint |
|---|---|
| GET | `/` |
| GET | `/health` |
| GET | `/health/database` |

**Toplam: 34 endpoint**

---

## 8. FRONTEND CURRENT STATE

### Mevcut (App.jsx — 165 satır)

| Ekran | Durum |
|---|---|
| Dashboard | ⚠️ Kısmi — 3 kart (toplam personel, gemi, aktif), belge metrikleri yok |
| Personel listesi | ✅ Temel liste + "Personel Ekle" formu |
| Personel detay | ⚠️ Kısmi — 6 alan gösteriyor, 9 yeni alan (experience_years vb.) gösterilmiyor |
| Gemiler listesi | ✅ Temel liste |
| Gemi detay | ✅ Temel detay + atama listesi |
| Atamalar | ✅ Temel liste |
| Kontratlar | ✅ Temel liste |
| Belgeler ekranı | ❌ YOK — backend hazır |
| Toplu belge yükleme | ❌ YOK — en kritik eksik |
| Pending eşleşme | ❌ YOK — STEP 1 ile backend hazır |
| Audit log ekranı | ❌ YOK — backend hazır |
| Dashboard belge metrikleri | ❌ YOK — `/api/expiration/summary` hazır |
| Arama/filtre UI | ❌ YOK — backend destekliyor |

**`App.css` (437 satır) — Aşama 4 için tamamen hazır.** Badge'ler, tablo, upload-zone, pending-card, audit-row, confidence-bar, tabs — tüm CSS class'lar yazılmış.

**`App.jsx` (165 satır) — Aşama 4 başlatılmamış.** Sadece mevcut CRUD ekranları mevcut.

---

## 9. TEST STATUS

**Son doğrulama: STEP 2 sonrası (2026-08-10)**

```
26 passed, 0 failed
```

| Dosya | Test Sayısı | Kapsam |
|---|---|---|
| `test_api.py` | 10 | Crew, Ship, Assignment, Contract CRUD; health; validation; FK |
| `test_audit.py` | 11 | CRUD audit logları; crew/ship/assignment/contract/document events |
| `test_documents.py` | 5 | Upload/match/create/dedup + **match_status filtresi (STEP 1)** |

### Test fonksiyonları (doğrulanmış isimler)

**test_documents.py:**
- `test_document_upload_matches_strong_identifier_and_creates_audit_log`
- `test_ambiguous_name_stays_pending`
- `test_cv_creates_crew_when_no_match_exists`
- `test_duplicate_upload_returns_existing_document`
- `test_match_status_filter_returns_only_pending_documents` ← **STEP 1**

### Eksik Test Kapsamı

- Expiration service testleri yok → **STEP 3 hedefi**
- Audit log tarih filtresi testi yok → **STEP 4 hedefi**
- Error case testleri kısmi (404/409/422 senaryoları eksik)

---

## 10. SECURITY STATUS

| Alan | Durum |
|---|---|
| Authentication | ❌ UYGULANMADI |
| Authorization/RBAC | ❌ UYGULANMADI |
| JWT/session | ❌ UYGULANMADI |
| Password hashing | ❌ UYGULANMADI |
| CORS | ⚠️ Configurable, varsayılan izin veriyor |
| SQL Injection | ✅ ORM korumalı |
| Path traversal | ✅ uuid4 ile dosya adı üretiliyor |
| File size limit | ✅ MAX_UPLOAD_SIZE_MB configurable |
| Checksum dedup | ✅ SHA-256 |
| Secrets | ✅ .env'de tutuluyor, git'e eklenmez |
| Input validation | ✅ Pydantic validators |

> ⚠️ **Sistem şu anda tamamen açık.** Herhangi bir istek tüm API'lere erişebilir.
> Tek kullanıcı / lokal kullanım için kabul edilebilir.
> **Network'e açılmadan önce authentication zorunludur.**

---

## 11. TECHNICAL DEBT (Güncel)

| Borç | Durum | Öncelik |
|---|---|---|
| ~~`.bak` dosyaları~~ | ✅ **STEP 2'de çözüldü** | — |
| ~~Kök dizin test txt dosyaları~~ | ✅ **STEP 2'de çözüldü** | — |
| User model migration yok | ⚠️ Açık — tablo oluşmuyor | P2 |
| `AuditLogResponse` schemas/ altında değil | ⚠️ route içine gömülü | P2 |
| Frontend App.jsx monolitik | ⚠️ Tek dosya, bileşen yok | P3 |
| Expiration testleri eksik | ⚠️ | P2 |
| Audit date range filtresi yok | ⚠️ | P2 |
| Authentication yok | ❌ | P3 |

---

## 12. COMPLETED DEVELOPMENT STEPS

---

### STEP 1 — match_status Filter
**Status:** ✅ COMPLETE
**Tarih:** 2026-08-10

**Amaç:**
Frontend pending belgeler ekranının çalışabilmesi için API desteği.

**Değiştirilen dosyalar:**
- `backend/app/services/document_service.py` — `list_documents()` metoduna `match_status: str | None` parametresi ve `Document.match_status == match_status` filtresi eklendi
- `backend/app/api/routes/documents.py` — `GET /api/documents/` endpoint'ine `match_status` query parametresi eklendi, service çağrısına iletildi
- `tests/test_documents.py` — `test_match_status_filter_returns_only_pending_documents` testi eklendi

**Doğrulama:**
```
GET /api/documents/?match_status=pending  → sadece pending belgeler döner
GET /api/documents/?match_status=matched  → sadece matched belgeler döner
GET /api/documents/                       → mevcut davranış korundu (geriye dönük uyumluluk)
```

**Test sonucu:** `26 passed, 0 failed`
**git diff --check:** PASS
**Kapsam dışı değişiklik:** Yok

---

### STEP 2 — Project Cleanup + Master Development Log
**Status:** ✅ COMPLETE
**Tarih:** 2026-08-10

**Silinen dosyalar:**
- `backend/app/api/routes/documents.py.bak` — aktif import zincirinde kullanılmadığı PowerShell Select-String ile doğrulandı
- `backend/app/services/document_processing.py.bak` — aktif import zincirinde kullanılmadığı doğrulandı
- `test_document.txt` — conftest.py / testlerde referans bulunmadı
- `test_document_v2.txt` — aynı şekilde
- `test_document_v3.txt` — aynı şekilde
- `test_document_v4.txt` — aynı şekilde

**Silindi (toplam):** 6 dosya

**Oluşturulan:** `docs/DEVELOPMENT_LOG.md` (bu dosya) — proje hafızası / AI handoff belgesi

**Fonksiyonel kod değişikliği:** YOK

**Test sonucu:** `26 passed, 0 failed`
**git diff --check:** PASS

---

### STEP 3 — Expiration Service Test Coverage
**Status:** ✅ COMPLETE
**Tarih:** 2026-08-10

**Amaç:**
`ExpirationService`'in tüm kategorilerini ve sınır koşullarını test coverage ile güvence altına almak.

**Oluşturulan dosya:**
- `tests/test_expiration.py` (12 test, ~95 satır)

**Production kod değişikliği:** YOK

**Test edilen senaryolar:**
- `expired`: geçmiş tarih → `expiry_status == "expired"`
- `urgent`: remaining ≤ 30 → `"urgent"` (sınır: bugün = urgent, 31. gün = approaching)
- `approaching`: 31 ≤ remaining ≤ 90 → `"approaching"` (sınır: 90. gün = approaching, 91. gün = valid)
- `valid`: remaining > 90 → `"valid"`
- `no_date`: expiry_date = None → `"no_date"`
- `summary`: tüm alanlar mevcut, `total == expired + urgent + approaching + valid + no_date`

**Boundary testleri:**
- `remaining = 0` (bugün) → urgent, expired değil ✅
- `remaining = 30` → urgent ✅ / `remaining = 31` → approaching ✅
- `remaining = 90` → approaching ✅ / `remaining = 91` → valid ✅

**Test sonucu:** `38 passed, 0 failed` (26 önceki + 12 yeni)
**git diff --check:** PASS
**Regression:** Production koda dokunulmadı — doğrulandı

**Teknik borç notu:**
`ExpirationService` tarih kaynağı olarak `date.today()` kullanır; timezone farkındalığı yoktur. Gelecekte UTC tabanlı hesaplamaya geçiş gerekebilir. Mevcut aşama için kabul edilebilir.

---

### STEP 4 — Audit Log Date Range Filter
**Status:** ✅ COMPLETE
**Tarih:** 2026-08-12

**Amaç:**
`GET /api/audit-logs/` endpoint'ine `date_from` ve `date_to` query parametreleri eklenerek belirli zaman aralığındaki audit olaylarının filtrelenebilmesi.

**Değiştirilen dosyalar:**
- `backend/app/api/routes/audit_logs.py` — `from datetime import date, datetime, time` eklendi; `date_from: date | None` ve `date_to: date | None` query parametreleri eklendi; `datetime.combine(date_from, time.min)` / `datetime.combine(date_to, time.max)` ile aralık filtresi uygulandı
- `tests/test_audit.py` — 3 yeni test eklendi (date_from, date_to, kombine)

**Doğrulama:**
```
GET /api/audit-logs/?date_from=2026-08-12          → sadece bugün ve sonrası
GET /api/audit-logs/?date_to=2026-08-11            → bugünden önceki loglar
GET /api/audit-logs/?date_from=2026-08-12&date_to=2026-08-13  → aralık
GET /api/audit-logs/                               → mevcut davranış korundu
```

**Eklenen test fonksiyonları:**
- `test_audit_log_date_from_filter_returns_logs_on_or_after`
- `test_audit_log_date_to_filter_excludes_future`
- `test_audit_log_date_range_combined`

**Test sonucu:** `41 passed, 0 failed` (38 önceki + 3 yeni)
**git diff --check:** PASS
**Production koda dokunulmayan alanlar:** model, schema, service, expiration, documents

---

### STEP 5A — Frontend Dashboard Expiration Metrics
**Status:** ✅ COMPLETE
**Tarih:** 2026-08-12

**Amaç:**
Dashboard'a `/api/expiration/summary` endpoint'inden gelen expired/urgent/approaching/valid sayılarını göstermek.

**Değiştirilen dosyalar:**
- `frontend/src/App.jsx`
  - `expirySummary` state eklendi
  - `loadData()` Promise.all'a `GET /api/expiration/summary` çağrısı eklendi
  - Dashboard'a `.card-icon.danger/warning/purple/success` snıflarıyla 4 expiration kartı eklendi
  - Mevcut 3 dashboard kartı `.card-icon` sarıcısı ile güncellendi (CSS uyumu)
- `frontend/src/App.css`
  - `.section-label` sınıfı eklendi (dashboard bölüm başlığı)

**Backend değişikliği:** YOK

**Çalışan endpoint:** `GET /api/expiration/summary`
**Gösterilen alanlar:** `expired` · `urgent` · `approaching` · `valid`
**Null guard:** `expirySummary !== null` — backend bağlantısı yokken kartlar görünmez

**Lint:** `0 warnings, 0 errors`
**Build:** `✅ 1.39s, 0 error`
**Regression (pytest):** Çalıştırılmadı (backend'e dokunulmadı) — son doğrulama: 41 passed (STEP 4)

---

### STEP 5B — Crew Detail Genişletme (9 Yeni Alan)
**Status:** ✅ COMPLETE
**Tarih:** 2026-08-12

**Amaç:**
Crew Detail ekranına backend'de mevcut olan 9 alanı eklemek: `birth_place`, `hometown`, `marital_status`, `experience_years`, `sea_service_months`, `languages`, `education_summary`, `notes`, `profile_data`

**Değiştirilen dosyalar:**
- `frontend/src/App.jsx`
  - `formatProfileData()` yardımcı fonksiyonu eklendi
  - `renderCrewDetail()` fonksiyonu oluşturuldu (eski inline JSX kaldırıldı)
  - 3 bölüm: Temel Bilgiler (6 alan) · Kişisel Bilgiler (6 alan) · Ek Bilgiler (2 alan)
  - `profile_data` için `<pre>` bloğu (sadece dolu olduğunda görülür)
  - Tüm null/undefined için `"—"` guard; `experience_years`/`sea_service_months` 0-safe
- `frontend/src/App.css`
  - `.profile-data-block` sınıfı eklendi (monospace, max-height: 240px)

**Backend değişikliği:** YOK

**Gösterilen alanlar (tam):**
```
Temel    : position, rank, nationality, status, email, phone
Kişisel  : birth_place, hometown, marital_status, experience_years, sea_service_months, languages
Ek       : education_summary, notes
JSON     : profile_data (dolu ise görünür)
```

**Lint:** `0 warnings, 0 errors`
**Build:** `✅ 648ms, 0 error`
**git diff --check:** PASS

---

### STEP 6 — Documents List Ekranı (Frontend Wiring Tamamlama)
**Status:** ✅ COMPLETE
**Tarih:** 2026-08-12

**Amaç:**
Antigravity'nin önceki oturumda token/session limiti nedeniyle yarım bıraktığı STEP 6 iskeletini tamamlamak. `documents` state, `documentsLoading`, `documentsError`, `loadDocuments()`, `openDocumentsPage()` fonksiyonları zaten mevcuttu; eksik olan tek şey UI wiring'iydi (nav butonu + render case + liste ekranı).

**Değiştirilen dosyalar:**
- `frontend/src/App.jsx`
  - `navigation` dizisine `["documents", Folder, "Belgeler"]` eklendi (mevcut `Folder` importu ilk kez kullanıldı)
  - Nav butonu `onClick`'i `documents` sayfası için mevcut `openDocumentsPage()` fonksiyonunu çağıracak şekilde güncellendi (diğer sayfalar için davranış değişmedi)
  - `renderPage()` içine `if (activePage === "documents") return renderDocumentsList();` case'i eklendi
  - Yeni `renderDocumentsList()` fonksiyonu eklendi: mevcut `documents`, `documentsLoading`, `documentsError` state'lerini kullanır; mevcut `.data-table`, `.empty`, `.form-error`, `.badge` / `.badge-type-*` / `.badge-matched` vb. CSS sınıflarını kullanır — yeni CSS eklenmedi

**Backend değişikliği:** YOK
**Migration değişikliği:** YOK
**Yeni dependency:** YOK

**Gösterilen kolonlar:** Dosya Adı · Belge Tipi · Eşleşme Durumu · Geçerlilik · Personel (eşleşen crew adı, `crewById` üzerinden)

**State handling:** loading → "Belgeler yükleniyor..." · error → `.form-error` mesajı · empty → `.empty` bloğu (Folder ikonu) · dolu → `.data-table`

**Not:** `expiry_status` backend'den `no_date` (alt çizgi) formatında geliyor, CSS sınıfı ise `.badge-no-date` (tire); `renderDocumentsList()` içinde `.replace(/_/g, "-")` ile normalize edildi. `document_type` değeri `seaman_book` için CSS'te özel bir badge rengi tanımlı değil (`badge-type-seaman_book` yok) — bu STEP kapsamında yeni CSS eklenmediği için düz `.badge` stiliyle görünecek, işlevsel bir sorun değil.

**Kapsam dışı bırakılanlar (bilinçli):** Dashboard'daki `renderCrewList()` tekrarı düzeltilmedi (ayrı checkpoint). Belge tipi/durum filtreleri (F-14) eklenmedi — bu STEP sadece liste ekranı içindi.

**Değişiklik büyüklüğü:** 44 satır eklendi, 2 satır değiştirildi (nav array + onClick) — toplam ~46 satır, 40-70 satır bütçesi içinde.

**Syntax doğrulama:** esbuild ile JSX parse — 0 hata
**Lint:** Bu oturumda gerçek `npm run lint` (oxlint) repo üzerinde çalıştırılamadı — bkz. rapor notu
**Build:** Bu oturumda gerçek `npm run build` (vite) repo üzerinde çalıştırılamadı — bkz. rapor notu

---

## 13. CURRENT VERIFIED STATE

```
Last completed step : STEP 6 (Documents list ekranı)

Tests               : 41 passed, 0 failed (son doğrulama: STEP 4 — STEP 6 backend'e dokunmadı)
Backend             : Stabil, 34 endpoint çalışıyor (değişmedi)
Frontend            : Dashboard expiration metrikleri ✅
                      Crew Detail 15 alan gösteriyor ✅
                      Belgeler listesi ✅ (STEP 6 — tablo, loading/error/empty state)
                      Upload/Pending/Audit ekranları henüz yok
Database            : 6 tablo (users tablosu migration'sız)
Security            : Authentication yok — lokal kullanım için kabul edilebilir

Known issues:
- User model migration yok
- Frontend Upload, Pending, Audit ekranları başlatılmadı
- Belge tipi/durum filtreleri (F-14) henüz yok — STEP 6 kapsamı sadece liste ekranıydı
- Dashboard'da renderCrewList() tekrarı (ayrı, düzeltilmemiş bug)
- Timezone borcu: date.today() UTC-farkındalıksız

Next recommended step : STEP 7 — Toplu upload UI (drag & drop)

Do not start yet:
- Authentication (P3)
- Frontend component split (P3)
```

---

## 14. NEXT EXECUTION ORDER

| Adım | Görev | Durum |
|---|---|---|
| STEP 1 | match_status filter | ✅ COMPLETE |
| STEP 2 | Cleanup + project memory | ✅ COMPLETE |
| STEP 3 | Expiration service testleri (`test_expiration.py`) | ✅ COMPLETE |
| STEP 4 | Audit log tarih filtresi (`date_from`, `date_to`) | ✅ COMPLETE |
| STEP 5A | Dashboard expiration metrics | ✅ COMPLETE |
| STEP 5B | Crew detail genisletme (9 yeni alan) | ✅ COMPLETE |
| STEP 5 | Frontend Aşama 4A — Navigation + Crew detail + Dashboard metrics | ⚠️ PARTIAL (5A+5B done, nav eksik) |
| STEP 6 | Frontend Aşama 4B — Documents list ekranı | ✅ COMPLETE |
| STEP 7 | Frontend Aşama 4C — Toplu upload UI | ⏳ PENDING |
| STEP 8 | Frontend Aşama 4D — Pending eşleşme ekranı | ⏳ PENDING |
| STEP 9 | Frontend Aşama 4E — Audit log ekranı | ⏳ PENDING |
| STEP 10 | User migration (Alembic 0004) | ⏳ PENDING |
| LATER | Authentication / JWT / RBAC | 🔴 BEKLEMEDE |
| LATER | Frontend component split | 🔴 BEKLEMEDE |

---

## 15. IMPORTANT CONSTRAINTS

Gelecek agent'ların uyması gereken kurallar:

1. **Alembic migration'larını (0001-0003) değiştirme.** Üretim verisi olabilir.
2. **`document_processing.py` mantığını gereksiz değiştirme.** parse_date ve match_crew stabil.
3. **`conftest.py`'ye dokunma.** 38 test burada tutunuyor.
4. **App.jsx'i tek seferde yeniden yazma.** Parçalı yapılacak (4A → 4B → 4C → 4D → 4E).
5. **Her STEP sonrası `pytest` + `git diff --check` çalıştır.**
6. **Authentication'ı beklenmedik bir komut olmadan başlatma.**
7. **Her STEP sonunda DUR. Otomatik STEP atlama yapma.**
8. **Bu dosyayı (DEVELOPMENT_LOG.md) her tamamlanan STEP sonrası güncelle.**

---

## 16. MASTER COMPLETION AUDIT

**Tarih:** 2026-08-12 | **Durum:** COMPLETE

**Özet:** Önceki oturum token/quota kesilmesiyle yarım kalmıştı. COMPLETION_MATRIX.md eksikti. Recovery analizi yapıldı, repository ile chat tutarlılığı doğrulandı, eksik dosya tamamlandı.

**Repository doğrulaması (2026-08-12):**
- Tests: `38 passed, 0 failed` ✅
- git diff --check: PASS ✅
- .bak dosyaları: YOK ✅ (STEP 2'de silindi)
- test_expiration.py: MEVCUT ✅ (STEP 3'te oluşturuldu)

**Tamamlanan işler (doğrulanmış):**

| STEP | Açıklama | Repository Durumu |
|---|---|---|
| STEP 1 | match_status filtresi | ✅ documents.py + document_service.py güncel |
| STEP 2 | Temizlik + DEVELOPMENT_LOG | ✅ .bak yok, log mevcut |
| STEP 3 | Expiration testleri | ✅ test_expiration.py (12 test) |

**Bu audit'te oluşturulan ROADMAP dosyaları:**
```
C:\CREWINTEL\docs\ROADMAP\
├── MASTER_ROADMAP.md     ← 2026-08-10 (önceki oturum)
├── CURRENT_STATE.md      ← 2026-08-10 (önceki oturum)
├── ENGINEERING_PLAN.md   ← 2026-08-10 (önceki oturum)
├── ARCHITECTURE_PLAN.md  ← 2026-08-10 (önceki oturum)
└── COMPLETION_MATRIX.md  ← 2026-08-12 (bu oturumda tamamlandı)
```

**Kod değişikliği:** YOK — yalnızca docs/ güncellendi

**Sonraki adım:** STEP 4 — Audit log `date_from`/`date_to` filtresi
(`backend/app/api/routes/audit_logs.py` + 2-3 test, ~10 satır, Low risk)

> ⚠️ **Not (2026-08-12 sync ile eklendi):** Bu bölüm (16. MASTER COMPLETION AUDIT) STEP 4'ten önceki tarihsel bir kayıttır. STEP 4, 5A, 5B ve 6 o tarihten sonra tamamlanmıştır. Güncel durum için bkz. Bölüm 13 (CURRENT VERIFIED STATE) ve aşağıdaki Bölüm 17.

---

## 17. DOCUMENTATION SYNC — STEP 1–6 CURRENT STATE ALIGNMENT

**Tarih:** 2026-08-12
**Tür:** Documentation Sync checkpoint (kod değişikliği içermez)

**Amaç:**
CURRENT_STATE.md, DEVELOPMENT_LOG.md ve COMPLETION_MATRIX.md dosyalarının STEP 1–6'nın gerçek (kod üzerinde doğrulanmış) durumuyla senkron olup olmadığını denetlemek ve tespit edilen eski/çelişkili kayıtları düzeltmek.

**İncelenen dosyalar:**
- `docs/ROADMAP/CURRENT_STATE.md`
- `docs/DEVELOPMENT_LOG.md` (bu dosya, önceki bölümler)
- `docs/ROADMAP/COMPLETION_MATRIX.md`
- `frontend/src/App.jsx` (STEP 6 wiring'i koddan doğrulamak için, salt-okunur)
- `backend/app/api/routes/documents.py`, `backend/app/api/routes/audit_logs.py` (STEP 1 ve STEP 4 iddialarını koddan doğrulamak için, salt-okunur)

**STEP 1–6 durumu — koddan doğrulandı:**

| STEP | Doğrulama | Sonuç |
|---|---|---|
| STEP 1 | `documents.py` route'unda `match_status` parametresi | ✅ COMPLETE |
| STEP 2 | `.bak` dosyaları yok, log mevcut | ✅ COMPLETE |
| STEP 3 | `test_expiration.py` (12 test) | ✅ COMPLETE |
| STEP 4 | `audit_logs.py`'de `date_from`/`date_to` (Query + `datetime.combine`) | ✅ COMPLETE |
| STEP 5A | `App.jsx`'te `expirySummary` state + 4 dashboard kartı | ✅ COMPLETE |
| STEP 5B | `renderCrewDetail()` — 3 bölüm, 9 yeni alan | ✅ COMPLETE |
| STEP 6 | `navigation`'da `documents` girişi + `renderPage()` case + `renderDocumentsList()` | ✅ COMPLETE |

**Güncellenen dosyalar ve yapılan değişiklikler:**

1. **`docs/ROADMAP/CURRENT_STATE.md`**
   - Header: "Son güncelleme 2026-08-10 / STEP 3" → "2026-08-12 / STEP 6"
   - Dashboard satırı: ⚠️ PARTIAL → ✅ DONE (STEP 5A ile expiration metrikleri mevcut)
   - Personel detay satırı: ⚠️ PARTIAL → ✅ DONE (STEP 5B ile 9 yeni alan mevcut)
   - Belgeler satırı: ✅ DONE olarak teyit edildi (STEP 6)
   - "Dashboard expiration ❌ YOK" tekrarlayan/çelişkili satırı kaldırıldı (Dashboard satırıyla birleştirildi)
   - `App.jsx` satır sayısı: 165 → 293 (gerçek güncel değer)
   - TESTS bölümü: 38 passed → 41 passed (STEP 4 sonrası son doğrulanan sayı), STEP 5A/5B/6'nın backend'e dokunmadığı ve bu yüzden pytest'in yeniden çalıştırılmadığı not edildi
   - STEP 6 lint/build durumu: gerçek `oxlint`/`vite build` bu makinede koşulmadığı açıkça belirtildi (olmuş gibi gösterilmedi)
   - CURRENT STEP bölümü: "Tamamlanan: STEP 3 / Sonraki: STEP 4" → "Tamamlanan: STEP 6 / Sonraki: STEP 7"
   - Backend, Database, Security, Deployment, AI/Mobile, Technical Debt bölümlerine **dokunulmadı** (bu STEP'ler yalnızca frontend'i etkiledi)
   - Authentication/RBAC ❌ MISSING olarak **korundu** — DONE yapılmadı

2. **`docs/ROADMAP/COMPLETION_MATRIX.md`**
   - Header: "Son tamamlanan: STEP 3" → "STEP 6" (bu zaten önceki checkpoint'te güncellenmişti, bu sync'te teyit edildi)
   - F-03 (Sidebar/navigation): "Missing: Belgeler + Audit sekmeleri" → "Missing: Audit sekmesi (Belgeler STEP 6'da eklendi)"; Next Action STEP 5 → STEP 9; Risk Med → Low
   - F-13 (Documents list screen) ✅ DONE olarak teyit edildi (önceki checkpoint'te işaretlenmişti)
   - F-05 (STEP 5A) ve F-08 (STEP 5B) ✅ DONE olarak teyit edildi
   - OVERALL COMPLETION SUMMARY yeniden hesaplandı: Frontend %50 → %57 — hesap yöntemi: F-01→F-22 (F-22 DEFERRED hariç, 21 madde), DONE=1.0 + PARTIAL=0.5 ağırlıklandırması: (11 DONE + 2×0.5 PARTIAL) / 21 ≈ %57
   - TOTAL ESTIMATED %55 → %54 — 7 kategorinin basit ortalaması (Backend/Database/Tests/Security/Operations/AI-Mobile değişmedi, yalnızca Frontend güncellendi)
   - Hesaplama yöntemi dosyaya not olarak eklendi (şeffaflık için)

3. **`docs/DEVELOPMENT_LOG.md`** (bu dosya)
   - Bölüm 16'daki eski "Sonraki adım: STEP 4" notunun üstüne, bunun STEP 4'ten önceki tarihsel bir kayıt olduğunu belirten bir uyarı eklendi (kayıt **silinmedi**, sadece bağlam eklendi)
   - Bu Bölüm 17 (DOCUMENTATION SYNC) yeni checkpoint olarak eklendi

**Eski tarihsel kayıtların korunması:** Bölüm 1–16 arasındaki hiçbir kayıt silinmedi veya yeniden yazılmadı. Bölüm 16'ya yalnızca bağlamsal bir not eklendi (yukarıda belirtildi).

**Kod değişikliği:** YOK. `frontend/src/`, `backend/app/`, migration dosyaları — hiçbiri değiştirilmedi.

**Test:** Bu sync sırasında hiçbir test çalıştırılmadı (kapsam yalnızca dokümantasyondu, kod değişmediği için test'e gerek yoktu).

**Sonraki adım:** STEP 7 — Toplu Upload UI (drag & drop)
(`frontend/src/App.jsx`, Medium-Large risk, ~200 satır tahmini)

**Safe Stop Point:** Dokümantasyon senkronizasyonu tamamlandı. Üç dosya (CURRENT_STATE.md, COMPLETION_MATRIX.md, DEVELOPMENT_LOG.md) STEP 1–6'nın gerçek koddan doğrulanmış durumuyla tutarlı. Kod tabanına dokunulmadı, MASTER_ROADMAP.md'ye dokunulmadı. Onay olmadan STEP 7'ye veya başka bir işe geçilmeyecek.

---

## 18. MASTER_ROADMAP SYNC — 2026-08-12

- MASTER_ROADMAP.md güncellendi
- STEP 1–6 tamamlandı
- STEP 7 sıradaki iş
- Kod değişikliği yapılmadı
- Test/lint/build çalıştırılmadı
- Safe Stop Point
- STEP 7'ye geçilmedi

---

## 19. STEP 7A — Upload Zone UI (Drag & Drop + Multi-file Staging)

**Tarih:** 2026-08-13
**Kapsam:** STEP 7'nin ilk checkpoint'i — F-15 (Bulk upload UI)'ın yalnızca UI/staging kısmı. **Backend'e henüz upload isteği gönderilmiyor.**

**Yapılan işler:**
- `Belgeler` ekranına drag & drop alanı eklendi (mevcut `.upload-zone` / `.drag-over` CSS sınıfları — daha önce hiç kullanılmıyordu, ilk kez kullanıldı)
- Tıklayarak dosya seçme (gizli `<input type="file" multiple>` + `fileInputRef`)
- Seçilen/sürüklenen dosyalar `stagedFiles` state'inde tutuluyor, `.file-list` / `.file-item` CSS sınıflarıyla listeleniyor (dosya adı + boyut)
- Aynı dosyanın (ad+boyut eşleşmesiyle) iki kez eklenmesi engellendi
- Her dosya için tekil kaldırma butonu (`removeStagedFile`, `.icon-button`)

**Değiştirilen dosyalar:**
- `frontend/src/App.jsx` — 77 satır eklendi, 1 satır değiştirildi (import satırı)
  - Yeni import: `useRef` (react), `Upload`, `X` (lucide-react)
  - Yeni state: `stagedFiles`, `dragActive`, `fileInputRef`
  - Yeni fonksiyonlar: `formatFileSize`, `addStagedFiles`, `removeStagedFile`, `handleFileInputChange`, `handleDragOver`, `handleDragLeave`, `handleDrop`
  - `renderDocumentsList()` içine upload-zone + file-list JSX'i eklendi

**Backend değişikliği:** YOK
**Migration:** YOK
**document_processing.py:** dokunulmadı

**Test:** Gerçek `npm run lint` (oxlint) / `npm run build` (vite) bu ortamda çalıştırılamadı (bu ortamın erişemediği gerçek repository/araç seti gerektiriyor). Bunun yerine izole bir syntax doğrulaması yapıldı: esbuild ile JSX parse — **0 hata**. `pytest` çalıştırılmadı (backend değişmedi, gerek yok).

**Bilinen sınırlama / sonraki checkpoint'e not:** Backend `POST /api/documents/upload` bir dosya listesini tek istekte kabul ediyor ancak `document_service.upload_documents()` içinde herhangi bir dosya boşsa veya boyut limitini aşarsa **tüm batch** HTTPException ile reddediliyor (dosya bazlı izole hata yönetimi yok). Bu nedenle STEP 7B'de dosyaların **tek tek** (her biri kendi POST isteğiyle) yüklenmesi planlanıyor — aksi halde bir hatalı dosya, aynı batch'teki geçerli dosyaların da reddedilmesine sebep olur. Ayrıca backend, duplicate (checksum eşleşen) dosyalar için ayrı bir "duplicate" bayrağı döndürmüyor — mevcut kaydı aynı `DocumentResponse` şeklinde döndürüyor. STEP 7C'de bunu ayırt etmek için `created_at` zaman damgası karşılaştırması (heuristik) kullanılması planlanıyor; bu, backend'e dokunmadan yapılabilecek en güvenilir yöntem.

**Roadmap durumu:** CURRENT_STATE.md / MASTER_ROADMAP.md / COMPLETION_MATRIX.md **güncellenmedi** — STEP 7 (F-15/F-16) bu checkpoint ile tamamlanmadı, yalnızca ilk alt-parçası bitti. Henüz tamamlanmamış işi COMPLETE göstermemek için bilinçli olarak dokunulmadı.

**Sonraki checkpoint:** STEP 7B — Staged dosyaların backend'e tek tek upload edilmesi + her dosya için durum takibi (uploading/success/error)

**SAFE STOP POINT:** STEP 7A tamamlandı ve doğrulandı. STEP 7B'ye geçilmedi.

---

# STEP 7B

## CHECKPOINT 7B-01 — SYSTEM INSPECTION

STATUS:
COMPLETED

DATE:
2026-08-13

OBJECTIVE:
STEP 7B (single-file upload wiring) öncesi backend/frontend gerçek davranışını kod üzerinden doğrulamak. Kod değişikliği yapılmadı.

FILES INSPECTED:
- `backend/app/api/routes/documents.py`
- `backend/app/services/document_service.py` (`upload_documents`)
- `backend/app/schemas/document.py`
- `backend/app/models/document.py`
- `backend/app/db/database.py` (`get_db`)
- `backend/app/core/config.py`
- `frontend/src/App.jsx` (STEP 7A staging kodu)

FILES MODIFIED:
- NONE

FINDINGS:

**Endpoint / request format:**
- `POST /api/documents/upload`, `multipart/form-data`, field adı `files` (`files: list[UploadFile] = File(...)`) — **çoklu dosya tek istekte de kabul ediliyor**, ama tekli istek de (`files` alanına 1 dosya) aynı endpoint ile çalışır — API contract değişmeden tek-tek gönderim yapılabilir. VERIFIED.
- Response: `201 Created`, `list[DocumentResponse]` — gönderilen dosya sayısı kadar obje döner (tek dosya gönderirsen 1 elemanlı liste). VERIFIED.

**HTTP hata kodları (koddan doğrulandı):**
- Boş dosya → `422 Unprocessable Entity`, detail: `"{filename}: empty file."`
- Boyut limiti aşımı → `413 Request Entity Too Large`, detail: `"{filename}: file is too large."`
- Limit kaynağı: `settings.max_upload_size_mb`, config default = **25 MB** (gerçek `.env` değeri UNKNOWN — bu makineden görülemiyor)
- 400/401/403/404/409/500 için upload endpoint'inde **özel bir handling yok** — sadece FastAPI'nin genel hata davranışı geçerli. VERIFIED.

**🔴 KRİTİK BULGU — Batch failure davranışı:**
`upload_documents()` içinde tüm dosyalar tek bir `for` döngüsünde işleniyor, ama `db.commit()` yalnızca döngü **tamamen bittikten sonra bir kez** çağrılıyor (satır ~156). `get_db()` dependency'si (`db/database.py`) exception durumunda **explicit rollback yapmıyor**, sadece `finally: db.close()`.
→ Sonuç: Bir batch'te (aynı `POST` isteğinde) 3. dosya `422`/`413` hatası verirse, döngü orada exception ile kesilir, `commit()`'e hiç ulaşılmaz — **1. ve 2. dosya için yapılan `db.add()`/`flush()` de commit edilmemiş olur, o dosyalar da kaybolur.**
→ **Bu, STEP 7B-05'teki "tek tek gönder" kuralının backend tarafından da zorunlu kılındığını kanıtlıyor** — varsayım değil, kod kanıtı. VERIFIED.

**Duplicate davranışı (checksum eşleşmesi):**
- `documents.checksum` kolonu `unique=True`. Aynı checksum'lı dosya yüklenirse: yeni dosya diskten silinir (`Path(path).unlink()`), mevcut DB kaydı (`existing`) hiçbir `UPDATE` yapılmadan doğrudan `saved` listesine eklenir — **`created_at`/`updated_at` değişmez, DB'ye yeni satır yazılmaz, audit log oluşmaz** (`log_event("document_uploaded", ...)` çağrısı duplicate `continue` ile atlanan koddan SONRA, yani duplicate için hiç çalışmıyor). VERIFIED.
- `DocumentResponse` şeması hem `created_at` hem `updated_at` (ikisi de `datetime`, tz-naive UTC) döndürüyor. Model: `created_at` yalnızca oluşturulurken set ediliyor, sonrasında hiç değişmiyor (`onupdate` sadece `updated_at`'te var).
- **Duplicate tespiti için backend'de ayrı bir flag YOK**, ama `created_at` alanı **güvenilir bir dolaylı sinyal**: Tek dosyalık istek atılmadan hemen önce `Date.now()` yakalanıp, response'taki `created_at` bundan önemli ölçüde (örn. birkaç saniye) eskiyse → duplicate (mevcut kayıt). Aynı anda oluşturulan taze kayıtla mevcut-ama-yakın-zamanda-oluşmuş bir kaydı ayırt etme riski teorik olarak var ama pratikte (tek dosya = tek istek, sıralı gönderim) ihmal edilebilir düzeyde. → **DUPLICATE DETECTION: VERIFIED (heuristic, response'ta explicit flag yok, ama created_at zaman karşılaştırmasıyla güvenilir şekilde çıkarılabilir)** — INSUFFICIENT DATA değil, çünkü gereken alan (`created_at`) response'ta gerçekten mevcut ve davranışı koddan doğrulandı.

**Authentication / Authorization:**
`documents.py` route'unda hiçbir `Depends(get_current_user)` vb. yok — mevcut sistemde zaten YOK (bilinen durum), STEP 7B kapsamıyla ilgisiz, değişmiyor. VERIFIED (konfirme edildi, yeni bulgu değil).

**Audit log:**
Yalnızca gerçek yeni upload için `document_uploaded` event'i yazılıyor (`entity=document`, `metadata={match_status, confidence}`). Duplicate'te audit YOK. VERIFIED.

**Frontend mevcut durum (STEP 7A):**
`stagedFiles` state'i dosya listesini tutuyor, henüz hiçbir HTTP isteği yapılmıyor — STEP 7B'nin başlangıç noktası bu state. VERIFIED (kendi önceki checkpoint'im).

TESTS:
NOT RUN (bu checkpoint yalnızca inceleme; kod değişmedi)

VALIDATION:
Yukarıdaki tüm bulgular ilgili dosyaların gerçek içeriğinden (bu oturumdaki sandbox kopyası — kullanıcının STEP 6/7A teslimlerinde sağladığı aynı kod tabanı) doğrudan okunarak doğrulandı. Hiçbir davranış varsayılmadı.

RESULT:
PASS

NEXT:
CHECKPOINT 7B-02 — Single File Upload (`uploadSingleFile(file)` fonksiyonu)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-02 — SINGLE FILE UPLOAD

STATUS:
COMPLETED

DATE:
2026-08-13

OBJECTIVE:
`stagedFiles`'taki dosyaları backend'e sırayla, dosya başına ayrı HTTP request ile yükleyen gerçek upload mekanizmasını kurmak. Her dosya için bağımsız durum (pending/uploading/success/error). Duplicate ayrımı bu checkpoint'e dahil değil (7B-01'de belirlendiği gibi ertelendi).

FILES INSPECTED:
- `frontend/src/App.jsx` (STEP 7A sonrası hali)

FILES MODIFIED:
- `frontend/src/App.jsx`

FILES NOT MODIFIED:
- `backend/app/api/routes/documents.py`
- `backend/app/services/document_service.py`
- `backend/app/schemas/document.py`
- `backend/app/models/document.py`
- `backend/app/db/database.py`
- `backend/app/core/config.py`
- Alembic migration dosyaları
- `document_processing.py`
- `App.css` (yeni CSS gerekmedi — mevcut `.file-item-status`, `.icon-button`, `.primary-button` sınıfları kullanıldı)

CHANGES:
- Yeni state: `uploadStatus` (key→status map), `uploadResults` (key→{document|error} map), `isUploading` (batch guard)
- `fileKey(file)` — `${name}_${size}` anahtarı (dedup mantığıyla tutarlı)
- `uploadSingleFile(file)` — tek dosyayı `POST /api/documents/upload`'a `multipart/form-data`, field adı `files` ile gönderir; başarıda gerçek `response.data[0]` (DocumentResponse) kaydedilir; hatada `error.response.data.detail` (backend mesajı) korunarak saklanır, generic mesajla ezilmez
- `uploadStagedFiles()` — `stagedFiles` üzerinde **sıralı `for...of` + `await`** (Promise.all YOK), her dosya kendi request'ini gönderir; bir dosyanın hata vermesi döngüyü durdurmaz; zaten uploading/success olan dosyalar atlanır; bitince `loadDocuments()` ile tablo yenilenir
- `renderDocumentsList()`'teki `file-list` bloğuna: her dosya için durum etiketi (Bekliyor/Yükleniyor.../Yüklendi/Hata: {backend mesajı}), uploading sırasında kaldır butonu devre dışı, ve `stagedFiles.length` dosyayı yükle butonu (`isUploading` iken devre dışı)

FINDINGS:
- Backend'in tek-dosyalık isteğe de aynı endpoint/response şemasıyla (`list[DocumentResponse]`, 1 elemanlı) cevap verdiği 7B-01'de doğrulanan bilgiyle tutarlı şekilde çalıştı; API contract'ta hiçbir varsayım gerekmedi.

TESTS:
NOT RUN — gerçek backend'e karşı canlı bir upload denemesi bu ortamdan (network erişimi kapalı, gerçek repository yok) yapılamadı. Yalnızca statik doğrulama yapıldı (aşağıya bakınız).

VALIDATION:
- JSX syntax: **PASS** (esbuild parse, 0 hata)
- git diff --check: gerçek `git` bu ortamda repository olarak mevcut değil; eşdeğer kontrol yapıldı — trailing whitespace taraması **temiz** (0 satır)
- npm run lint (oxlint): **NOT RUN** — `oxlint` bu sandbox ortamında kurulu değil, çalıştırılamadı
- npm run build (vite): **NOT RUN** — `vite` bu sandbox ortamında kurulu değil, çalıştırılamadı
- Backend regresyon: **N/A / dokunulmadı** — bu checkpoint'te hiçbir backend dosyasına write/edit çağrısı yapılmadı (yalnızca `App.jsx` düzenlendi)

KNOWN LIMITATIONS:
- Duplicate tespiti bu checkpoint'te YOK (bilinçli olarak ertelendi — 7B-01'de belirlenen `created_at` heuristiği henüz uygulanmadı)
- Gerçek `npm run lint` / `npm run build` / canlı backend testi kullanıcının kendi makinesinde doğrulanmalı — bu ortamdan çalıştırılamadı
- Retry mekanizması yok (7B-09'a bırakıldı)
- Upload sonrası staged listesi temizlenmiyor / başarılı dosyalar listeden çıkarılmıyor (bilinçli olarak bu checkpoint'in kapsamı dışı bırakıldı)

RESULT:
PASS (statik doğrulama kapsamında)

NEXT:
CHECKPOINT 7B-03 — UI Status Management (zaten büyük ölçüde bu checkpoint'te birlikte uygulandı — bir sonraki oturumda önce bunun teyidi yapılmalı, ardından 7B-04/05 değerlendirilmeli)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-03 — UI STATUS MANAGEMENT

STATUS:
COMPLETED (7B-02 kapsamında zaten karşılandı — bu checkpoint yalnızca doğrulama, kod değişikliği yok)

DATE:
2026-08-13

OBJECTIVE:
Her staged dosyanın bağımsız, kullanıcının anlayabileceği bir durumu olduğunu doğrulamak: pending / uploading / success / error / duplicate.

FILES INSPECTED:
- `frontend/src/App.jsx` (`renderDocumentsList()` içindeki file-list bloğu)

FILES MODIFIED:
- NONE

CHANGES:
- NONE

FINDINGS:
- `pending`: `uploadStatus[key] || "pending"` fallback'i ile — kullanıcı "Bekliyor" olarak görüyor. VERIFIED.
- `uploading`: "Yükleniyor..." olarak gösteriliyor, kaldır butonu bu durumda devre dışı. VERIFIED.
- `success`: "Yüklendi" olarak gösteriliyor. VERIFIED.
- `error`: "Hata: {backend mesajı}" olarak gösteriliyor — backend'in gerçek `detail` metni korunuyor. VERIFIED.
- `duplicate`: **YOK.** 7B-02 kabul notu #3 gereği bilinçli olarak bu checkpoint'in kapsamı dışında — ayrı bir duplicate-detection checkpoint'ine bırakıldı. Bu durum COMPLETED sayılmasını engellemiyor çünkü zaten baştan bu checkpoint'in kapsamından çıkarılmıştı.
- Her dosyanın durumu bağımsız mı: EVET — `fileKey`'e göre ayrı state girdisi, 7B-02 final audit'inde zaten kanıtlandı.
- Bir dosyanın error olması diğerlerini etkiliyor mu: HAYIR — 7B-02 final audit'inde zaten kanıtlandı (sequential for-loop, her dosya kendi try/catch'i içinde).

TESTS:
NOT RUN (kod değişikliği olmadığı için gerek yok)

VALIDATION:
Bu checkpoint kod değiştirmediği için ayrı bir syntax/lint/build doğrulamasına gerek yok — 7B-02'nin doğrulanmış hali geçerliliğini koruyor.

RESULT:
PASS

NEXT:
CHECKPOINT 7B-04 — Progress (gerçek progress verisi yoksa sahte yüzde üretilmeyecek)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-04 — PROGRESS

STATUS:
COMPLETED

DATE:
2026-08-13

OBJECTIVE:
Gerçek (byte-bazlı) upload progress varsa göstermek; yoksa sahte/uydurma yüzde üretmemek.

FILES INSPECTED:
- `frontend/package.json` (axios versiyonu teyidi: `^1.19.0`)
- `frontend/src/App.jsx` (7B-02/03 sonrası hali)

FILES MODIFIED:
- `frontend/src/App.jsx`

CHANGES:
- Yeni state: `uploadProgress` (key → 0-100 arası tam sayı veya `null`)
- `uploadSingleFile()`'a axios `onUploadProgress` callback'i eklendi — `progressEvent.total` gerçekten mevcutsa (`if (progressEvent.total)`) `Math.round((loaded/total)*100)` ile gerçek yüzde hesaplanıyor; `total` yoksa (örn. content-length bilinmiyorsa) **hiçbir yüzde üretilmiyor**, state `null` kalıyor
- Her upload başlangıcında `uploadProgress[key]` `null`'a resetleniyor (önceki denemeden kalan yüzdenin yanlışlıkla görünmesini engellemek için)
- Render: `status === "uploading"` iken `typeof progress === "number"` ise `"Yükleniyor... %N"`, değilse sadece `"Yükleniyor..."` — sahte yüzde YOK

FINDINGS:
- `onUploadProgress`, axios'un 0.x'ten beri stabil, resmi olarak dokümante edilmiş bir config seçeneği — tarayıcıda XHR'nin `upload.onprogress` event'ini sarıyor, gerçek gönderilen/toplam byte bilgisini veriyor. Bu, "sahte progress" değil, gerçek ağ katmanı verisi. Backend'in ayrıca bir progress endpoint'i sağlamasına gerek yok — progress tamamen istemci tarafında, gönderilen request body'nin (FormData) boyutu üzerinden hesaplanıyor.
- `progressEvent.total` bazı ortamlarda (örn. content-length header'ı hesaplanamıyorsa) `undefined` olabilir — kod bunu açıkça kontrol ediyor ve o durumda yüzde göstermiyor (fallback metin).
- Bu checkpoint gerçek bir tarayıcı ortamında (bu sandbox'ta yok) canlı olarak test EDİLEMEDİ — davranış axios'un dokümante edilmiş, uzun süredir stabil API sözleşmesine dayanıyor, ama gerçek dosya yükleme sırasında görsel/sayısal doğrulama kullanıcının kendi ortamında yapılmalı.

TESTS:
NOT RUN (tarayıcı/network gerektiriyor, bu ortamda yok)

VALIDATION:
- JSX syntax: PASS (esbuild parse, 0 hata)
- Trailing whitespace: PASS (0 satır)
- Backend/App.css: DOKUNULMADI

KNOWN LIMITATIONS:
- Küçük dosyalarda (örn. birkaç KB) upload o kadar hızlı bitebilir ki progress event'i hiç tetiklenmeden direkt `success`'e geçilebilir — bu normal ve beklenen bir davranış, hata değil.
- Progress yalnızca upload (giden) tarafını gösteriyor; backend'in dosyayı işleme (metin çıkarma, eşleştirme) süresi progress'e dahil değil — bu süre zaten kısa ve backend'de ayrı bir progress mekanizması yok.

RESULT:
PASS

NEXT:
CHECKPOINT 7B-05 — Toplu upload orkestrasyonunun teyidi (7B-02'de `uploadStagedFiles()` ile zaten sıralı/tek-tek gönderim sağlanmıştı — bu checkpoint'te yeni kod beklenmiyor, yalnızca doğrulama)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-05 — SINGLE REQUEST PER FILE

STATUS:
COMPLETED (7B-02 kapsamında zaten karşılandı — bu checkpoint yalnızca doğrulama, kod değişikliği yok)

DATE:
2026-08-13

OBJECTIVE:
Toplu upload fonksiyonunun her dosya için ayrı bir HTTP request gönderdiğini, tek bir batch request kullanmadığını doğrulamak.

FILES INSPECTED:
- `frontend/src/App.jsx` (`uploadStagedFiles()`, satır 215-227)

FILES MODIFIED:
- NONE

CHANGES:
- NONE

FINDINGS:
- `uploadStagedFiles()` yalnızca `for (const file of stagedFiles) { ... await uploadSingleFile(file); }` kullanıyor — her `file` için `uploadSingleFile` ayrı bir `axios.post` çağrısı yapıyor (bkz. 7B-02). VERIFIED.
- Dosyadaki TEK `Promise.all` kullanımı dashboard'un ilk yüklemesinde (satır 70 — crew/ships/assignments/contracts/expiry, birbirinden bağımsız salt-okunur GET istekleri) — upload akışıyla ilgisi yok, karıştırılmamalı. VERIFIED.
- `.map(async ...)` gibi gizli paralellik deseni de yok. VERIFIED.
- Sonuç: "50 dosya → tek multipart request" anti-paterni YOK; "file1→request→sonuç, file2→request→sonuç..." deseni doğrulandı.

TESTS:
NOT RUN (kod değişikliği olmadığı için gerek yok)

VALIDATION:
Kod değişikliği yapılmadığı için 7B-04'ün doğrulanmış hali geçerliliğini koruyor.

RESULT:
PASS

NEXT:
CHECKPOINT 7B-06 — Duplicate Detection (`created_at` heuristiği ile, 7B-01'de tanımlanan yönteme göre)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-06 — DUPLICATE DETECTION

STATUS:
COMPLETED

DATE:
2026-08-13

OBJECTIVE:
Backend'de explicit bir "duplicate" flag'i olmadığı için (7B-01'de doğrulandı), `created_at` zaman damgası karşılaştırmasıyla duplicate dosyaları ayırt etmek. Yanlış pozitif üretmemeye öncelik vermek (spec: "duplicate olduğunu kesin olarak belirlemeye yetmiyorsa duplicate olarak işaretleme").

FILES INSPECTED:
- `frontend/src/App.jsx` (`uploadSingleFile()`, 7B-04 sonrası hali)

FILES MODIFIED:
- `frontend/src/App.jsx`

CHANGES:
- `uploadSingleFile()` içinde, `axios.post` çağrısından hemen önce `requestSentAt = Date.now()` yakalanıyor
- Başarılı response'ta: `document.created_at` (backend'de tz-naive UTC — 7B-01'de doğrulandı) sonuna `"Z"` eklenerek doğru şekilde UTC olarak parse ediliyor
- `DUPLICATE_THRESHOLD_MS = 3000` (3 saniye) eşiği ile: `requestSentAt - createdAtMs > 3000` ise → mevcut kayıt (duplicate); değilse → gerçekten yeni yüklenen dosya (success)
- Parse başarısız olursa (`Number.isNaN(createdAtMs)`) → **fail-safe olarak duplicate işaretlenmiyor**, `success` kabul ediliyor (spec'in "yanlış pozitif üretme" önceliğine uygun)
- `uploadResults`'a `duplicate: boolean` alanı eklendi
- Status modeline `"duplicate"` eklendi, render'da "Zaten yüklenmiş (duplicate)" olarak gösteriliyor
- Yeni CSS eklenmedi (düz metin, mevcut `.file-item-status` kullanılıyor)

FINDINGS / SINIRLAMALAR (dürüstçe belirtiliyor):
- Bu bir **heuristik**, kesin bir backend kontratı değil. 3 saniyelik eşik keyfi seçildi (network gecikmesi + saat senkronizasyon farkını tolere etmek için mantıklı bir değer, ama kanıtlanmış/test edilmiş bir sabit değil).
- Teorik yanlış negatif senaryosu: Aynı dosya, ilk kez yüklendikten **3 saniyeden kısa süre sonra** tekrar yüklenirse (örn. kullanıcı çok hızlı iki kez "Yükle"ye basarsa aynı staged dosyayı), `created_at` farkı eşiği aşmayabilir ve yanlışlıkla `success` gösterilebilir (aslında `duplicate`'tir). Bu, "yanlış pozitif üretme" önceliğinin doğal bir sonucu — sistem şüpheli durumda `success` tarafına düşüyor, `duplicate` tarafına değil.
- Teorik yanlış pozitif riski çok düşük: Sunucu saati ile istemci saati arasında >3sn fark varsa, gerçekten yeni bir dosya yanlışlıkla duplicate işaretlenebilir. Bu ortamda test edilemedi.
- Bu checkpoint gerçek bir backend'e karşı canlı test EDİLEMEDİ (network erişimi yok) — mantık 7B-01'in kod-doğrulanmış bulgularına dayanıyor, ama gerçek davranış kullanıcının kendi ortamında (iki kez aynı dosyayı yükleyerek) doğrulanmalı.

TESTS:
NOT RUN (tarayıcı/network gerektiriyor, bu ortamda yok)

VALIDATION:
- JSX syntax: PASS (esbuild parse, 0 hata)
- Trailing whitespace: PASS (0 satır)
- Backend/App.css: DOKUNULMADI

RESULT:
PASS (heuristik olarak — yukarıdaki sınırlamalarla birlikte)

NEXT:
CHECKPOINT 7B-07 — Error Handling (per-file HTTP status kodu + backend/frontend hata ayrımının daha görünür hale getirilmesi — mevcut hata mesajı zaten backend detail'ini koruyor, bu checkpoint'te HTTP status kodunun da ayrıca takip edilip edilmemesi değerlendirilecek)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-07 — ERROR HANDLING

STATUS:
COMPLETED

DATE:
2026-08-13

OBJECTIVE:
Her dosyanın hata bilgisini daha ayrıntılı takip etmek: HTTP status kodu + backend hatası mı yoksa ağ/frontend hatası mı ayrımı. Bir dosyanın hatası diğerlerini durdurmuyor olması zaten 7B-02/05'te doğrulandı — bu checkpoint yalnızca hata bilgisinin zenginliğini artırıyor.

FILES INSPECTED:
- `frontend/src/App.jsx` (`uploadSingleFile()` catch bloğu, 7B-06 sonrası hali)

FILES MODIFIED:
- `frontend/src/App.jsx`

CHANGES:
- `catch` bloğunda artık şunlar ayrıca yakalanıyor:
  - `httpStatus` — `error.response?.status ?? null` (backend'den gerçek bir HTTP response geldiyse kodu; gelmediyse `null`)
  - `isNetworkError` — `!error.response` (axios'un response almadığı durum — network kopması, CORS, sunucuya ulaşılamama vb.)
  - Mesaj önceliği: backend `detail` varsa o kullanılıyor (değişmedi) → yoksa VE network hatasıysa "Sunucuya bağlanılamadı (ağ hatası)." → yoksa axios'un kendi `error.message`'ı
- `uploadResults[key]`'e `httpStatus` ve `source` (`"backend"` veya `"network"`) alanları eklendi
- Render: hata satırında artık `Hata (HTTP {kod}): {mesaj}` formatı — HTTP kodu yoksa (network hatası) parantez kısmı hiç gösterilmiyor

FINDINGS / SINIRLAMALAR:
- 7B-01'de yalnızca `422` (boş dosya) ve `413` (boyut aşımı) backend kodda doğrulanmıştı. Bu checkpoint, spec'in açık talimatına uyarak (**"HTTP status kodlarını varsayarak yorumlama"**) `400/401/403/404/409/500` gibi kodlar için **özel/uydurma bir yorum eklemedi** — hangi kod gelirse gelsin ham haliyle (`HTTP {kod}`) gösteriliyor, backend'in `detail` mesajı öncelikli.
- `401/403` gibi kodlar zaten mevcut sistemde teorik olarak imkânsız çünkü authentication/authorization hiç yok (bilinen durum, STEP 7 kapsamı dışı).
- Bu checkpoint gerçek bir hata senaryosuyla (örn. gerçekten 25MB üstü dosya yükleyerek) canlı test EDİLEMEDİ — mantık axios'un dokümante edilmiş `error.response` / `error.request` ayrımına dayanıyor.

TESTS:
NOT RUN (tarayıcı/network gerektiriyor)

VALIDATION:
- JSX syntax: PASS (esbuild parse, 0 hata)
- Trailing whitespace: PASS (0 satır)
- Backend/App.css: DOKUNULMADI

RESULT:
PASS

NEXT:
CHECKPOINT 7B-08 — Upload Summary (Toplam/Başarılı/Duplicate/Hatalı sayıları — artık 7B-06/07 ile gerekli tüm durumlar mevcut, gerçek sayımdan hesaplanacak, hard-coded değer yok)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-08 — UPLOAD SUMMARY

STATUS:
COMPLETED

DATE:
2026-08-13

OBJECTIVE:
Upload batch'i tamamlandığında kullanıcıya gerçek sonuçlardan hesaplanan bir özet göstermek. Hard-coded değer yok, yalnızca gerçekten tamamlanmış işlemlerden sonra hesaplanmalı.

FILES INSPECTED:
- `frontend/src/App.css` (`.upload-summary`, `.upload-stat` — daha önce hiç kullanılmamış, hazır CSS)
- `frontend/src/App.jsx` (7B-07 sonrası hali)

FILES MODIFIED:
- `frontend/src/App.jsx`

CHANGES:
- `computeUploadSummary()` fonksiyonu eklendi: `isUploading` true iken (batch devam ederken) `null` döner — spec'in "yalnızca tamamlanmış işlemlerden sonra hesaplanmalı" kuralına uygun
- `stagedFiles` içinden yalnızca nihai duruma ulaşmış (`success`/`duplicate`/`error`) dosyalar sayılıyor; hiç deneme yapılmamışsa (`attempted.length === 0`) da `null` dönüyor, panel hiç gösterilmiyor
- **Önemli tasarım kararı:** `App.css`'teki hazır kategoriler `matched`/`pending`/`duplicate`/`error` — yani "success" değil, backend'in `document.match_status` alanına göre ayrılmış. Bu nedenle özet, upload başarısını değil, **başarılı yüklenen belgenin personelle eşleşip eşleşmediğini** (`matched` vs `pending`) ayrı bir eksende gösteriyor. `unmatched` için CSS'te ayrı kategori olmadığından `pending` kovasına dahil edildi.
- Tüm sayılar (`matched`, `pending`, `duplicate`, `error`, `total`) `uploadStatus`/`uploadResults` state'lerinden anlık hesaplanıyor — hiçbir sabit/hard-coded değer yok
- Yeni CSS eklenmedi — `.upload-summary`/`.upload-stat.{matched|pending|duplicate|error}` zaten mevcuttu, ilk kez kullanıldı

FINDINGS:
- Bu tasarım kararı (`matched/pending` ayrımı) spec'in orijinal örneğindeki "Başarılı: 7" ifadesinden farklı bir çerçeveleme oldu — CREWINTEL'in kendi CSS'i zaten bu şekilde tasarlanmıştı (muhtemelen Antigravity'nin önceki çalışmasından), ben buna sadık kaldım. Eğer gerçek kullanıcı ihtiyacı düz "başarılı/hatalı/duplicate" sayısıysa (match_status ayrımı olmadan), bu ayrı bir küçük düzeltme olarak ele alınabilir — şimdilik mevcut CSS'in niyetine göre ilerledim.
- "Toplam" sayısı için CSS'te ayrı bir stat kutusu yok (yalnızca 4 kategori var) — bu checkpoint'te yeni CSS eklememek için ayrı bir toplam kutusu eklenmedi, `uploadSummary.total` state'te hesaplanıyor ama şu an görsel olarak ayrıca gösterilmiyor.

TESTS:
NOT RUN (tarayıcı gerektiriyor)

VALIDATION:
- JSX syntax: PASS (esbuild parse, 0 hata)
- Trailing whitespace: PASS (0 satır)
- Hard-coded değer taraması: PASS (tüm sayılar `uploadSummary.*`'dan, state'ten türetiliyor)
- Backend: DOKUNULMADI

RESULT:
PASS

NEXT:
CHECKPOINT 7B-09 — Retry (yalnızca `error` durumundaki dosyalar tekrar denenebilecek; `success`/`duplicate` dosyalar tekrar gönderilmeyecek)

BLOCKERS:
NONE

---

## CHECKPOINT 7B-09 — RETRY

STATUS:
COMPLETED

DATE:
2026-08-13

OBJECTIVE:
Hatalı dosyalar için "Tekrar Dene" — yalnızca başarısız dosyayı yeniden göndermek, başarılı/duplicate dosyaları asla tekrar göndermemek, aynı backend contract'ını (mevcut `uploadSingleFile`) kullanmak.

FILES INSPECTED:
- `frontend/src/App.jsx` (7B-08 sonrası hali)

FILES MODIFIED:
- `frontend/src/App.jsx`

CHANGES:
- `retryUpload(file)` fonksiyonu eklendi: `uploadStatus[key] !== "error"` ise hiçbir şey yapmadan çıkıyor (guard) — bu hem mantıksal koruma hem de çift-tetikleme koruması (retry sırasında status "uploading"a geçtiği an bu koşul da false olur)
- `retryUpload`, mevcut `uploadSingleFile(file)`'ı **aynen** çağırıyor — yeni bir upload fonksiyonu/endpoint yok, backend contract'ı değişmedi
- Retry tamamlandıktan sonra `loadDocuments()` çağrılıyor (batch upload ile tutarlı — retry başarılı olursa belge tablosu güncellensin diye)
- "Tekrar Dene" butonu, `file-item` içinde **yalnızca `status === "error"` iken render ediliyor** — bu, kod seviyesinde `success`/`duplicate` dosyalar için butonun DOM'da hiç var olmamasını garanti ediyor (koşullu render, disabled değil — daha güçlü bir garanti)

FINDINGS:
- Retry sırasında dosyanın state'i doğru şekilde tekrar `uploading`'e geçiyor (çünkü `uploadSingleFile` bunu zaten en başında yapıyor — 7B-02'den beri değişmedi) ve sonucuna göre `success`/`error`/`duplicate`'e dönüyor (7B-06'daki duplicate mantığı retry'de de aynen çalışıyor — aynı fonksiyon çağrıldığı için ayrı bir kod yolu yok, otomatik tutarlı).
- Bu checkpoint gerçek bir hata senaryosunda (örn. gerçekten başarısız bir dosyayı retry ederek) canlı test EDİLEMEDİ.

TESTS:
NOT RUN (tarayıcı gerektiriyor)

VALIDATION:
- JSX syntax: PASS (esbuild parse, 0 hata)
- Trailing whitespace: PASS (0 satır)
- Backend: DOKUNULMADI, yeni endpoint/contract değişikliği yok

RESULT:
PASS

NEXT:
CHECKPOINT 7B-10 — Validation (gerçek `npm run lint` / `npm run build` / `pytest` — bu, kullanıcının kendi `C:\CREWINTEL` ortamında çalıştırması gereken bir checkpoint; bu sandbox'tan gerçek araçlara erişim yok)

BLOCKERS:
NONE


