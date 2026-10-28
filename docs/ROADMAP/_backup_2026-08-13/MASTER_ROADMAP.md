# CREWINTEL — MASTER ROADMAP
> Tek kaynak proje yol haritası. Tüm geliştirme bu belge üzerinden yönetilir.

**Son güncelleme:** 2026-08-10 | **Mevcut durum:** Backend stabil · STEP 3 tamamlandı · STEP 4 bekliyor

---

## 1. PROJECT MISSION

CREWINTEL, gemi personelinin belgelerini, kontratlarını, atamalarını ve gemi bilgilerini merkezi bir sistemde arşivleyen; belge geçerlilik sürelerini takip eden ve tüm işlemleri denetlenebilir hale getiren bir **Crew Management Platform**'udur.

**Hedef:** Tek kullanıcı, lokal ortam → ileride çok kullanıcılı network ortamı.

---

## 2. CURRENT VERSION

```
Version    : 0.1.x (development)
Stage      : Backend MVP Complete + Frontend Partial
Last STEP  : STEP 3 (Expiration Tests)
Tests      : 38 passed, 0 failed
Auth       : NOT IMPLEMENTED
```

---

## 3. COMPLETED HISTORY

| STEP | Açıklama | Durum | Test |
|---|---|---|---|
| STEP 1 | `match_status` filtresi (`GET /api/documents/?match_status=...`) | ✅ DONE | 26→26 passed |
| STEP 2 | `.bak` + test txt temizliği + `DEVELOPMENT_LOG.md` oluşturma | ✅ DONE | 26 passed |
| STEP 3 | `ExpirationService` test coverage (`test_expiration.py`, 12 test) | ✅ DONE | 26→38 passed |

---

## 4. REMAINING WORK (Sıralı)

### 🟢 SAFE — Küçük, bağımsız, hemen yapılabilir

| STEP | Açıklama | Boyut | Dosyalar |
|---|---|---|---|
| **STEP 4** | Audit log tarih aralığı filtresi (`date_from` / `date_to`) | Small | `audit_logs.py` + 2-3 test |
| **STEP 5** | Frontend 4A — Navigation güncelleme + Crew detail genişletme + Dashboard expiration metrikleri | Medium | `App.jsx` |
| **STEP 6** | Frontend 4B — Documents list ekranı | Medium | `App.jsx` |
| **STEP 7** | Frontend 4C — Toplu belge yükleme UI | Medium-Large | `App.jsx` |
| **STEP 8** | Frontend 4D — Pending eşleşme ekranı | Medium | `App.jsx` |
| **STEP 9** | Frontend 4E — Audit log ekranı | Small-Medium | `App.jsx` |
| **STEP 10** | User model Alembic migration (0004) | Small | `alembic/versions/` |

### 🟡 MONITOR — Orta risk

| STEP | Açıklama | Boyut | Risk |
|---|---|---|---|
| **STEP 11** | MIME type whitelist validation (upload güvenliği) | Small | Düşük |
| **STEP 12** | `AuditLogResponse` şemasını `schemas/` altına taşı | Small | Düşük |
| **STEP 13** | Crew rank/experience_years filtresi backend'e ekle | Small | Düşük |
| **STEP 14** | Error case test coverage genişletme | Medium | Düşük |

### 🔴 HOLD — Büyük, riskli, ayrı planlama gerekli

| STEP | Açıklama | Risk |
|---|---|---|
| **STEP 15** | Authentication (JWT + password hashing + User CRUD) | YÜKSEK — tüm API'ler etkilenir |
| **STEP 16** | Authorization / RBAC | YÜKSEK — STEP 15 gerekir |
| **STEP 17** | Frontend component split (App.jsx → bileşenler) | Orta — STEP 9 sonrası |
| **STEP 18** | Mobile uygulama | FUTURE |
| **STEP 19** | AI/OCR document intelligence | FUTURE |
| **STEP 20** | Deployment (nginx, SSL, production hardening) | FUTURE |
| **STEP 21** | Monitoring / alerting | FUTURE |

---

## 5. DEPENDENCY MAP

```
match_status (DONE)
        ↓
Pending documents API (DONE)
        ↓
Pending UI → STEP 8

User model (exists, no migration)
        ↓
STEP 10: User migration (0004)
        ↓
STEP 15: Auth (JWT, passwords)
        ↓
STEP 16: Authorization / RBAC
        ↓
Network deployment güvenli

Documents (DONE)
        ↓
Document processing (DONE)
        ↓
Document matching (DONE)
        ↓
Expiration tracking (DONE)
        ↓
Dashboard metrics → STEP 5

Audit logging (DONE)
        ↓
Audit date filter → STEP 4
        ↓
Audit UI → STEP 9

App.css (DONE — 437 satır hazır)
        ↓
STEP 5 → STEP 6 → STEP 7 → STEP 8 → STEP 9
(her biri bağımsız, sıralı)
```

---

## 6. PRIORITY SYSTEM

```
P0 — BLOCKING    : Sistemin kullanılmasını engelliyor
P1 — HIGH        : Temel kullanım senaryosu için şart
P2 — MEDIUM      : Önemli ama engelleyici değil
P3 — LOW         : İyileştirme / gelecek
FUTURE           : MVP sonrası
```

---

## 7. TOKEN-SAFE EXECUTION STRATEGY

Her STEP için kurallar:
1. Tek komuta tek STEP
2. STEP sonunda her zaman: `pytest` + `git diff --check`
3. Frontend STEP'leri: `lint` + `build` zorunlu
4. DEVELOPMENT_LOG her STEP sonrası güncellenir
5. Bir STEP'i bitirmeden diğerine geçme
6. Her STEP'in boyutu: max ~150 satır değişiklik (Large için 200)

---

## 8. RELEASE MILESTONES

### M1 — Backend Complete (✅ REACHED)
- Tüm CRUD endpoint'leri
- Document processing pipeline
- Expiration service
- Audit logging
- 38 test

### M2 — Frontend Complete (IN PROGRESS)
- STEP 4 + STEP 5-9 tamamlandığında
- Belgeler ekranı + upload + pending + audit + dashboard

### M3 — Security Ready (PLANNED)
- STEP 10 + STEP 15 + STEP 16 tamamlandığında
- Auth + RBAC

### M4 — Production Ready (FUTURE)
- STEP 20 deployment
- Monitoring
- SSL/nginx

---

## 9. DEFINITION OF DONE

Bir STEP için "DONE" kriterleri:
- [ ] Kod değişikliği tamamlandı
- [ ] `pytest` → 0 failed
- [ ] `git diff --check` → PASS
- [ ] Frontend STEP'i → `lint` + `build` PASS
- [ ] Production koda gereksiz dokunulmadı
- [ ] DEVELOPMENT_LOG güncellendi
- [ ] Sonraki STEP'e geçilmedi (komut beklendi)

---

## 10. FUTURE ROADMAP (MVP Sonrası)

```
MOBILE
  └── React Native veya Flutter — mobile/ klasörü hazırlanmış (boş)

AI / OCR
  └── ai/ klasörü hazırlanmış (boş)
  └── Document intelligence, otomatik alan çıkarma, gelişmiş matching

DEPLOYMENT
  └── deployment/ klasörü hazırlanmış (boş)
  └── nginx, SSL, Docker Swarm/K8s

MONITORING
  └── Sentry, Prometheus/Grafana, log aggregation

NOTIFICATIONS
  └── E-posta/SMS belge bitiş uyarıları

REPORTING
  └── PDF raporlar, CSV export
```
