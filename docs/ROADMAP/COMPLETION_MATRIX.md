# CREWINTEL — COMPLETION MATRIX
> Tüm önemli özelliklerin tek tablolu durum listesi. "Bir şeyi atladık mı?" kontrol listemiz.
> **Son güncelleme:** 2026-08-12 | Son tamamlanan: STEP 6

---

## STATUS LEGEND

| Kod | Anlam |
|---|---|
| ✅ DONE | Kod mevcut, doğrulanmış, testleri geçiyor |
| ⚠️ PARTIAL | Başlanmış, tamamlanmamış |
| ❌ MISSING | Planlanmış, henüz başlanmamış |
| ❓ UNVERIFIED | Kod/yapı mevcut ama çalıştığı doğrulanmamış |
| ⏸️ DEFERRED | Bilinçli olarak sonraya bırakılmış |
| 🔮 FUTURE | MVP sonrası, uzun vadeli |

---

## BACKEND

| ID | Domain | Feature | Status | Priority | Current Files | Missing Files | Test | Risk | Next Action |
|---|---|---|---|---|---|---|---|---|---|
| B-01 | Core | FastAPI app + CORS | ✅ DONE | — | `main.py` | — | ✅ | — | — |
| B-02 | Core | pydantic-settings config | ✅ DONE | — | `core/config.py` | — | ✅ | — | — |
| B-03 | Core | SQLAlchemy 2.x DB connection | ✅ DONE | — | `db/database.py` | — | ✅ | — | — |
| B-04 | Core | Global error handler | ⚠️ PARTIAL | P2 | `main.py` | — | ❌ | Low | STEP 11+ |
| B-05 | Crew | Crew CRUD (5 endpoint) | ✅ DONE | — | `routes/crew.py`, `models/crew_member.py` | — | ✅ | — | — |
| B-06 | Crew | Crew list filters (name/position/nationality/status/ship_id) | ✅ DONE | — | `routes/crew.py` | — | ✅ | — | — |
| B-07 | Crew | Crew rank/experience filter | ❌ MISSING | P3 | — | `routes/crew.py` (2 param) | ❌ | Low | STEP 13 |
| B-08 | Ship | Ship CRUD (5 endpoint) | ✅ DONE | — | `routes/ships.py` | — | ✅ | — | — |
| B-09 | Assignment | Assignment CRUD (5 endpoint) | ✅ DONE | — | `routes/assignments.py` | — | ✅ | — | — |
| B-10 | Contract | Contract CRUD (5 endpoint) | ✅ DONE | — | `routes/contracts.py` | — | ✅ | — | — |
| B-11 | Document | Multi-file upload (PDF+TXT) | ✅ DONE | — | `routes/documents.py`, `services/document_service.py` | — | ✅ | — | — |
| B-12 | Document | Document list + filters (crew_id, type, match_status, expiry) | ✅ DONE | — | `routes/documents.py`, `services/document_service.py` | — | ✅ | — | STEP 1 ✅ |
| B-13 | Document | Document detail | ✅ DONE | — | `routes/documents.py` | — | ✅ | — | — |
| B-14 | Document | Document file download | ✅ DONE | — | `routes/documents.py` | — | ❓ | — | — |
| B-15 | Document | Manual match (PUT /{id}/match) | ✅ DONE | — | `routes/documents.py` | — | ✅ | — | — |
| B-16 | Document | Document delete | ✅ DONE | — | `routes/documents.py` | — | ❌ | — | — |
| B-17 | Document | SHA-256 checksum deduplication | ✅ DONE | — | `services/document_service.py` | — | ✅ | — | — |
| B-18 | Document | MIME type whitelist validation | ❌ MISSING | P2 | — | `services/document_service.py` | ❌ | Low | STEP 11 |
| B-19 | Processing | Text extraction (PDF+TXT) | ✅ DONE | — | `services/document_processing.py` | — | ✅ | — | — |
| B-20 | Processing | Regex metadata extraction (date, number, name) | ✅ DONE | — | `services/document_processing.py` | — | ✅ | — | — |
| B-21 | Processing | Document type detection | ✅ DONE | — | `services/document_processing.py` | — | ✅ | — | — |
| B-22 | Processing | Crew name matching (SequenceMatcher) | ✅ DONE | — | `services/document_processing.py` | — | ✅ | — | — |
| B-23 | Processing | CV → auto crew creation | ✅ DONE | — | `services/document_processing.py` | — | ✅ | — | — |
| B-24 | Expiration | Expired/Urgent/Approaching/Valid/No-date endpoints | ✅ DONE | — | `routes/expiration.py`, `services/expiration_service.py` | — | ✅ | — | — |
| B-25 | Expiration | Expiration summary endpoint | ✅ DONE | — | `routes/expiration.py` | — | ✅ | — | — |
| B-26 | Audit | Audit log (all CRUD events) | ✅ DONE | — | `services/audit.py` | — | ✅ | — | — |
| B-27 | Audit | Audit log list + filters (action, entity) | ✅ DONE | — | `routes/audit_logs.py` | — | ✅ | — | — |
| B-28 | Audit | Audit log date range filter (date_from/date_to) | ✅ DONE | — | `routes/audit_logs.py` | — | ✅ STEP 4 | Low | — |
| B-29 | Audit | AuditLogResponse in schemas/ | ⚠️ PARTIAL | P2 | `routes/audit_logs.py` (inline) | `schemas/audit_log.py` | ❌ | Low | STEP 12 |
| B-30 | User | User model | ⚠️ PARTIAL | P2 | `models/user.py` | migration 0004 | ❌ | Med | STEP 10 |
| B-31 | Auth | User schema | ❌ MISSING | P3 | — | `schemas/user.py` | ❌ | High | STEP 15 |
| B-32 | Auth | Auth routes (login, register, me) | ❌ MISSING | P3 | — | `routes/auth.py` | ❌ | High | STEP 15 |
| B-33 | Auth | JWT / session | ❌ MISSING | P3 | — | `core/security.py` | ❌ | High | STEP 15 |
| B-34 | Auth | Password hashing | ❌ MISSING | P3 | — | `core/security.py` | ❌ | High | STEP 15 |
| B-35 | Auth | Auth middleware / dependency | ❌ MISSING | P3 | — | all routes | ❌ | High | STEP 15 |
| B-36 | Auth | RBAC / authorization | ❌ MISSING | ⏸️ DEFERRED | — | — | ❌ | High | STEP 16 |

---

## DATABASE

| ID | Domain | Feature | Status | Priority | Current | Missing | Risk | Next Action |
|---|---|---|---|---|---|---|---|---|
| D-01 | Migration | 0001 crew_members | ✅ DONE | — | `alembic/versions/0001` | — | — | — |
| D-02 | Migration | 0002 ships/assignments/contracts | ✅ DONE | — | `alembic/versions/0002` | — | — | — |
| D-03 | Migration | 0003 documents/audit_logs | ✅ DONE | — | `alembic/versions/0003` | — | — | — |
| D-04 | Migration | 0004 users table | ❌ MISSING | P2 | — | `alembic/versions/0004` | Med | STEP 10 |
| D-05 | Model | crew_members (28 alan) | ✅ DONE | — | `models/crew_member.py` | — | — | — |
| D-06 | Model | ships | ✅ DONE | — | `models/ship.py` | — | — | — |
| D-07 | Model | ship_crew_assignments | ✅ DONE | — | `models/assignment.py` | — | — | — |
| D-08 | Model | contracts | ✅ DONE | — | `models/contract.py` | — | — | — |
| D-09 | Model | documents (16 alan) | ✅ DONE | — | `models/document.py` | — | — | — |
| D-10 | Model | audit_logs | ✅ DONE | — | `models/audit_log.py` | — | — | — |
| D-11 | Model | users | ⚠️ PARTIAL | P2 | `models/user.py` | migration 0004 | Med | STEP 10 |

---

## FRONTEND

| ID | Domain | Feature | Status | Priority | Current Files | Missing | Test | Risk | Next Action |
|---|---|---|---|---|---|---|---|---|---|
| F-01 | Core | React + Vite setup | ✅ DONE | — | `App.jsx`, `main.jsx` | — | ✅ build | — | — |
| F-02 | Core | App.css design system | ✅ DONE | — | `App.css` (437 satır) | — | ✅ lint | — | — |
| F-03 | Nav | Sidebar/navigation | ⚠️ PARTIAL | P1 | `App.jsx` | Audit sekmesi (Belgeler STEP 6'da eklendi) | ✅ build | Low | STEP 9 |
| F-04 | Dashboard | Basic metrics (crew/ship counts) | ✅ DONE | — | `App.jsx` | — | ✅ build | — | — |
| F-05 | Dashboard | Expiration metrics (expired/urgent/approaching) | ✅ DONE | — | `App.jsx` (/api/expiration/summary) | — | ✅ lint+build | Low | STEP 5A ✅ |
| F-06 | Crew | Crew list | ✅ DONE | — | `App.jsx` | — | ✅ build | — | — |
| F-07 | Crew | Crew create form | ✅ DONE | — | `App.jsx` | — | ✅ build | — | — |
| F-08 | Crew | Crew detail (extended — 9 yeni alan) | ✅ DONE | — | `App.jsx` | — | ✅ lint+build | Low | STEP 5B ✅ |
| F-09 | Crew | Crew search/filter UI | ❌ MISSING | P2 | — | `App.jsx` | ❌ | Low | STEP 5+ |
| F-10 | Ship | Ship list + detail | ✅ DONE | — | `App.jsx` | — | ✅ build | — | — |
| F-11 | Assignment | Assignment list | ✅ DONE | — | `App.jsx` | — | ✅ build | — | — |
| F-12 | Contract | Contract list | ✅ DONE | — | `App.jsx` | — | ✅ build | — | — |
| F-13 | Document | Documents list screen | ✅ DONE | — | `App.jsx` (`renderDocumentsList`) | — | ❓ | — | STEP 6 ✅ |
| F-14 | Document | Document type/status filters | ❌ MISSING | P1 | — | `App.jsx` | ❌ | Low | STEP 6 |
| F-15 | Document | Bulk upload UI (drag & drop) | ❌ MISSING | P1 | — | `App.jsx` | ❌ | Med | **STEP 7** |
| F-16 | Document | Upload result summary (matched/pending/dup) | ❌ MISSING | P1 | — | `App.jsx` | ❌ | Med | STEP 7 |
| F-17 | Document | Pending matching screen | ❌ MISSING | P1 | — | `App.jsx` | ❌ | Med | **STEP 8** |
| F-18 | Document | Manual match dropdown | ❌ MISSING | P1 | — | `App.jsx` | ❌ | Med | STEP 8 |
| F-19 | Audit | Audit log screen | ❌ MISSING | P1 | — | `App.jsx` | ❌ | Low | **STEP 9** |
| F-20 | Audit | Audit filters (action, entity) | ❌ MISSING | P2 | — | `App.jsx` | ❌ | Low | STEP 9 |
| F-21 | Error | User-friendly error states | ⚠️ PARTIAL | P2 | `App.jsx` | Generic mesaj var, detay yok | ❌ | Low | STEP 5+ |
| F-22 | Component | App.jsx component split | ⏸️ DEFERRED | P3 | `App.jsx` (monolitik) | `src/components/` | — | Med | STEP 17 |

---

## TESTS

| ID | Domain | Feature | Status | Priority | File | Count | Next Action |
|---|---|---|---|---|---|---|---|
| T-01 | API | Health, Crew, Ship, Assignment, Contract | ✅ DONE | — | `test_api.py` | 10 | — |
| T-02 | Audit | CRUD audit kayıtları, filtreler | ✅ DONE | — | `test_audit.py` | 11 | — |
| T-03 | Document | Upload, match, dedup, match_status filter | ✅ DONE | — | `test_documents.py` | 5 | — |
| T-04 | Expiration | Tüm kategoriler + boundary + summary | ✅ DONE | — | `test_expiration.py` | 12 | STEP 3 ✅ |
| T-05 | Audit | Date range filter testi | ✅ DONE | — | `test_audit.py` (eklendi) | 3 | STEP 4 |
| T-06 | Error | 404/409/422 error case coverage | ⚠️ PARTIAL | P2 | `test_api.py` | kısmi | STEP 14 |
| T-07 | Document | Download endpoint testi | ❌ MISSING | P2 | `test_documents.py` | 1 | STEP 14 |
| T-08 | Frontend | Birim / entegrasyon testi | ❌ MISSING | P3 | — | — | FUTURE |
| T-09 | Performance | 100 dosya toplu upload | ❌ MISSING | P3 | — | — | FUTURE |

**Toplam mevcut:** `38 passed, 0 failed`

---

## SECURITY

| ID | Domain | Feature | Status | Priority | Next Action |
|---|---|---|---|---|---|
| S-01 | Auth | Authentication | ❌ MISSING | P3 | STEP 15 |
| S-02 | Auth | Authorization / RBAC | ❌ MISSING | ⏸️ DEFERRED | STEP 16 |
| S-03 | Upload | MIME type whitelist | ❌ MISSING | P2 | STEP 11 |
| S-04 | Upload | File size limit | ✅ DONE | — | env config |
| S-05 | Upload | Path traversal protection | ✅ DONE | — | UUID4 filename |
| S-06 | Data | SQL injection | ✅ DONE | — | SQLAlchemy ORM |
| S-07 | Data | Input validation | ✅ DONE | — | Pydantic |
| S-08 | Data | Checksum dedup | ✅ DONE | — | SHA-256 |
| S-09 | Config | Secrets in .env | ✅ DONE | — | .gitignore |
| S-10 | Network | CORS | ⚠️ PARTIAL | P2 | Configurable, geniş |
| S-11 | Network | SSL/HTTPS | ❌ MISSING | 🔮 FUTURE | nginx + Let's Encrypt |
| S-12 | Audit | Complete audit trail | ✅ DONE | — | tüm CRUD kayıtlı |

---

## OPERATIONS

| ID | Domain | Feature | Status | Priority | Next Action |
|---|---|---|---|---|---|
| O-01 | Container | Docker Compose | ✅ DONE | — | — |
| O-02 | Container | Backend Dockerfile | ✅ DONE | — | — |
| O-03 | Container | Frontend Dockerfile | ✅ DONE | — | — |
| O-04 | Config | Environment (.env) | ✅ DONE | — | — |
| O-05 | Storage | Local file storage (`storage/`) | ✅ DONE | — | — |
| O-06 | Deploy | nginx / reverse proxy | ❌ MISSING | 🔮 FUTURE | STEP 20 |
| O-07 | Deploy | SSL certificate | ❌ MISSING | 🔮 FUTURE | STEP 20 |
| O-08 | Monitor | Error tracking (Sentry) | ❌ MISSING | 🔮 FUTURE | — |
| O-09 | Monitor | Metrics (Prometheus/Grafana) | ❌ MISSING | 🔮 FUTURE | — |
| O-10 | Backup | Database backup (pg_dump) | ❌ MISSING | 🔮 FUTURE | — |
| O-11 | CI/CD | GitHub Actions | ❌ MISSING | 🔮 FUTURE | — |

---

## AI / MOBILE

| ID | Domain | Feature | Status | Priority | Notes |
|---|---|---|---|---|---|
| A-01 | AI | `ai/` klasörü | ❓ UNVERIFIED | 🔮 FUTURE | Boş (içerik kontrol edilmedi) |
| A-02 | AI | OCR entegrasyonu | ❌ MISSING | 🔮 FUTURE | — |
| A-03 | AI | Gelişmiş NLP metadata | ❌ MISSING | 🔮 FUTURE | — |
| A-04 | AI | Vector similarity matching | ❌ MISSING | 🔮 FUTURE | SequenceMatcher yerine |
| M-01 | Mobile | `mobile/` klasörü | ❓ UNVERIFIED | 🔮 FUTURE | Boş |
| M-02 | Mobile | React Native / Flutter app | ❌ MISSING | 🔮 FUTURE | API hazır |

---

## LEGACY / PARTIAL WORK RECOVERY

| ID | Feature | Nerede İz Var | Ne Kadar Tamam | Ne Eksik | Öncelik | Risk |
|---|---|---|---|---|---|---|
| L-01 | User model/migration | `models/user.py` var, migration 0004 yok | %30 | Migration, schema, routes, service | P2 | Med |
| L-02 | Frontend Aşama 4 | `App.css` hazır (437 satır), `App.jsx` 165 satır (eski) | %15 | Belgeler, upload, pending, audit, expiration, crew detay | P1 | Med |
| L-03 | AuditLogResponse schema | `audit_logs.py` route içine gömülü | %50 | `schemas/audit_log.py` | P2 | Low |
| L-04 | Error handling | HTTPException var her yerde | %40 | Global exception handler | P2 | Low |
| L-05 | CORS sıkılaştırma | Config var, geniş | %50 | Auth sonrası kısıtlanacak | P2 | Low |

---

## POSSIBLY FORGOTTEN (UNVERIFIED)

| Item | Durum | Kontrol Gerekiyor |
|---|---|---|
| `scripts/` klasörü içeriği | ❓ UNVERIFIED | İçerik hiç kontrol edilmedi |
| `database/` klasörü içeriği | ❓ UNVERIFIED | İçerik hiç kontrol edilmedi |
| `backend/app/run.py` | ❓ UNVERIFIED | `uvicorn` entry point olduğu biliniyor ama test edilmedi |
| `backend/app/db/init_db.py` | ❓ UNVERIFIED | `create_all` kullanımı — production'da çalışıyor mu? |
| Document download endpoint (FileResponse) | ❓ UNVERIFIED | Testte doğrulanmamış (T-07) |
| `storage/` klasörü volume mapping | ❓ UNVERIFIED | Docker compose'da mount var mı? |

---

## OVERALL COMPLETION SUMMARY

```
Backend Core       : ████████████████░░░░  80%  (auth eksik)
Database           : ████████████████░░░░  80%  (users migration eksik)
Frontend           : ███████████░░░░░░░░░  57%  (Belgeler tamamlandı — upload/pending/audit eksik)
Tests              : ████████████████░░░░  75%  (error cases, frontend testleri eksik)
Security           : ████████░░░░░░░░░░░░  40%  (auth, MIME validation eksik)
Operations         : ████████░░░░░░░░░░░░  40%  (local dev hazır, production hazır değil)
AI/Mobile          : ░░░░░░░░░░░░░░░░░░░░   5%  (sadece klasörler var)

TOTAL ESTIMATED    : ███████████░░░░░░░░░  54%  (MVP backend tam, frontend Belgeler ile ilerledi)
```

**Hesaplama notu (2026-08-12 sync):** Frontend yüzdesi, F-01→F-22 arası 22 maddeden (F-22 DEFERRED hariç, 21 madde üzerinden) `DONE = 1.0`, `PARTIAL = 0.5`, `MISSING = 0` ağırlıklandırmasıyla hesaplandı: (11 DONE + 2×0.5 PARTIAL) / 21 ≈ %57. TOTAL ESTIMATED, 7 kategorinin basit ortalamasıdır. Backend/Database/Tests/Security/Operations/AI-Mobile yüzdeleri bu sync'te değişmedi (bu STEP'ler yalnızca frontend'e dokundu).

---

## NEXT RECOMMENDED ACTIONS (Öncelik Sırası)

```
1. STEP 4  — Audit date range filter  (Low risk, ~10 satır) ✅
2. STEP 5  — Frontend 4A  (Med risk, ~190 satır, CSS hazır) ✅
3. STEP 6  — Frontend 4B  (Med risk, ~46 satır — beklenenden küçük, iskelet zaten mevcuttu) ✅
4. STEP 7  — Frontend 4C  (Med-Large, ~200 satır)
5. STEP 8  — Frontend 4D  (Med risk, ~120 satır)
6. STEP 9  — Frontend 4E  (Low-Med, ~80 satır)
7. STEP 10 — User migration 0004  (Med risk, migration dikkat)
8. STEP 11 — MIME validation  (Low risk)
9. STEP 12 — AuditLogResponse schema  (Low risk)
10. STEP 15 — Authentication  (HIGH risk — ayrı, uzun oturum)
```
