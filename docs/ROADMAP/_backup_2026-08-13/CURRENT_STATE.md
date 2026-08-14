# CREWINTEL — CURRENT STATE
> Bu belge yalnız okunduğunda "CREWINTEL şu anda nerede?" sorusunu yanıtlar.
> **Son güncelleme:** 2026-08-10 | Tamamlanan: STEP 3

---

## ÖZET

CREWINTEL, gemi personel yönetim sistemidir. Backend MVP'si tamamlanmış ve stabil durumda. Frontend temel CRUD ekranlarına sahip; belge yönetimi UI henüz yazılmamış. Authentication yoktur — sistem lokal tek kullanıcı için tasarlanmıştır.

---

## BACKEND

| Alan | Durum | Detay |
|---|---|---|
| Framework | ✅ DONE | FastAPI 0.141.1 |
| ORM | ✅ DONE | SQLAlchemy 2.0.51 |
| Database | ✅ DONE | PostgreSQL 17 (Docker: port 5433) |
| Config | ✅ DONE | pydantic-settings, `.env` tabanlı |
| Migrations | ✅ DONE | Alembic, 3 migration (0001→0002→0003) |
| Crew CRUD | ✅ DONE | 5 endpoint, filtreli liste, audit log |
| Ship CRUD | ✅ DONE | 5 endpoint, IMO validation, audit log |
| Assignment CRUD | ✅ DONE | 5 endpoint, audit log |
| Contract CRUD | ✅ DONE | 5 endpoint, audit log |
| Document upload | ✅ DONE | Multi-file, PDF+TXT, SHA-256 dedup |
| Document list | ✅ DONE | crew_id, doc_type, match_status, expiry_status filtreli |
| Document download | ✅ DONE | FileResponse |
| Document match | ✅ DONE | Manuel eşleştirme, audit log |
| Document delete | ✅ DONE | Audit log |
| Document processing | ✅ DONE | Text extract, regex metadata, name matching |
| Expiration service | ✅ DONE | expired/urgent/approaching/valid/no_date + summary |
| Audit logging | ✅ DONE | Tüm CRUD olayları, GET /api/audit-logs/ |
| Error handling | ⚠️ PARTIAL | HTTPException var, global handler yok |
| User model | ⚠️ PARTIAL | Model var, migration yok (0004 bekleniyor) |
| Authentication | ❌ MISSING | Hiçbir middleware yok |
| Authorization/RBAC | ❌ MISSING | |

**Toplam API endpoint:** 34

---

## DATABASE

| Tablo | Durum | Migration |
|---|---|---|
| `crew_members` | ✅ Mevcut (28 alan) | 0001 + 0003 |
| `ships` | ✅ Mevcut | 0002 |
| `ship_crew_assignments` | ✅ Mevcut | 0002 |
| `contracts` | ✅ Mevcut | 0002 |
| `documents` | ✅ Mevcut (16 alan) | 0003 |
| `audit_logs` | ✅ Mevcut | 0003 |
| `users` | ⚠️ Model var, **tablo yok** | 0004 henüz oluşturulmadı |

**Document.match_status değerleri:** `pending` · `matched` · `unmatched`

**Expiry status değerleri (hesaplanan):** `expired` · `urgent` · `approaching` · `valid` · `no_date`

---

## FRONTEND

| Ekran | Durum | Notlar |
|---|---|---|
| Dashboard | ⚠️ PARTIAL | 3 kart var (personel/gemi/aktif), belge metrikleri yok |
| Personel listesi | ✅ Temel | Liste + "Personel Ekle" formu |
| Personel detay | ⚠️ PARTIAL | 6 alan gösteriyor, 9 yeni alan gösterilmiyor |
| Gemiler | ✅ Temel | Liste + detay + atama listesi |
| Atamalar | ✅ Temel | Liste |
| Kontratlar | ✅ Temel | Liste |
| Belgeler | ❌ YOK | API hazır |
| Toplu upload | ❌ YOK | En kritik eksik |
| Pending eşleşme | ❌ YOK | Backend STEP 1 ile hazır |
| Audit log | ❌ YOK | Backend hazır |
| Arama/filtre UI | ❌ YOK | Backend destekliyor |
| Dashboard expiration | ❌ YOK | `/api/expiration/summary` hazır |

**`App.css` (437 satır):** Tamamen hazır — badge, tablo, upload-zone, pending-card, audit-row, confidence-bar, tabs.

**`App.jsx` (165 satır):** Sadece mevcut CRUD ekranları. Aşama 4 başlatılmadı.

---

## TESTS

```
38 passed, 0 failed  (2026-08-10 STEP 3 sonrası)

test_api.py        : 10 test (Crew, Ship, Assignment, Contract, validation, FK)
test_audit.py      : 11 test (CRUD audit kayıtları, filtreler)
test_documents.py  : 5 test  (upload, match, create-from-CV, dedup, match_status filter)
test_expiration.py : 12 test (expired/urgent/approaching/valid/no_date/summary + boundary)
```

**Eksik coverage:** error cases (404/409/422), audit date filter, frontend testleri.

---

## SECURITY

| Alan | Durum |
|---|---|
| Authentication | ❌ YOK |
| Authorization | ❌ YOK |
| JWT | ❌ YOK |
| SQL injection | ✅ ORM korumalı |
| Path traversal | ✅ UUID4 filename |
| File size limit | ✅ MAX_UPLOAD_SIZE_MB |
| Checksum dedup | ✅ SHA-256 |
| CORS | ⚠️ Configurable, varsayılan geniş |
| Secrets | ✅ .env, git'e eklenmez |
| Input validation | ✅ Pydantic |
| MIME validation | ⚠️ Eksik — whitelist yok |

> Sistem şu anda tamamen açık. Lokal kullanım için kabul edilebilir. **Network'e açılmadan önce authentication zorunludur.**

---

## DEPLOYMENT

| Alan | Durum |
|---|---|
| Docker Compose | ✅ Çalışıyor (postgres + backend + frontend) |
| PostgreSQL | ✅ port 5433 (yerel) / 5432 (Docker ağı) |
| Backend Dockerfile | ✅ Mevcut |
| Frontend Dockerfile | ✅ Mevcut |
| Environment config | ✅ .env + docker-compose env |
| Production hardening | ❌ YOK |
| SSL/nginx | ❌ YOK |
| Monitoring | ❌ YOK |

---

## AI / MOBILE

| Alan | Durum |
|---|---|
| `ai/` klasörü | ⚠️ BOŞ — gelecek için ayrılmış |
| `mobile/` klasörü | ⚠️ BOŞ — gelecek için ayrılmış |
| `deployment/` klasörü | ⚠️ BOŞ |
| `scripts/` klasörü | UNVERIFIED — içerik kontrol edilmedi |
| `database/` klasörü | UNVERIFIED — içerik kontrol edilmedi |

---

## TECHNICAL DEBT

| Borç | Öncelik | Notlar |
|---|---|---|
| User migration eksik | P2 | `users` tablosu oluşmuyor |
| Authentication yok | P3 | Network'e açılmadan önce şart |
| `AuditLogResponse` route içine gömülü | P2 | `schemas/audit_log.py` olmalı |
| `date.today()` timezone yok | P3 | UTC refactor ileride gerekebilir |
| App.jsx monolitik | P3 | Bileşen ayrımı — Aşama 4 bittikten sonra |
| MIME validation eksik | P2 | Upload güvenliği |
| Global error handler yok | P2 | Beklenmedik 500'lerde stack trace sızabilir |

---

## CURRENT STEP

```
Tamamlanan : STEP 3
Sonraki    : STEP 4 — Audit Date Range Filter
             (audit_logs.py + 2-3 test, ~10 satır, P2, Low risk)
```

---

## KNOWN LIMITATIONS

1. Belge eşleştirme yalnızca metin tabanlı regex — OCR yok, PDF dışı format yok
2. Authentication yokken herhangi bir istek tüm API'lere erişebilir
3. `date.today()` server yerel saatine göre çalışır — timezone edge case'leri olabilir
4. Belge eşleştirme confidence eşiği (≥90) sabit kodlanmış — configurable değil
5. Expiration hesabı gerçek zamanlı (cron/job yok) — sayfa yenilenince güncellenir
