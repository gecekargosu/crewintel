# CREWINTEL — MASTER DEVELOPMENT LOG

> AI-readable project memory & engineering handoff document.
> Bu dosya, projeyi devralan herhangi bir AI agent'ın mevcut durumu sıfırdan taramadan anlayabilmesi için tasarlanmıştır.

**Son güncelleme:** 2026-08-30 (v3 — mobile security hardening)
**Tamamlanan faz:** FASE 3 (Auth & Authorization)
**Test durumu:** 282 passed, 0 failed, 2 skipped

---

## 1. PROJECT IDENTITY

| Alan | Değer |
|------|-------|
| Proje adı | CREWINTEL |
| Proje tipi | Crew Management / Personnel Archive System |
| Hedef kullanıcı | Tek kullanıcı (denizcilik sektörü) |
| Geliştirme aşaması | Backend stabil · Frontend monolitik ama fonksiyonel · AI modülü entegre |
| Proje kökü | `C:\CREWINTEL` |
| GitHub | https://github.com/gecekargosu/crewintel |

### Kısa Açıklama

CREWINTEL; gemi personelinin CV'lerini, pasaportlarını, gemiadamı cüzdanlarını, STCW belgelerini, GOC belgelerini, sağlık belgelerini, kontratlarını ve diğer belgelerini merkezi bir sistemde arşivleyen, belge geçerlilik sürelerini takip eden ve tüm işlemleri denetlenebilir hale getiren profesyonel bir crew management platformudur.

---

## 2. PROJECT GOAL

### Çözülen Problem

Gemi personelinin belgeleri Excel/kağıt/farklı klasörlerde tutulduğunda belge kaybı, tarihlerin unutulması, denetim problemleri ve manuel takip yükü oluşmaktadır. CREWINTEL bu süreci dijitalleştirir.

### Mevcut Kullanım Senaryoları (koddan doğrulanmış)

- Personel (crew member) CRUD yönetimi (+ CSV import/export)
- Gemi (ship) CRUD yönetimi
- Personel–gemi ataması (assignment)
- Kontrat yönetimi
- Belge yükleme (PDF/TXT), arşivleme ve otomatik eşleştirme
- Belge tipi tespiti (CV, pasaport, STCW, GOC, medical, contract, other)
- İsim/pasaport/gemiadamı cüzdanı numarası ile personel eşleştirme
- CV yüklendiğinde otomatik personel oluşturma
- Belge geçerlilik süresi takibi (expired / urgent / approaching / valid / no_date)
- Tüm CRUD işlemlerinin audit log kaydı
- Pending belgeler için manuel eşleştirme + onay/reddetme
- Dashboard özeti + görevler (tıklanabilir kartlar)
- Authentication / JWT / RBAC (admin, hr, viewer, roller)
- Bildirim sistemi (bildirim üretme + okundu işaretleme + e-posta gönderimi)
- Crew Portal (personel kendi belgesini yükler, iş ilanlarına başvurur)
- İş İlanları + Yayın (WhatsApp, Instagram, Facebook kanalları)
- AI modülleri: belge analizi, kişisel eşleştirme, anomali tespit, öneri, özetleme
- WhatsApp Business API entegrasyonu (kuyruk + retry + duplicate koruması)
- Push notification altyapısı (device token yönetimi)
- Mesajlaşma (conversation + message)
- Ayarlar paneli (SMTP, WhatsApp, uygulama ayarları)

---

## 3. ARCHITECTURE (Doğrulanmış)

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│  React/Vite (tek sayfa uygulama — App.jsx, 5066 satır)         │
│  Port: 5173 (Vite dev) / 80 (nginx Docker)                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP (Axios, JWT token header)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND                                  │
│  FastAPI (Python 3.13)                                         │
│  Port: 8000                                                    │
│  17 router · 100+ endpoint · JWT auth · RBAC                   │
├─────────────────────────────────────────────────────────────────┤
│  Routes: auth, crew, ships, assignments, contracts,            │
│          documents, expiration, audit_logs, dashboard,         │
│          portal, messages, notifications, devices,             │
│          settings, jobs, ai, webhooks                           │
├─────────────────────────────────────────────────────────────────┤
│  Services: audit, document_service, document_processing,       │
│            match_engine, eligibility, expiration_service,      │
│            notifications, push, whatsapp                        │
├─────────────────────────────────────────────────────────────────┤
│  AI Modules (backend/ai/): llm_client, document_analyzer,     │
│            crew_matcher, anomaly_detector, recommendation,     │
│            summarizer                                          │
├─────────────────────────────────────────────────────────────────┤
│  Auth: JWT (access token), password hashing (bcrypt),          │
│        role-based access (admin/hr/viewer/crew),               │
│        brute-force koruması (10 deneme/5dk/IP)                │
├─────────────────────────────────────────────────────────────────┤
│  ORM: SQLAlchemy 2.x · Migration: Alembic (10 migration)      │
└─────────────────────┬───────────────────────────────────────────┘
                      │ SQLAlchemy (psycopg)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE                                    │
│  PostgreSQL 17                                                  │
│  Port: 5433 (host) / 5432 (Docker)                             │
│  20 tablo · 10 migration (head: 20260818_0010)                 │
└─────────────────────────────────────────────────────────────────┘
```

| Katman | Teknoloji | Versiyon |
|--------|-----------|----------|
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
| AI/LLM | httpx (Groq API) | — |
| Testing | pytest | 8.4.1 |
| Test HTTP | httpx | 0.28.1 |
| Container | Docker Compose | — |
| Database | PostgreSQL | 17 |

---

## 4. DIRECTORY STRUCTURE (Güncel)

```
C:\CREWINTEL\
├── .env                          # Runtime secrets — git'e eklenmez
├── .env.example                  # Şablon (GROQ_API_KEY dahil)
├── .env.groq                     # Groq API key örneği
├── docker-compose.yml            # postgres + backend + frontend servisleri
├── docker-compose.prod.yml       # Production compose
├── pytest.ini                    # Test config (rootdir, pythonpath)
├── playwright.config.js          # E2E test config
├── playwright-audit.config.js    # Audit test config
│
├── ai/                           # ⚠️ BOŞ — modüller taşındı
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt          # Python paketleri
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 20260809_0001_create_crew_members.py
│   │       ├── 20260809_0002_add_core_domain_models.py
│   │       ├── 20260809_0003_add_documents_profiles_audit.py
│   │       ├── 20260817_0004_add_auth_and_indexes.py
│   │       ├── 20260817_0005_add_document_matches.py
│   │       ├── 20260818_0006_add_notifications_staffing_portal.py
│   │       ├── 20260818_0007_add_app_settings.py
│   │       ├── 20260818_0008_add_jobs.py
│   │       ├── 20260818_0009_add_job_publishing.py
│   │       └── 20260818_0010_mobile.py
│   ├── tests/
│   │   ├── conftest.py           # SQLite in-memory test DB, fixtures
│   │   └── test_auth.py          # Auth testleri (yeni)
│   └── app/
│       ├── main.py               # FastAPI app, CORS, 17 router kaydı
│       ├── run.py                # Uvicorn entry point
│       ├── core/
│       │   ├── config.py         # pydantic-settings, .env yükler
│       │   └── security.py       # JWT, password hashing, token
│       ├── api/
│       │   ├── deps.py           # get_current_user, require_roles
│       │   └── routes/
│       │       ├── auth.py       # Login, register, users CRUD, JWT
│       │       ├── crew.py       # CrewMember CRUD + import/export
│       │       ├── ships.py      # Ship CRUD + staffing + positions
│       │       ├── assignments.py # Assignment CRUD
│       │       ├── contracts.py  # Contract CRUD
│       │       ├── documents.py  # Document upload/match/review/approve
│       │       ├── expiration.py # Expiration summary + filters
│       │       ├── audit_logs.py # Audit log listing + date filter
│       │       ├── dashboard.py  # Dashboard summary
│       │       ├── portal.py     # Crew portal (izole)
│       │       ├── messages.py   # Conversation + messages
│       │       ├── notifications.py # Notifications + email
│       │       ├── devices.py    # Push device tokens
│       │       ├── settings.py   # App settings (SMTP, WhatsApp)
│       │       ├── jobs.py       # Job postings + applications + publish
│       │       └── ai.py         # AI endpoints (analyze, match, etc.)
│       ├── db/
│       │   ├── database.py       # engine, SessionLocal, Base, get_db()
│       │   ├── init_db.py        # create_all (test/dev için)
│       │   └── seed.py           # Seed data
│       ├── models/               # SQLAlchemy ORM modelleri (14 dosya)
│       │   ├── crew_member.py    # 35 alan
│       │   ├── ship.py           # 9 alan
│       │   ├── assignment.py     # ShipCrewAssignment
│       │   ├── contract.py       # 11 alan
│       │   ├── document.py       # 20 alan
│       │   ├── document_match.py # 10 alan
│       │   ├── audit_log.py      # 9 alan
│       │   ├── user.py           # 9 alan (role, is_active, password_hash)
│       │   ├── user_device.py    # Push device tokens
│       │   ├── job.py            # JobPosting, JobApplication, JobTemplate, JobPublication, WhatsAppMessage, JobImage
│       │   ├── notification.py   # 11 alan
│       │   ├── message.py        # Conversation + Message
│       │   ├── setting.py        # AppSetting (key/value)
│       │   └── ship_position.py  # 6 alan
│       ├── schemas/              # Pydantic request/response şemaları
│       │   ├── crew_member.py
│       │   ├── ship.py
│       │   ├── assignment.py
│       │   ├── contract.py
│       │   └── document.py
│       └── services/             # İş mantığı katmanı
│           ├── audit.py          # log_event() helper
│           ├── document_service.py
│           ├── document_processing.py
│           ├── document_processing.HEAD.py  # ⚠️ Stale backup (15 Ağustos corruption)
│           ├── match_engine.py
│           ├── eligibility.py
│           ├── expiration_service.py
│           ├── notifications.py
│           ├── push.py
│           └── whatsapp.py
│
├── backend/ai/                   # AI modülleri (repo kökünden taşındı)
│   ├── __init__.py
│   ├── llm_client.py             # Groq API client
│   ├── document_analyzer.py
│   ├── crew_matcher.py
│   ├── anomaly_detector.py
│   ├── recommendation.py
│   └── summarizer.py
│
├── frontend/
│   ├── package.json              # React, Vite, Axios, Lucide-React
│   ├── vite.config.js
│   ├── index.html
│   ├── nginx.conf
│   └── src/
│       ├── main.jsx
│       ├── App.jsx               # ⚠️ 5066 satır monolitik dosya
│       ├── App.css
│       └── index.css
│
├── tests/                        # Root-level pytest tests
│   ├── conftest.py               # SQLite in-memory fixtures
│   ├── test_api.py               # Crew, Ship, Assignment, Contract CRUD
│   ├── test_audit.py             # Audit log tests (date filter dahil)
│   ├── test_documents.py         # Upload, match, filter tests
│   ├── test_expiration.py        # Expiration service tests
│   └── test_auth.py              # Auth tests (yeni)
│
├── playwright-tests/             # E2E testler
├── playwright-audit/             # Audit E2E testler
├── scripts/                      # Yardımcı scriptler
├── database/                     # DB ile ilgili dosyalar
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── DEVELOPMENT_LOG.md        # ← BU DOSYA
│   ├── system-tree/              # Detaylı sistem ağaçları
│   │   ├── README.md
│   │   ├── BACKEND.md
│   │   ├── DATABASE.md
│   │   ├── FRONTEND.md
│   │   └── INTEGRATIONS.md
│   └── ROADMAP/                  # Yol haritası dosyaları
│       ├── MASTER_ROADMAP.md
│       ├── CURRENT_STATE.md
│       ├── COMPLETION_MATRIX.md
│       ├── ENGINEERING_PLAN.md
│       └── ARCHITECTURE_PLAN.md
│
├── storage/                      # Yüklenen belge dosyaları
├── backups/                      # Yedek dosyalar
├── mobile-app/                   # Android mobil uygulama (UMAY Admin) — 84+ dosya
├── deployment/                   # Deployment dosyaları
│
├── CREWINTEL_AUDIT.txt           # ⚠️ Stale dosya
├── CREWINTEL_CURRENT_STATE.txt   # ⚠️ Stale dosya
├── CREWINTEL_REAL_STATE_20260815.txt  # ⚠️ Stale dosya
├── CREWINTEL_REVIEW_PACKAGE.txt  # ⚠️ Stale dosya (git takibinde)
├── project-tree.txt              # ⚠️ Stale dosya
├── duplicate_test.txt            # ⚠️ Stale dosya
├── duplicate_test_2.txt          # ⚠️ Stale dosya
├── e ps                          # ⚠️ Stale dosya (kazayla oluşmuş)
├── backend;C                     # ⚠️ Boş dizin (kazayla oluşmuş)
└── mobile.zip                    # ⚠️ Stale dosya
```

---

## 5. BACKEND CURRENT STATE

| Modül | Durum | Dosya | Notlar |
|-------|-------|-------|--------|
| FastAPI app | ✅ DONE | main.py | 17 router, CORS configurable |
| Config | ✅ DONE | core/config.py | pydantic-settings, `.env`'den yükler |
| Security | ✅ DONE | core/security.py | JWT, bcrypt password hashing |
| Auth deps | ✅ DONE | api/deps.py | get_current_user, require_roles |
| DB connection | ✅ DONE | db/database.py | pool_pre_ping, get_db() dependency |
| Alembic migrations | ✅ DONE | 10 migration | Linear chain, head: 20260818_0010 |
| Authentication | ✅ DONE | routes/auth.py | Login, register, JWT, brute-force koruması |
| User CRUD | ✅ DONE | routes/auth.py | Admin kullanıcı yönetimi |
| CrewMember CRUD | ✅ DONE | routes/crew.py | 35 alan, filtreli liste, CSV import/export |
| Ship CRUD | ✅ DONE | routes/ships.py | IMO validation, staffing, positions |
| Assignment CRUD | ✅ DONE | routes/assignments.py | |
| Contract CRUD | ✅ DONE | routes/contracts.py | 7/30/90 gün filtre |
| Document upload | ✅ DONE | routes/documents.py | Multi-file, PDF+TXT, SHA-256 checksum |
| Document match | ✅ DONE | routes/documents.py + match_engine.py | Otomatik + manuel eşleştirme |
| Document review | ✅ DONE | routes/documents.py | Onay/reddetme kuyruğu |
| Expiration service | ✅ DONE | routes/expiration.py + services/ | expired/urgent/approaching/valid/no_date |
| Audit logging | ✅ DONE | routes/audit_logs.py + services/audit.py | log_event(), tarih filtresi |
| Dashboard | ✅ DONE | routes/dashboard.py | Özet + görevler |
| Notifications | ✅ DONE | routes/notifications.py | Bildirim üretme + okundu + e-posta |
| Messages | ✅ DONE | routes/messages.py | Conversation + message |
| Devices | ✅ DONE | routes/devices.py | Push device token yönetimi |
| Settings | ✅ DONE | routes/settings.py | App settings (SMTP, WhatsApp) |
| Portal | ✅ DONE | routes/portal.py | Crew portal (izole, kendi verisi) |
| Jobs | ✅ DONE | routes/jobs.py | İş ilanları + yayın + WhatsApp |
| AI | ✅ DONE | routes/ai.py + backend/ai/ | Groq API entegrasyonu |
| WhatsApp | ✅ DONE | services/whatsapp.py | Graph API, kuyruk, retry |

---

## 6. DATABASE CURRENT STATE

### Migration Zinciri

```
0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0007 → 0008 → 0009 → 0010 (head)
```

| Migration | İçerik |
|-----------|--------|
| 0001 | Initial crew_members table |
| 0002 | ships, assignments, contracts, users |
| 0003 | documents, audit_logs, crew profile fields |
| 0004 | Auth fields (password_hash, audit user identity), crew identifier indexes |
| 0005 | document_matches table |
| 0006 | notifications, user↔crew link, availability, document archive, ship positions |
| 0007 | app_settings (SMTP + WhatsApp alanları) |
| 0008 | job_postings, job_applications |
| 0009 | job_templates, job_publications, whatsapp_messages, job_images, job_posting detay alanları |
| 0010 | M1 Mobile: crew_members iş tercihleri, user_devices, conversations, messages, job_applications.match_score/applied_from |

### Tablolar (20)

| Tablo | Alan Sayısı | Açıklama |
|-------|------------|----------|
| crew_members | 35 | Personel bilgileri + profil + iş arama |
| ships | 10 | Gemi bilgileri |
| ship_positions | 6 | Gemi kadro pozisyonları |
| assignments | 10 | Personel-gemi atamaları |
| contracts | 11 | Kontrat bilgileri |
| documents | 20 | Belge arşivi + eşleştirme durumu |
| document_matches | 10 | Eşleştirme geçmişi |
| users | 9 | Kullanıcılar (admin/hr/viewer/crew rolleri) |
| user_devices | 7 | Push device tokenları |
| audit_logs | 9 | Audit trail |
| notifications | 11 | Bildirimler |
| conversations | 6 | Mesajlaşma sohbetleri |
| messages | 8 | Mesajlar |
| job_postings | 27 | İş ilanları + detay |
| job_applications | 9 | İş başvuruları |
| job_templates | 5 | İlan şablonları |
| job_publications | 9 | Yayın geçmişi (kanal bazlı) |
| whatsapp_messages | 11 | WhatsApp gönderim kuyruğu |
| job_images | 5 | Üretilen ilan görselleri |
| app_settings | 2 | Key/value uygulama ayarları |

### Bilinen Uyumsuzluklar

- `job_postings.start_date`: DB'de var, model'de yok (eski sütun, zararsız)
- `alembic_version`: DB tablosu (Alembic iç, model'de doğal olarak yok)

---

## 7. API INVENTORY

### Toplam: 100+ endpoint

| Router | Prefix | Endpoint Sayısı | Notlar |
|--------|--------|-----------------|--------|
| auth | `/api/auth` | 10 | login, register, users CRUD, password/email change |
| crew | `/api/crew` | 8 | CRUD + eligible + export + import |
| ships | `/api/ships` | 8 | CRUD + staffing + positions |
| assignments | `/api/assignments` | 5 | CRUD |
| contracts | `/api/contracts` | 5 | CRUD |
| documents | `/api/documents` | 9 | upload, bulk, match, review, approve, reject, manual-match, download, list |
| expiration | `/api/expiration` | 6 | summary + expired/urgent/approaching/valid/no-date |
| audit_logs | `/api/audit-logs` | 1 | date_from/date_to filtre |
| dashboard | `/api/dashboard` | 1 | summary |
| notifications | `/api/notifications` | 5 | list, generate, read, send-bulk, send-email |
| portal | `/api/portal` | 10 | me, documents, jobs, apply, contact, preferences, contracts |
| messages | `/api/messages` | 4 | conversations, send, read |
| devices | `/api/devices` | 2 | register, unregister |
| settings | `/api/settings` | 3 | get/put, contact, notif-public |
| jobs | `/api/jobs` | 13 | CRUD + apply + publish + image + publications + whatsapp |
| job-templates | `/api/job-templates` | 4 | CRUD |
| whatsapp | `/api/whatsapp` | 3 | queue, process, send |
| webhooks | `/api/webhooks` | 2 | whatsapp verify + receive |
| ai | `/api/ai` | 7 | health, analyze, analyze/upload, match, anomalies, recommend, summarize |

---

## 8. FRONTEND CURRENT STATE

| Ekran | Durum | Notlar |
|-------|-------|--------|
| Login | ✅ DONE | JWT token ile giriş, brute-force koruması |
| Dashboard | ✅ DONE | Özet kartları, expiration metrikleri, görevler |
| Personel listesi | ✅ DONE | Filtreli liste, arama, CSV import/export |
| Personel detay | ✅ DONE | 35 alan, belgeler, atamalar |
| Belgeler | ✅ DONE | Liste + drag&drop upload + toplu yükleme |
| Review kuyruğu | ✅ DONE | Onay/reddetme |
| Gemiler | ✅ DONE | CRUD + staffing + pozisyon yönetimi |
| Atamalar | ✅ DONE | CRUD |
| Kontratlar | ✅ DONE | CRUD + süre filtresi |
| Uygunluk | ✅ DONE | Pozisyon bazlı personel arama |
| İş İlanları | ✅ DONE | CRUD + yayın paneli + retry |
| İletişim | ✅ DONE | WhatsApp linkleri |
| Ayarlar | ✅ DONE | SMTP, WhatsApp, uygulama ayarları |
| Crew Portal | ✅ DONE | Personel kendi verisi + iş başvurusu |
| Audit Log | ✅ DONE | Tarih filtresi |
| Notification | ✅ DONE | Bildirim listesi |
| AI | ❌ YOK | Backend hazır, frontend'de bağlantı yok |

**App.jsx:** 5066 satır, tek dosya (monolitik). Tüm ekranlar, state, API çağrıları burada.
**CSS:** Güncel, tüm ekranlar için sınıflar mevcut.

---

## 9. TEST STATUS

```
282 passed, 2 skipped, 0 failed (son doğrulama: 2026-08-28)
```

| Dosya | Test Sayısı | Kapsam |
|-------|------------|--------|
| `tests/test_api.py` | 10 | Crew, Ship, Assignment, Contract CRUD; health; validation; FK |
| `tests/test_audit.py` | 14 | CRUD audit logları + date_from/date_to filtre |
| `tests/test_audit_fixes.py` | 6 | Crew izolasyonu, admin silme, rate limit |
| `tests/test_auth.py` | 26 | Login, JWT, roller, brute-force, user management |
| `tests/test_crew_filtering.py` | 17 | Rank, languages, experience, contract, document filtreleri |
| `tests/test_documents.py` | 14 | Upload, match, dedup, download, strong identifier, classification |
| `tests/test_document_pipeline.py` | 35 | Batch, candidates, matches, delete, type, expiry, pagination, RBAC, lifecycle |
| `tests/test_expiration.py` | 12 | Expiration service tüm kategoriler + boundary testleri |
| `tests/test_match_engine.py` | 21 | Exact, fuzzy, conflict, review, dry-run, bulk |
| `tests/test_mobile_api.py` | 18 | Register, portal, messages, devices, deactivate |
| `tests/test_phase4b_features.py` | 25 | Eligibility, staffing, notifications, CSV, settings, portal, jobs, WhatsApp |
| `tests/test_ai.py` | 29 | AI endpoint RBAC, health, mocked LLM, validation |
| `tests/test_date_identifier.py` | 33 | Tarih parse + pasaport çıkarma (unit) |
| `tests/test_document_processing.py` | 4 | İsim çıkarma (unit) |
| `tests/test_match_crew.py` | 7 | Personel eşleştirme (unit) |
| `tests/test_normalize.py` | 2 | Metin normalizasyonu (unit) |
| `tests/test_auth.py` | 26 | Auth testleri (login, JWT, role, brute-force, audit) |
| `tests/test_ai.py` | 17 | AI endpoint testleri (health, analyze, match, summarize, RBAC) |
| `tests/test_crew_filtering.py` | 17 | Crew filtreleme (rank, languages, experience, contract) |
| `tests/test_match_engine.py` | 21 | Matching engine (exact, fuzzy, conflict, review, dry-run) |
| `tests/test_mobile_api.py` | 18 | Mobile API (register, portal, messages, devices) |
| `tests/test_phase4b_features.py` | 25 | Phase 4B (eligibility, staffing, notifications, CSV, portal, jobs, WhatsApp) |
| `tests/test_audit_fixes.py` | 6 | Audit fixes (crew isolation, admin delete, rate limit) |
| `tests/test_date_identifier.py` | 33 | Date parsing + passport extraction (unit) |
| `tests/test_document_processing.py` | 4 | Name extraction (unit) |
| `tests/test_match_crew.py` | 7 | Crew matching (unit) |
| `tests/test_normalize.py` | 2 | Text normalization (unit) |

### Frontend Lint
```
0 errors (29 warnings — kritik değil)
```

### AI Endpoint Testleri (yeni)
- `tests/test_ai.py` — 17 test
- Health endpoint: her zaman çalışır, GROQ_API_KEY olsa da olmasa da
- Analyze/Match/Summarize/Anomalies/Recommend: GROQ_API_KEY yokken 503, mock ile test edildi
- AI endpoint'lerine `require_roles("admin", "hr")` eklendi (2026-08-28, P0 RBAC fix)
- Viewer/crew → 403, unauthenticated → 401, LLM auth layer'da engelleniyor

### Frontend Build
```
✅ 378ms, 0 error
```

---

## 10. SECURITY STATUS

| Alan | Durum | Detay |
|------|-------|-------|
| Authentication | ✅ DONE | JWT access token, login endpoint |
| Password hashing | ✅ DONE | bcrypt |
| Authorization/RBAC | ✅ DONE | admin/hr/viewer/crew rolleri, require_roles() |
| Brute-force koruması | ✅ DONE | 10 hatalı deneme / 5dk / IP |
| JWT secret | ✅ Güçlü | `dev-insecure-secret-change-me` değil, güçlü secret kullanılıyor |
| CORS | ✅ Configurable | `.env`'den ayarlanıyor |
| SQL Injection | ✅ ORM korumalı | SQLAlchemy parameterized queries |
| Path traversal | ✅ Korunaklı | uuid4 ile dosya adı üretiliyor |
| File size limit | ✅ Configurable | MAX_UPLOAD_SIZE_MB |
| Checksum dedup | ✅ SHA-256 | |
| Secrets | ✅ .env'de | Git'e eklenmez, .gitignore'da |
| Input validation | ✅ Pydantic | |
| Docker healthcheck | ✅ DONE | Backend + PostgreSQL |

### Bilinen Zayıflıklar

- `backend/.env` dosyası `.freebuff/` altında oluştu — `backend/.env` `.gitignore`'da değil ama Docker compose root `.env`'den okuyor, local dev için gerekebilir
- Production'da rate limiting memory'de (Redis'e taşımalı)

---

## 11. TECHNICAL DEBT

| Borç | Durum | Öncelik |
|------|-------|---------|
| ~~`document_processing.HEAD.py` stale backup~~ | ✅ Silindi | — |
| ~~`backend;C` boş dizin~~ | ✅ Silindi | — |
| ~~`e ps` stale dosya~~ | ✅ Silindi | — |
| ~~`CREWINTEL_AUDIT.txt` ve benzeri stale dosyalar~~ | ✅ Silindi | — |
| ~~`duplicate_test.txt` / `duplicate_test_2.txt`~~ | ✅ Silindi | — |
| ~~`project-tree.txt`~~ | ✅ Silindi | — |
| `CREWINTEL_REVIEW_PACKAGE.txt` | ⚠️ Git'ten çıkarılmalı | Düşük |
| App.jsx monolitik (5066 satır) | ⚠️ Bölünecek | Yüksek |
| Frontend AI bağlantısı yok | ⚠️ Planlanmalı | Orta |
| ~~AI endpoint'lerinde RBAC yok~~ | ✅ Düzeltildi (P0 fix) | — |
| 2 migration'da boş downgrade (0003, 0004) | ⚠️ Düzeltilebilir | Düşük |
| `job_postings.start_date` DB'de model'de yok | ⚠️ Temizlenmeli | Düşük |
| Rate limiting memory'de | ⚠️ Redis'e taşınmalı | Orta |
| CI/CD pipeline yok | ⚠️ Kurulmalı | Orta |
| Passport regex: `Document No: PAS-XXXXXX` formatını yakalayamıyor | ⚠️ Metadata extraction gap | Düşük |

---

## 12. COMPLETED DEVELOPMENT STEPS

### STEP 1–6 (2026-08-10/12) — İlk Geliştirme
- STEP 1: match_status filter
- STEP 2: Cleanup + development log
- STEP 3: Expiration service testleri (12 test)
- STEP 4: Audit log tarih filtresi
- STEP 5A: Dashboard expiration metrics
- STEP 5B: Crew detail genişletme (9 yeni alan)
- STEP 6: Documents list ekranı

### STEP 7A–7B (2026-08-13) — Upload UI
- STEP 7A: Drag & drop upload zone UI
- STEP 7B: Single-file upload wiring + inspection

### FASE 0–2 (2026-08-28) — Kritik Düzeltmeler
- **FASE 0:** GitHub ↔ Local senkronizasyonu ✅
- **FASE 1:** AI modülü entegrasyonu ✅
  - `ai/` → `backend/ai/` taşındı
  - sys.path hack kaldırıldı
  - GROQ_API_KEY docker-compose'a eklendi
  - `renderPortal` → `RenderPortal` React hook düzeltmesi
  - Stale dosyalar git'ten temizlendi
  - Docker healthcheck eklendi
  - Backend test conftest.py eklendi
- **FASE 2:** DB + Migrations bütünlüğü ✅
  - 10 migration linear chain doğrulandı
  - 20 tablo, 19 model — sütunlar uyumlu
  - `alembic current` = `alembic heads` = `20260818_0010`

---

## 13. CURRENT VERIFIED STATE

```
Last completed step : FASE 4 — Document Pipeline + Match Engine Audit (2026-08-28)

Tests               : 282 passed, 2 skipped, 0 failed
Backend             : Stabil, 100+ endpoint, 17 router
Frontend            : 5066 satır monolitik App.jsx, 0 lint error, build OK
Database            : 20 tablo, 10 migration, head: 20260818_0010
Security            : JWT + RBAC + brute-force koruması aktif (AI dahil)
AI                  : Groq entegrasyonu sağlıklı + RBAC korumalı
Docker              : 3 servis ayakta (frontend, backend, postgres)
Docs                : Development log, system-tree, human test checklist güncel

P0 RBAC Fix (2026-08-28):
- AI endpoint'lerine require_roles("admin", "hr") eklendi
- Viewer/crew → 403, unauthenticated → 401
- LLM client auth layer'da engelleniyor (çağrılmıyor)
- Integration smoke test: Docker'da doğrulandı

Known issues:
- App.jsx monolitik (5066 satır)
- Frontend'de AI bağlantısı yok
- 2 migration'da boş downgrade
- Rate limiting memory'de
- Passport regex: Document No: formatını yakalayamıyor (metadata extraction gap)

Match Engine Audit (2026-08-28):
- 758 belgeden 715'i eşleşmiş (%94 başarı)
- 43 unmatched: tamamı DB'de olmayan test kişisi belgeleri
- İngilizce format ("Name: X") extract_name ile doğru parse ediliyor
- Türkçe format ("Adı Soyadı: X") sorunsuz çalışıyor
- Pozitif test: DB'ye geçici "Ahmet Yilmaz" eklenip AUTO_MATCH doğrulandı
- Passport regex: "Document No: PAS-XXXXXX" formatını yakalayamıyor (technical debt)

Frontend düzeltmeleri (2026-08-28):
- CSV Export: JWT token ile fetch (401 fix)
- Email feedback: "Gönderildi 0 kişi" yanıltıcılığı düzeltildi
- form-input dark mode: color-scheme: light eklendi
- CSV Import: indirilebilir şablon eklendi
- Badge CSS: conflict, review_required, failed, rejected eklendi
- Form validasyon: backend detail mesajları frontend'e yansıyor

Next recommended step : FASE 5 — Matching Engine derin tur veya J responsive test

Do not start yet:
- App.jsx refactor (tek seferde değil, incremental)
- Production deployment
```

---

## 14. RED LINES (Bu kurallar ASLA çiğnenmemeli)

1. Projeyi sıfırdan yazma.
2. Çalışan işlevselliği silme.
3. Veritabanı şemasını Alembic migration olmadan değiştirme.
4. Authentication davranışını test olmadan değiştirme.
5. Deterministic matching'i LLM-based guessing ile değiştirme.
6. App.jsx'i tek seferde yeniden yazma (incremental, feature-by-feature).
7. Her büyük değişiklik öncesi: inspect → explain → modify → test → report.
8. Testler başarısızken hiçbir görevi "tamamlandı" olarak işaretleme.
9. Mevcut API endpoint'lerinin backward compatibility'ini koru.
10. Her düzeltme için bir doğrulama komutu/testi olmalı.
11. Her değişikliğin changelog'unu tut.
12. Sorun zaten düzeltilmişse tekrar "düzeltme" — doğrula ve geç.

---

| 2026-08-29 | Social downloader JWT auth eklendi | FASE 3 |
| 2026-08-29 | Cookie encryption (XOR) eklendi | FASE 3 |
| 2026-08-29 | Rate limiting (20/dk) eklendi | FASE 3 |
| 2026-08-29 | DEBUG-only HTTP logging | FASE 3 |
| 2026-08-29 | ApiClient.init() 14 Activity'ye eklendi | FASE 3 |
| 2026-08-29 | Typed data models (Map yerine) | FASE 3 |
| 2026-08-30 | ShipListActivity kendi layout'unu kullaniyor | FASE 3 |
| 2026-08-30 | SalaryActivity kendi item layout'unu kullaniyor | FASE 3 |
| 2026-08-30 | Notes crash duzeltildi (NoteRequest model) | FASE 3 |
| 2026-08-30 | Notes PostgreSQL'e tasindi (RAM yerine) | FASE 3 |
| 2026-08-30 | Job Post EXTRA_TEXT kaldirildi (resim uzeri yazi) | FASE 3 |
| 2026-08-30 | JWT Refresh Token (7 gun) + 401 auto refresh | FASE 3 |
| 2026-08-30 | Cookie encryption AES (Fernet) ile degistirildi | FASE 3 |
| 2026-08-30 | Task ownership eklendi (user_id) | FASE 3 |
| 2026-08-30 | --no-check-certificates kaldirildi | FASE 3 |
| 2026-08-30 | Dashboard kinetik animasyonlar (pulse/breathe) | FASE 3 |
| 2026-08-30 | HTTPS network security config (production) | FASE 4 |
| 2026-08-30 | WorkManager download (arka plan destegi) | FASE 4 |
| 2026-08-30 | JWT Secure Storage (Android Keystore) | FASE 4 |
| 2026-08-30 | Rate limiting enhanced (cleanup + retry-after) | FASE 4 |
| 2026-08-30 | Typed DTO tum Maps activity'leri | FASE 4 |
| 2026-08-30 | Play Store hazirlik (ProGuard + minify) | FASE 4 |

---

## 15. NEXT EXECUTION ORDER

| Faz | Görev | Durum |
|-----|-------|-------|
| FASE 3 | Auth & Authorization testleri | ✅ Tamamlandı |
| FASE 4 | Mobile security hardening | ✅ Tamamlandı |
| FASE 5 | Integration testleri (mobile ↔ backend) | ⏳ SIRADA |
| FASE 6 | İnsan testi (Pazartesi öncesi) | ⏳ |
| FASE 7 | Matching ölçek benchmarkı | ⏳ |
| FASE 8 | App.jsx incremental refactor | ⏳ |
| FASE 9 | AI/Business logic ayrımı | ⏳ |
| FASE 10 | Production hazırlığı (CI/CD, HTTPS, Docker security) | ⏳ |
| FASE 11 | Play Store yayını | ⏳ |

---

## 16. CHANGELOG

| Tarih | Değişiklik | Fase/STEP |
|-------|-----------|-----------|
| 2026-08-09 | İlk kurulum, crew_members tablosu | 0001 |
| 2026-08-09 | ships, assignments, contracts, users eklendi | 0002 |
| 2026-08-09 | documents, audit_logs, crew profile fields | 0003 |
| 2026-08-10 | STEP 1: match_status filter | STEP 1 |
| 2026-08-10 | STEP 2: Cleanup + development log | STEP 2 |
| 2026-08-10 | STEP 3: Expiration service testleri (12 test) | STEP 3 |
| 2026-08-12 | STEP 4: Audit log tarih filtresi | STEP 4 |
| 2026-08-12 | STEP 5A: Dashboard expiration metrics | STEP 5A |
| 2026-08-12 | STEP 5B: Crew detail genişletme | STEP 5B |
| 2026-08-12 | STEP 6: Documents list ekranı | STEP 6 |
| 2026-08-13 | STEP 7A: Drag & drop upload zone | STEP 7A |
| 2026-08-13 | STEP 7B: Single-file upload wiring | STEP 7B |
| 2026-08-17 | Auth, portal, messages, notifications eklendi | 0004–0006 |
| 2026-08-17 | App settings, jobs eklendi | 0007–0008 |
| 2026-08-18 | Job publishing, mobile features eklendi | 0009–0010 |
| 2026-08-18 | AI modülleri eklendi (repo kökünde) | AI |
| 2026-08-28 | `ai/` → `backend/ai/` taşındı, sys.path hack kaldırıldı | FASE 1 |
| 2026-08-28 | GROQ env var'ları docker-compose'a eklendi | FASE 1 |
| 2026-08-28 | `RenderPortal` React hook düzeltmesi | FASE 1 |
| 2026-08-28 | Stale dosyalar git'ten temizlendi | FASE 1 |
| 2026-08-28 | Docker healthcheck eklendi | FASE 1 |
| 2026-08-28 | `backend/tests/conftest.py` eklendi | FASE 1 |
| 2026-08-28 | JWT_SECRET_KEY güçlü secret ile değiştirildi | FASE 1 |
| 2026-08-28 | DB migration bütünlüğü doğrulandı | FASE 2 |
| 2026-08-28 | DEVELOPMENT_LOG.md baştan yazıldı | FASE 2 |
| 2026-08-28 | Match engine kritik 3 hata düzeltildi (passport conflict, TR isim, ID mismatch) | FASE 3 |
| 2026-08-28 | Duplicate uyarıda dosya adı gösterme eklendi | FASE 3 |
| 2026-08-28 | Maritime relevance filtresi eklendi (metadata.maritime_relevance) | FASE 3 |
| 2026-08-28 | Kişisel bilgiler tablosu 3x Uyruk hatası düzeltildi | FASE 3 |
| 2026-08-28 | Bireysel WhatsApp butonu eklendi (personel detayı) | FASE 3 |
| 2026-08-28 | E-posta gönderme test edildi — SMTP aktif, çalışıyor | FASE 3 |
| 2026-08-29 | Social Downloader entegre edildi (yt-dlp + ffmpeg, `/api/social/downloader/*`) | FASE 3 |
| 2026-08-29 | Android SocialDownloaderActivity URL fix — port 8001 bağımlılığı kaldırıldı | FASE 3 |
| 2026-08-29 | Dockerfile'a ffmpeg kurulumu eklendi | FASE 3 |
| 2026-08-29 | Social downloader analiz YouTube, Instagram, TikTok, Facebook, Pinterest, Twitter destekli | FASE 3 |
