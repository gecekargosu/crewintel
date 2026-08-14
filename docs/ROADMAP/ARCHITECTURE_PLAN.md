# CREWINTEL — ARCHITECTURE PLAN
> Mevcut mimari ile hedef mimariyi karşılaştırır. Geçiş stratejisini açıklar.

---

## KATMAN DİYAGRAMI

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React/Vite  ←→  Axios  ←→  App.jsx  ←→  App.css           │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (JSON + multipart)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         API LAYER                            │
│  FastAPI  ←→  Pydantic schemas  ←→  HTTPException           │
│  Routes: crew / ships / assignments / contracts /            │
│          documents / expiration / audit_logs                 │
└──────────┬───────────────────────────────────┬──────────────┘
           │                                   │
           ▼                                   ▼
┌──────────────────────┐          ┌────────────────────────────┐
│    SERVICE LAYER      │          │     PROCESSING LAYER       │
│  DocumentService      │          │  document_processing.py    │
│  ExpirationService    │          │  - extract_text()          │
│  audit.log_event()    │          │  - extract_metadata()      │
└──────────┬────────────┘          │  - match_crew()            │
           │                       │  - parse_date()            │
           ▼                       │  - store_file()            │
┌──────────────────────┐          └────────────────────────────┘
│   DOMAIN / MODEL      │
│  SQLAlchemy Models    │
│  crew_member / ship / │
│  assignment / contract│
│  document / audit_log │
│  user (tablo yok)    │
└──────────┬────────────┘
           │
           ▼
┌──────────────────────┐          ┌────────────────────────────┐
│    DATABASE LAYER     │          │   FILE STORAGE LAYER       │
│  PostgreSQL 17        │          │  storage/  (local disk)    │
│  Docker port 5433     │          │  uuid4 filename            │
│  Alembic migrations   │          │  SHA-256 dedup             │
└──────────────────────┘          └────────────────────────────┘
```

---

## KATMAN DETAYLARI

### 1. Frontend Layer

| | Mevcut | Hedef |
|---|---|---|
| Framework | React + Vite | React + Vite (değişmez) |
| Yapı | Tek dosya (App.jsx) | App.jsx + bileşenler (STEP 17 sonrası) |
| CSS | App.css (437 satır, hazır) | Aynı |
| HTTP | Axios (muhtemelen) | Axios |
| State | useState (local) | useState — Redux/Context gerekmez |
| Routing | Sayfa tabanlı (nav prop) | Aynı |
| Auth | Yok | JWT token → localStorage (STEP 15 sonrası) |

**Güçlü:** App.css tamamen hazır, CSS sistemi sağlam.
**Zayıf:** App.jsx tek dosya, 165 satır — Aşama 4 sonrası ~900 satıra çıkacak.
**Teknik Borç:** Component split (STEP 17) — Aşama 4 bittikten sonra.

### 2. API Layer

| | Mevcut | Hedef |
|---|---|---|
| Framework | FastAPI | FastAPI (değişmez) |
| Validation | Pydantic v2 | Aynı |
| Error handling | HTTPException (kısmi) | Global exception handler eklenmeli |
| Auth middleware | Yok | `Depends(get_current_user)` (STEP 15) |
| Rate limiting | Yok | Gelecek |
| API versioning | Yok (implicit /api/) | Gelecek |

**Güçlü:** 34 endpoint, tümü çalışıyor, Pydantic validation sağlam.
**Zayıf:** Authentication yok, global error handler yok.

### 3. Service Layer

| Servis | Mevcut | Durum |
|---|---|---|
| `DocumentService` | upload, list, get, delete, match, serialize | ✅ DONE |
| `ExpirationService` | expired/urgent/approaching/valid/no_date/summary | ✅ DONE |
| `audit.log_event()` | Tüm CRUD event'larına yayılmış | ✅ DONE |
| `UserService` | YOK | MISSING (STEP 15) |
| `NotificationService` | YOK | FUTURE |

### 4. Domain / Model Layer

| Model | Tablo | Alanlar | Durum |
|---|---|---|---|
| `CrewMember` | `crew_members` | 28 | ✅ |
| `Ship` | `ships` | 7 | ✅ |
| `ShipCrewAssignment` | `ship_crew_assignments` | 8 | ✅ |
| `Contract` | `contracts` | 11 | ✅ |
| `Document` | `documents` | 16 | ✅ |
| `AuditLog` | `audit_logs` | 7 | ✅ |
| `User` | — | 7 | ⚠️ Model var, **tablo yok** |

### 5. Database Layer

| | Mevcut | Hedef |
|---|---|---|
| DB | PostgreSQL 17 | Aynı |
| ORM | SQLAlchemy 2.0 | Aynı |
| Migration | Alembic (3 migration) | +0004 (users), +future |
| Connection | pool_pre_ping | Aynı |
| Test DB | SQLite in-memory (StaticPool) | Aynı |

### 6. Document Storage Layer

| | Mevcut | Hedef |
|---|---|---|
| Depolama | Lokal disk (`storage/`) | Lokal → S3/MinIO (gelecek) |
| Filename | UUID4 | Aynı |
| Dedup | SHA-256 checksum | Aynı |
| Max boyut | `MAX_UPLOAD_SIZE_MB` env | Aynı |
| Desteklenen | PDF + TXT | +DOCX, +images (gelecek) |

### 7. Processing Layer

| | Mevcut | Hedef |
|---|---|---|
| Text extract | pypdf + raw text | +OCR (gelecek, ai/ klasörü) |
| Metadata | Regex tabanlı | +NLP (gelecek) |
| Name matching | `SequenceMatcher` (≥0.98 high, ≥0.80 medium) | Aynı (stabil) |
| Date parsing | `parse_date()` — 3 format | Genişletilebilir |
| Doc type | Keyword matching | Aynı |

### 8. Audit Layer

| | Mevcut | Hedef |
|---|---|---|
| Model | `AuditLog` (7 alan) | +date filter (STEP 4) |
| Events | Tüm CRUD | Aynı |
| API | `GET /api/audit-logs/` | +date_from/date_to (STEP 4) |
| UI | YOK | STEP 9 |
| Schema | Route içine gömülü | Ayrı `schemas/audit_log.py` (STEP 12) |

### 9. Authentication / Security Layer

| | Mevcut | Hedef |
|---|---|---|
| Auth | ❌ YOK | JWT (STEP 15) |
| User CRUD | ❌ YOK | STEP 15 |
| RBAC | ❌ YOK | STEP 16 |
| Password | ❌ YOK | bcrypt (passlib) |
| MIME validation | ⚠️ PARTIAL | STEP 11 |
| CORS | ⚠️ Geniş | STEP 15 sonrası sıkılaştır |

### 10. AI Layer

| | Mevcut | Hedef |
|---|---|---|
| Klasör | `ai/` (BOŞ) | OCR, NLP, gelişmiş matching |
| Document AI | Regex tabanlı | Gelecek ML/AI model |
| Crew matching | SequenceMatcher | Gelecek vector similarity |

### 11. Mobile Layer

| | Mevcut | Hedef |
|---|---|---|
| Klasör | `mobile/` (BOŞ) | React Native veya Flutter |
| API | Backend hazır | Aynı API kullanılacak |
| Auth | Yok → JWT sonrası | JWT token (STEP 15 sonrası) |

### 12. Deployment / Operations Layer

| | Mevcut | Hedef |
|---|---|---|
| Container | Docker Compose | Docker Compose → K8s (gelecek) |
| Reverse proxy | Yok | nginx (gelecek) |
| SSL | Yok | Let's Encrypt (gelecek) |
| Monitoring | Yok | Sentry + Prometheus (gelecek) |
| Backup | Yok | pg_dump cron (gelecek) |
| CI/CD | Yok | GitHub Actions (gelecek) |

---

## MİMARİ GEÇİŞ STRATEJİSİ

```
CURRENT (M1 — Backend MVP)
  ✅ FastAPI + SQLAlchemy + PostgreSQL
  ✅ Document processing pipeline
  ✅ 34 API endpoint
  ✅ 38 test
  ❌ Auth yok
  ❌ Frontend eksik

TRANSITION (M2 — Frontend Complete)
  → STEP 4-9: Frontend tamamlanır
  → STEP 10: User migration
  → STEP 11: MIME validation
  Mimari değişmez, yeni katman eklenmez
  Mevcut çalışan sistemi bozmak YASAK

TRANSITION (M3 — Security)
  → STEP 15: Auth (en riskli adım)
  → STEP 16: RBAC
  → Tüm API'ler etkilenir, testler güncellenir
  → Network'e açılabilir hale gelir

TARGET (M4 — Production)
  → nginx + SSL
  → Monitoring
  → CI/CD
  → S3/MinIO storage
  → Mobile app
  → AI/OCR
```

---

## MİMARİ KARARLARI (ADR — Architecture Decision Records)

### ADR-1: Tek kullanıcı varsayımı
**Karar:** Auth olmadan başla, ileride ekle.
**Neden:** MVP hızlı geliştirildi, lokal kullanım için auth gereksiz.
**Risk:** Network'e açılırsa kritik güvenlik açığı.

### ADR-2: SQLite test DB
**Karar:** Production PostgreSQL yerine SQLite in-memory test DB.
**Neden:** Docker bağımlılığı olmadan hızlı test.
**Risk:** PostgreSQL-specific özellikler (JSON ops, arrays) test'te farklı davranabilir.

### ADR-3: Regex tabanlı metadata extraction
**Karar:** NLP/AI yerine regex ve SequenceMatcher.
**Neden:** Hızlı MVP, deterministic sonuçlar.
**Risk:** False positive/negative, Türkçe format farklılıkları.

### ADR-4: Lokal file storage
**Karar:** S3 yerine lokal `storage/` klasörü.
**Neden:** Basitlik, lokal kullanım.
**Risk:** Ölçeklenemez, yedekleme yok.

### ADR-5: App.jsx monolitik
**Karar:** Component split olmadan tek dosya.
**Neden:** MVP hızı.
**Risk:** ~900 satıra çıkacak, okunması zorlaşacak.
**Plan:** STEP 9 sonrası STEP 17 ile component split.
