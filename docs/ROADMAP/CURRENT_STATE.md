# CREWINTEL — CURRENT STATE
> Bu belge yalnız okunduğunda "CREWINTEL şu anda nerede?" sorusunu yanıtlar.
> **Son güncelleme:** 2026-08-12 | Tamamlanan: STEP 6

---

## ÖZET

CREWINTEL, gemi personel yönetim sistemidir. Backend MVP'si tamamlanmış ve stabil durumda. Frontend'de Dashboard (expiration metrikleri dahil), Personel (detay dahil), Gemiler, Atamalar, Kontratlar ve Belgeler ekranları tamamlanmış durumda; toplu upload, pending eşleşme ve audit log ekranları henüz yazılmamış. Authentication yoktur — sistem lokal tek kullanıcı için tasarlanmıştır.

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
| Audit logging | ✅ DONE | Tüm CRUD olayları, GET /api/audit-logs/ (+ date_from/date_to — STEP 4) |
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
| Dashboard | ✅ DONE | 3 temel kart + expiration metrikleri (STEP 5A) |
| Personel listesi | ✅ Temel | Liste + "Personel Ekle" formu |
| Personel detay | ✅ DONE | 15 alan gösteriyor — 9 yeni alan STEP 5B ile eklendi |
| Gemiler | ✅ Temel | Liste + detay + atama listesi |
| Atamalar | ✅ Temel | Liste |
| Kontratlar | ✅ Temel | Liste |
| Belgeler | ✅ DONE | STEP 6 — liste ekranı (tablo, loading/error/empty state) |
| Toplu upload | ❌ YOK | En kritik eksik — **STEP 7** |
| Pending eşleşme | ❌ YOK | Backend STEP 1 ile hazır — STEP 8 |
| Audit log | ❌ YOK | Backend hazır — STEP 9 |
| Arama/filtre UI | ❌ YOK | Backend destekliyor |

**`App.css` (437 satır):** Tamamen hazır — badge, tablo, upload-zone, pending-card, audit-row, confidence-bar, tabs.

**`App.jsx` (293 satır):** Dashboard, Crew (liste+detay), Ships, Assignments, Contracts, Documents ekranları mevcut. Sidebar navigation'da Belgeler sekmesi var (STEP 6); Audit sekmesi henüz yok (STEP 9 bekliyor).

---

## TESTS

```
41 passed, 0 failed  (STEP 4 sonrası doğrulanan son sayı)

test_api.py        : 10 test (Crew, Ship, Assignment, Contract, validation, FK)
test_audit.py      : 11 test + STEP 4 date range testleri (CRUD audit kayıtları, filtreler)
test_documents.py  : 5 test  (upload, match, create-from-CV, dedup, match_status filter)
test_expiration.py : 12 test (expired/urgent/approaching/valid/no_date/summary + boundary)
```

**Not:** STEP 5A, 5B ve 6 frontend-only değişikliklerdi, backend'e dokunmadı — bu yüzden pytest bu adımlardan sonra yeniden çalıştırılmadı, 41 sayısı hâlâ geçerli son doğrulama.

**STEP 6 lint/build durumu:** Bu dokümantasyon senkronizasyonu sırasında STEP 6 için gerçek `npm run lint` / `npm run build` bu makinede çalıştırılmadı. STEP 6 teslim edildiğinde yalnızca izole bir ortamda JSX syntax doğrulaması (esbuild parse, 0 hata) yapılmıştı — bu, gerçek `oxlint`/`vite build` sonucunun yerini tutmaz. Bu adım hâlâ bekliyor.

**Eksik coverage:** error cases (404/409/422), frontend testleri.

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
Tamamlanan : STEP 6 (Documents List Ekranı)
Sonraki    : STEP 7 — Toplu Upload UI (drag & drop)
             (App.jsx, Medium-Large risk)
```

---

## KNOWN LIMITATIONS

1. Belge eşleştirme yalnızca metin tabanlı regex — OCR yok, PDF dışı format yok
2. Authentication yokken herhangi bir istek tüm API'lere erişebilir
3. `date.today()` server yerel saatine göre çalışır — timezone edge case'leri olabilir
4. Belge eşleştirme confidence eşiği (≥90) sabit kodlanmış — configurable değil
5. Expiration hesabı gerçek zamanlı (cron/job yok) — sayfa yenilenince güncellenir
