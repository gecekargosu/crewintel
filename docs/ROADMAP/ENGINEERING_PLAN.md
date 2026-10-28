# CREWINTEL — ENGINEERING PLAN
> Her önemli özellik için uygulama mühendisliği detayları.
> Bir geliştirici bu belgeyi okuyarak işi nasıl yapacağını anlayabilmeli.

---

## STEP 4 — Audit Log Date Range Filter

**Status:** MISSING · **Priority:** P2 · **Risk:** Low · **Size:** Small

### Requirement
`GET /api/audit-logs/` endpoint'ine `date_from` ve `date_to` query parametreleri eklenmesi. Bu sayede belirli zaman aralığındaki audit olayları filtrelenebilir.

### Architecture
Query parametresi → SQLAlchemy filter → `AuditLog.created_at` sütunu üzerinde aralık sorgusu.

### Files
```
MODIFY: backend/app/api/routes/audit_logs.py
ADD (tests): tests/test_audit.py (2-3 yeni test fonksiyonu)
```

### Implementation Sequence
1. `audit_logs.py` route'una `date_from: date | None` ve `date_to: date | None` parametresi ekle
2. `query.filter(AuditLog.created_at >= date_from)` ve `<= date_to` filtrele
3. `datetime` dönüşümüne dikkat: `date` → `datetime` başlangıç/bitiş (00:00:00 / 23:59:59)
4. Test yaz: iki farklı tarihli log oluştur, aralık filtresini doğrula

### Dependencies
Yok — bağımsız.

### Testing
- `test_audit_log_filter_by_date_range_returns_only_matching_logs`
- `test_audit_log_filter_excludes_logs_outside_date_range`

### Definition of Done
- `GET /api/audit-logs/?date_from=2026-08-01&date_to=2026-08-10` çalışıyor
- Mevcut 38 test bozulmadı
- `git diff --check` PASS

### Safe STOP
`pytest` → 40+ passed, 0 failed

---

## STEP 5 — Frontend 4A: Navigation + Crew Detail + Dashboard Metrics

**Status:** MISSING · **Priority:** P1 · **Risk:** Medium · **Size:** Medium (~190 satır App.jsx değişikliği)

### Requirement
1. Sidebar navigation'a "Belgeler" ve "Audit" sekmeleri ekle
2. Crew detay ekranına 9 yeni alan ekle (birth_place, hometown, marital_status, experience_years, sea_service_months, languages, education_summary, notes, profile_data)
3. Dashboard'a `/api/expiration/summary` verisini çekip belge expiration kartlarını göster

### Architecture
- `App.jsx`'teki `renderPage()` ve `navigation` dizisi genişletilir
- `loadData()` içine `/api/expiration/summary` eklenir
- `renderCrewDetail()` ayrı fonksiyon haline getirilir (inline'dan çıkarılır)

### Files
```
MODIFY: frontend/src/App.jsx
```

### CSS Classes (App.css'te hazır)
- `.card.warning`, `.card.danger` → expiration uyarı kartları
- `.detail-grid` → genişletilmiş crew detay
- `.badge-expired`, `.badge-urgent`, `.badge-approaching` → expiry badge'leri

### Dependencies
App.css (hazır) · `/api/expiration/summary` endpoint (hazır)

### Testing
`oxlint` + `vite build` PASS · Mevcut CRUD ekranları bozulmamış

### Safe STOP
lint ✅ + build ✅

---

## STEP 6 — Frontend 4B: Documents List Screen

**Status:** MISSING · **Priority:** P1 · **Risk:** Medium · **Size:** Medium (~150 satır)

### Requirement
Belgeler ekranı:
- `GET /api/documents/` ile belge listesi
- Filtreler: document_type, match_status, expiry_status
- Her belgede: dosya adı, tür, personel adı (veya "Eşleşmemiş"), expiry badge, indir butonu
- Boş durum gösterimi

### Architecture
```
state: documents[]
filterDocType, filterMatchStatus, filterExpiry

loadDocuments() → GET /api/documents/?...
renderDocumentList() → tablo veya kart listesi
```

### Files
```
MODIFY: frontend/src/App.jsx
```

### CSS Classes (App.css'te hazır)
- `.data-table`, `.data-table th`, `.data-table td`
- `.badge-type-cv`, `.badge-type-passport`, ... (tüm tip badge'leri hazır)
- `.badge-valid`, `.badge-expired`, `.badge-urgent`, `.badge-approaching`
- `.filter-bar`, `.empty`

### Dependencies
STEP 5 tamamlanmış olmalı (navigation "Belgeler" sekmesi)

### Testing
lint + build PASS · Document list API çağrısı çalışıyor

### Safe STOP
lint ✅ + build ✅

---

## STEP 7 — Frontend 4C: Bulk Upload UI

**Status:** MISSING · **Priority:** P1 · **Risk:** Medium-Large · **Size:** ~200 satır

### Requirement
- Dosya sürükle-bırak veya input ile çoklu dosya seçimi
- `POST /api/documents/upload` multipart/form-data
- Yükleme sırasında progress bar
- Sonuç özeti: matched / pending / duplicate / error sayıları
- Her dosya için durum badge'i
- Hata durumunda kullanıcı dostu mesaj (stack trace gösterme)

### Architecture
```
state: uploadFiles[], isUploading, uploadResults[]
drag-over event → dragover class CSS transition
handleFileSelect() → FormData → axios.post('/api/documents/upload')
renderUploadSummary() → upload-summary grid
renderFileList() → file-item list
```

### Files
```
MODIFY: frontend/src/App.jsx
```

### CSS Classes (App.css'te hazır)
- `.upload-zone`, `.upload-zone.drag-over`
- `.upload-progress-bar`, `.upload-progress-fill`
- `.upload-summary`, `.upload-stat.matched/.pending/.duplicate/.error`
- `.file-list`, `.file-item`, `.file-item-name`, `.file-item-status`

### Critical Rule (User stated)
> "YANLIŞ PERSONELE BELGE BAĞLAMAK, EŞLEŞTİRMENİN BAŞARISIZ OLMASINDAN DAHA KÖTÜDÜR."

Eşleşme sonuçlarını backend response'dan al. Frontend'de sahte sonuç üretme.

### Dependencies
STEP 6 tamamlanmış olmalı

### Testing
lint + build PASS · Upload API yanıtı doğru parse ediliyor

### Safe STOP
lint ✅ + build ✅

---

## STEP 8 — Frontend 4D: Pending Matching Screen

**Status:** MISSING · **Priority:** P1 · **Risk:** Medium · **Size:** ~120 satır

### Requirement
- `GET /api/documents/?match_status=pending` ile pending belgeler
- Her pending belge için: dosya adı, tür, güven skoru, "personel seç" dropdown
- Personel dropdown: mevcut crew listesi
- `PUT /api/documents/{id}/match` ile manuel eşleştirme
- Eşleştirme sonrası liste güncellenmeli

### Architecture
```
state: pendingDocs[], allCrew[]
selectedCrewForDoc: {docId: crewId}

renderPendingList() → pending-card bileşeni
handleMatch(docId, crewId) → PUT /api/documents/{id}/match
```

### Files
```
MODIFY: frontend/src/App.jsx
```

### CSS Classes (App.css'te hazır)
- `.pending-card`, `.pending-meta`, `.pending-actions`
- `.confidence-bar`, `.confidence-track`, `.confidence-fill`
- `.badge-pending`, `.badge-matched`

### Dependencies
STEP 6 (Documents list) + STEP 1 (match_status filter — DONE)

### Testing
lint + build PASS · Eşleştirme sonrası belge listede görünmüyor

### Safe STOP
lint ✅ + build ✅

---

## STEP 9 — Frontend 4E: Audit Log Screen

**Status:** MISSING · **Priority:** P1 · **Risk:** Low-Medium · **Size:** ~80 satır

### Requirement
- `GET /api/audit-logs/` ile audit olayları listesi
- Filtreler: action, entity
- Her satırda: zaman, action badge, entity, mesaj
- Sayfalama (offset/limit)

### Architecture
```
state: auditLogs[], auditFilter{action, entity}
loadAuditLogs() → GET /api/audit-logs/?...
renderAuditLog() → .audit-row list
```

### Files
```
MODIFY: frontend/src/App.jsx
```

### CSS Classes (App.css'te hazır)
- `.audit-row`, `.audit-time`, `.audit-message`, `.audit-status`
- `.tabs`, `.tab-btn`, `.tab-btn.active`

### Dependencies
Navigation'da "Audit" sekmesi (STEP 5)

### Testing
lint + build PASS · Audit log listesi görünüyor

### Safe STOP
lint ✅ + build ✅ — **Frontend Aşama 4 TAMAMLANDI**

---

## STEP 10 — User Model Migration (Alembic 0004)

**Status:** MISSING · **Priority:** P2 · **Risk:** Medium · **Size:** Small

### Requirement
`users` tablosunu production database'de oluştur.

### Architecture
Alembic migration 0004, mevcut `User` model'den tablo oluşturur.

```python
# User model alanları (model/user.py'den):
id, email (unique), full_name, role, is_active, created_at, updated_at
```

### Files
```
CREATE: backend/alembic/versions/20260810_0004_add_users_table.py
```

### Implementation Sequence
1. `alembic revision --autogenerate -m "add_users_table"` VEYA manuel migration yaz
2. Migration içeriğini doğrula (sadece users tablosu eklenmeli)
3. Test DB üzerinde çalıştır
4. pytest → 38+ passed

### Critical Warning
Migration zinciri: `0001 → 0002 → 0003 → 0004`
`down_revision` değeri `0003`'ün revision ID'si olmalı.

### Dependencies
Auth (STEP 15) bu migration'a bağlı.

### Testing
`pytest` → 38+ passed, 0 failed

### Safe STOP
Migration dosyası oluştu + pytest PASS (migration tablo oluşturmayı doğrula)

---

## STEP 11 — MIME Type Validation

**Status:** MISSING · **Priority:** P2 · **Risk:** Low · **Size:** Small (~15 satır)

### Requirement
Upload sırasında sadece izin verilen MIME type'ları kabul et.

### Whitelist (öneri)
```
application/pdf
text/plain
application/msword
application/vnd.openxmlformats-officedocument.wordprocessingml.document
image/jpeg
image/png
```

### Files
```
MODIFY: backend/app/services/document_service.py (upload_documents metodu)
```

### Implementation
`upload.content_type` kontrol et → izin verilmeyenler için `HTTP 422`.

### Dependencies
Yok.

---

## STEP 15 — Authentication (JWT)

**Status:** MISSING · **Priority:** P3 · **Risk:** HIGH · **Size:** LARGE

> ⚠️ Bu STEP'e başlamadan önce STEP 10 (User migration) tamamlanmış olmalı.
> Tüm API endpoint'leri etkilenir — mevcut testler kırılır ve güncellenmesi gerekir.

### Architecture
```
POST /api/auth/login    → email + password → JWT token
POST /api/auth/register → (opsiyonel)
GET  /api/auth/me       → current user

Dependency: get_current_user() → tüm route'lara eklenecek
```

### Files
```
CREATE: backend/app/api/routes/auth.py
CREATE: backend/app/schemas/user.py
CREATE: backend/app/core/security.py (password hashing, JWT)
MODIFY: backend/app/main.py (auth router)
MODIFY: backend/requirements.txt (python-jose veya pyjwt, passlib)
MODIFY: tüm route'lar (Depends(get_current_user) ekle)
MODIFY: tüm testler (auth header ekleme)
```

### Risk
- Tüm API'ler değişir → mevcut 38 test kırılır
- Test fixture'larına auth eklemek gerekir
- Migration 0004 şart

### Safe Approach
Ayrı uzun oturumda, parçalı olarak yapılmalı.

---

## GENEL MÜHENDİSLİK KURALLARI

1. **Alembic migration'larını (0001-0003) değiştirme.** Üretim verisi var olabilir.
2. **`document_processing.py` match/parse mantığını gereksiz değiştirme.** Stabil.
3. **`conftest.py`'ye dokunma.** 38 test burada tutunuyor.
4. **Her STEP sonunda `pytest` + `git diff --check` zorunlu.**
5. **Frontend STEP'lerinde `lint` + `build` zorunlu.**
6. **Her STEP'in safe STOP noktasını belgele.**
7. **Bir STEP bitmeden diğerine geçme.**
