# CREWINTEL — FAZ ROADMAP (Checkpoint Master List)

> **BU DOSYA TEK GERÇEK KAYNAKTIR.**
> Hangi AI aracıyla (Claude, ChatGPT, Antigravity, vb.) çalışırsan çalış,
> önce bu dosyayı ve `docs/DEVELOPMENT_LOG.md`'nin SON kayıtlarını oku.
> Bir checkpoint'in yanında ✅ yoksa, o checkpoint TAMAMLANMAMIŞTIR.

**Son güncelleme:** 2026-08-17
**Oluşturan:** Antigravity — C:\CREWINTEL gerçek kodu + git status + terminal çıktıları ile doğrulandı
**Referans:** Kullanıcının FAZ_ROADMAP taslağı (2026-08-16, ChatGPT mimari gözden geçirmesi)

---

## ÇALIŞMA MODELİ (her checkpoint için aynı)

1. Kullanıcı "CHECKPOINT X'e başla" der
2. AI kodu/dosyayı hazırlar, tam talimatlarla sunar
3. Kullanıcı kopyalar, gerekiyorsa `docker compose up -d --build` çalıştırır
4. Terminal çıktısını AI'ye geri gönderir
5. AI doğrular, `DEVELOPMENT_LOG.md`'ye kaydeder, bu dosyada `✅` işaretler
6. Bir checkpoint bitmeden bir sonrakine geçilmez

**Token/oturum sınırı:** Mevcut checkpoint bitirilir ya da güvenli ara noktada durulup
"NEXT CHECKPOINT: X" notu bırakılır. Yeni oturumda bu dosya + DEVELOPMENT_LOG son kayıtları okunur.

---

## CURRENT VERIFIED STATE

**Son doğrulama tarihi: 2026-08-17**

> [!IMPORTANT]
> Aşağıdaki bilgiler gerçek terminal çıktıları ve C:\CREWINTEL kodu ile doğrulanmıştır.
> Eski raporlar, ChatGPT mesajları veya AI tahminleri değil.

### Backend
| Konu | Durum | Kaynak |
|---|---|---|
| `docker compose run --rm backend pytest -q` | ✅ **13 passed in 1.67s** | Koddan doğrulandı (BUG-2 fix sonrası) |
| `backend/pytest.ini` | ✅ Mevcut (`pythonpath = .`) | Koddan doğrulandı |
| `pytest.ini` (kök dizin) | ✅ Mevcut (`testpaths = tests`, `pythonpath = backend`) | Koddan doğrulandı |
| Docker backend build | ✅ Başarılı (image build + container start) | Kullanıcı terminal çıktısı |
| Docker backend start | ✅ Aktif | Kullanıcı terminal çıktısı |

### Frontend
| Konu | Durum | Kaynak |
|---|---|---|
| `npm run lint` (oxlint) | ✅ **0 warnings, 0 errors** | Kullanıcı terminal çıktısı |
| `App.jsx` satır sayısı | 486 satır | Koddan doğrulandı |
| Bulk upload UI (7B) | ✅ Kodda mevcut | App.jsx incelendi |

### Entegrasyon Testleri (Host, .venv)
| Konu | Durum | Kaynak |
|---|---|---|
| `python -m pytest tests/ -q` | ✅ **41 passed, 0 failed** | BUG-2 fix sonrası doğrulandı |

### Git
| Konu | Durum |
|---|---|
| Toplam commit sayısı | 4 commit |
| Son commit | `a2d2368 checkpoint before crew document auto matching` |
| Uncommitted modified files | 5 dosya: `documents.py`, `schemas/document.py`, `document_service.py`, `DEVELOPMENT_LOG.md`, `App.jsx` |
| Untracked files (storage hariç) | 30+ dosya (backup, handoff zip, corrupted backup'lar) |

> [!WARNING]
> STEP 1-7B arasındaki tüm çalışma **commit edilmemiş** durumda. CHECKPOINT D bu yüzden kritik.

### ✅ BUG-2 FIX — Audit Log date_from/date_to Timezone
**Durum:** TAMAMLANDI (2026-08-17)
**Değişiklik:** `backend/app/models/audit_log.py` — `created_at` default'u naive UTC'den local time'a değiştirildi (2 satır)
**Doğrulama:** Host 41 passed + Docker 13 passed = **54 passed, 0 failed** ✅

### Tamamlanmış Kod Değişiklikleri (uncommitted)
Gerçek `git diff --stat` çıktısından:
- `backend/app/api/routes/documents.py` — 4 satır değişiklik (STEP 1: match_status filter)
- `backend/app/schemas/document.py` — 1 satır ekleme
- `backend/app/services/document_service.py` — 23 satır değişiklik (BUG-1 + STEP 7B duplicate logic)
- `docs/DEVELOPMENT_LOG.md` — 3488 satır ekleme (tüm STEP 1-7B kayıtları)
- `frontend/src/App.jsx` — 128 satır değişiklik (net, STEP 5A/5B/6/7A/7B tümü)

### Önemli Dosya Durumu
| Dosya | Boyut | Son Değişiklik | Durum |
|---|---|---|---|
| `document_processing.py` | 8931 bytes | 2026-08-15 02:11 | ✅ Aktif, stabil |
| `document_service.py` | 9004 bytes | 2026-08-15 23:30 | ✅ Aktif, BUG-1 fix dahil |
| `App.jsx` | 486 satır / 25819 byte | 2026-08-14 | ✅ Aktif, 7B-09 + BUG-1 |
| `document_processing.py.bak` + diğer backup'lar | 5 adet | 2026-08-14/15 | ⚠️ Temizlenmeli (CHECKPOINT D) |

---

## 🔴 AKTİF CHECKPOINT'LER (önce bunlar bitmeli)

### ✅ CHECKPOINT B-devam — Backend Test Doğrulama
**Durum:** TAMAMLANDI
**Doğrulama:** `docker compose run --rm backend pytest -q` → **13 passed** (Docker unit tests)
**Not:** `backend/pytest.ini` oluşturuldu. Docker build + start başarılı.

---

### ✅ CHECKPOINT C — Frontend Lint Doğrulama
**Durum:** TAMAMLANDI
**Doğrulama:** `cd frontend && npm run lint` → **0 warnings, 0 errors**

---

### ⏳ CHECKPOINT D — Güvenli Git Checkpoint
**Durum:** BEKLEMEDE — sıradaki commit checkpoint
**Amaç:** Tüm uncommitted değişiklikleri (STEP 1-7B + BUG-1 + BUG-2) tek commit ile kayıt altına almak.

**Commit edilecek dosyalar (modified):**
- `backend/app/api/routes/documents.py` (STEP 1: match_status filter)
- `backend/app/schemas/document.py` (STEP 1)
- `backend/app/services/document_service.py` (BUG-1 fix + STEP 7B)
- `backend/app/models/audit_log.py` (BUG-2 fix)
- `docs/DEVELOPMENT_LOG.md` (tüm STEP kayıtları)
- `frontend/src/App.jsx` (STEP 5A/5B/6/7A/7B)

**Untracked (kullanıcı onayıyla `.gitignore`'a eklenecek):**
- `backend/app/services/document_processing.py.*` (backup/corrupted dosyalar)
- `backend/pytest.ini`
- `CREWINTEL_HANDOFF*`, `_RECOVERY_*`, `*.zip`, `*.txt` (handoff dosyaları)

**Commit mesajı:** `feat: STEP 1-7B + BUG-1 + BUG-2 — match_status, upload UI, audit fix`

**Kabul kriterleri:**
- `git status` → modified: 0, staging temiz
- `python -m pytest tests/ -q` → 41 passed, 0 failed
- `docker compose run --rm backend pytest -q` → 13 passed, 0 failed

---

### ✅ CHECKPOINT E — STEP 8A Kapsam Kesinleşti
**Durum:** TAMAMLANDI (kod değişikliği yok — mimari analiz)
**Sonuç:** 8A alt checkpoint'leri ve 9+1 test senaryosu kesinleşti. Detaylar aşağıda STEP 8A bölümünde.

---

## STEP 8A — Belge Eşleştirme Motoru (Match Engine)

> **Sistemin kalbi.** 10.000 belgeyi doğru kişiye bağlayamazsak diğer her şeyin anlamı azalır.
> Backend-only, algoritmik, kendi başına test edilebilir.
> STEP 8B (UI) bu checkpoint'in çıktısına bağımlıdır.

### Mevcut Match Engine Durumu (koddan doğrulandı)

**`match_crew()` fonksiyonu — `backend/app/services/document_processing.py`:**

```
Mevcut Eşleştirme Zinciri:
  1. Passport number exact match → +100 puan, eşleşmezse ELEME
  2. Seaman book number exact match → +100 puan, eşleşmezse ELEME
  3. Email exact match → +70 puan
  4. İsim fuzzy match (SequenceMatcher):
     ≥ 0.999 → +95 puan
     ≥ 0.98  → +75 puan
     ≥ 0.80  → +45 puan
  5. Date of birth exact match → +30 puan

Karar Mantığı:
  score == 0           → "unmatched"
  top_score - 2nd < 20 → "pending" (belirsiz)
  score ≥ 90           → "matched"
  score < 90           → "pending"
```

**Performans sorunu (koddan doğrulandı):**
`candidates = session.query(CrewMember).all()` — her belge yüklemesinde **TÜM** personeli belleğe çekiyor.
2000 personel × 10000 belge = kritik ölçek sorunu.

### Hedef Mimari vs Mevcut

| Katman | Mevcut | Hedef (8A sonrası) |
|---|---|---|
| Passport exact | ✅ Var | ✅ Korunuyor |
| Seaman book exact | ✅ Var | ✅ Korunuyor |
| Email exact | ✅ Var | ✅ Korunuyor |
| Ad+Soyad+DOB üçlü | ⚠️ Ayrı ayrı, puanlı | ✅ Üçlü kombinasyon güçlendirilecek |
| Fuzzy name (rapidfuzz) | ❌ Sadece SequenceMatcher | ✅ rapidfuzz eklenecek |
| Dosya adı hint | ⚠️ `extract_name()` fallback olarak var | ✅ Korunuyor, net belgeleniyor |
| Confidence banding | ⚠️ Sadece ≥90 auto | ✅ 95-100 auto / 75-94 review / <75 pending |
| SQL optimizasyon | ❌ .all() | ✅ Indexed SQL filtering |

### 8A Checkpoint'leri

- [ ] **8A-01** — Mevcut `match_crew()` kodunu analiz et + dokümante et (KOD DEĞİŞİKLİĞİ YOK)
- [ ] **8A-02** — Confidence banding: 95-100 → auto / 75-94 → review-flag / <75 → pending
- [ ] **8A-03** — Ambiguity threshold parametrik hale getir: mevcut <20 → <15 (konfigüre edilebilir)
- [ ] **8A-04** — `rapidfuzz` entegrasyonu (requirements.txt'e bağımlılık)
- [ ] **8A-05** — SQL optimizasyonu: `.all()` → indexed SQL filtering
- [ ] **8A-06** — Match-specific testler (9+1 senaryo — aşağıya bak)
- [ ] **8A-07** — DEVELOPMENT_LOG kaydı + Docker validation

**Test senaryoları (mevcut `match_crew()` kod yollarından türetildi — 9 temel + 1 rapidfuzz):**
```
# Güçlü kimlik eşleştirme
test_match_by_passport_exact()           # passport +100, ≥90 → matched
test_match_by_seaman_book_exact()        # seaman_book +100, ≥90 → matched
test_wrong_passport_eliminates_candidate()  # yanlış passport → ELEME

# Orta güç eşleştirme
test_match_by_email_only()               # email +70, <90 → pending
test_match_by_name_high_similarity()     # ≥0.999 → +95, ≥90 → matched
test_match_by_name_medium_similarity()   # ≥0.98 → +75, <90 → pending
test_match_by_name_and_dob()             # +45+30=75, <90 → pending

# Belirsiz / eşleşmez
test_unmatched_no_matching_info()        # score=0 → unmatched
test_pending_ambiguous_two_close()       # top - 2nd < threshold → pending

# rapidfuzz (8A-04 sonrası eklenir)
test_rapidfuzz_tolerates_name_typo()     # "KAYAA" ≈ "KAYA" → still matches
```

**Kabul kriterleri:**
- `python -m pytest tests/ -q` → 0 failed (mevcut 41 + yeni 9 test = ≥50)
- `docker compose run --rm backend pytest -q` → 13 passed (unit testler korunur)
- `rapidfuzz` requirements.txt'te ve Docker build başarılı
- Confidence banding çalışıyor, `.env` üzerinden konfigüre edilebilir

**Riskler:**
- `rapidfuzz` SequenceMatcher threshold'ları ile çelişebilir → mevcut testler regression guard
- SQL optimizasyonu dikkatli test edilmeli (SQLite vs PostgreSQL davranış farkı)

---

## STEP 8B — Pending Eşleşme Ekranı (UI)

> 8A'nın ürettiği veriyi gösteren frontend katmanı. 8A tamamlanmadan başlanmaz.

- [ ] **8B-01** — Frontend: Pending ekranı sidebar'a ekleme, temel liste (GET /api/documents/?match_status=pending)
- [ ] **8B-02** — Frontend: Her pending belge için aday listesi (isim + confidence %) gösterimi
- [ ] **8B-03** — Frontend: "Bu personele ata" butonu (mevcut `PUT /{id}/match` endpoint kullanılır — yeni endpoint gerekmez)
- [ ] **8B-04** — Validation + DEVELOPMENT_LOG kaydı

---

## STEP 9 — Audit Log Ekranı

> Backend hazır (GET /api/audit-logs/ + date_from/date_to filtresi). Küçük frontend işi.

- [ ] **9-01** — Frontend: Audit log listesi ekranı, sidebar'a ekleme
- [ ] **9-02** — Filtreleme UI (tarih aralığı — backend zaten destekliyor)
- [ ] **9-03** — Validation + log kaydı

---

## STEP 10A — Temel Personel Filtreleri + Pagination

> **Match Engine'den BAĞIMSIZ.** 8A tamamlanmadan başlanabilir.
> Mevcut CrewMember model alanlarını kullanır — yeni tablo veya migration gerektirmez.

**Mevcut filtreler (crew.py, koddan doğrulandı):** first_name, last_name, position, nationality, status, ship_id, offset/limit (max 100)

**Eklenecek — Model alanı mevcut, filtrede yok:**
- `rank` (String 100) — ilike filtre
- `languages` (Text) — ilike filtre
- `experience_years_min` (Integer) — >= filtre
- `sea_service_months_min` (Integer) — >= filtre

**Pagination:**
- `limit` max 100 → 200'e yükselt

- [x] **10A-01** — Backend: rank, languages, experience_years_min, sea_service_months_min filtreleri
- [x] **10A-02** — Backend: pagination limit artırma (100 → 200)
- [x] **10A-03** — Backend: testler (16 yeni test, `tests/test_crew_filtering.py`)
- [x] **10A-03b** — Backend: `crew_member.py` schema eksikliği giderildi (languages/experience vb. Create/Update'e eklendi)
- [x] **10A-04** — Frontend: temel filtre çubuğu UI (collapsible panel, 7 filtre, aktif filtre badge)
- [x] **10A-05** — Frontend: filtre state + API bağlama (loadCrew, resetCrewFilters, Enter desteği)
- [ ] **10A-06** — Validation + DEVELOPMENT_LOG kaydı — ✅ Tamamlandı (lint 0 error, build ✅, 57 test ✅)

---

## STEP 10B — Belge/Sözleşme Durumu Filtreleri

> **Bağımlılık var.** Documents JOIN + ExpirationService gerektirir. STEP 8A + 10A sonrası.
> STEP 13 (rank→belge şeması) tamamlanmadan "eksik belge" filtresi tam çalışmaz.

**Filtreler:**
- `contract_status` — aktif/biten/yaklaşan sözleşme (contracts JOIN)
- `contract_expiring_days` — N gün içinde biten sözleşme
- `passport_expiry_status` — expired/urgent/approaching (documents JOIN + expiration)
- `seaman_book_expiry_status` — aynı
- `has_no_documents` — hiç belgesi olmayan personel (basit COUNT check)
- `document_type_missing` — belirli belge türü eksik (STEP 13'e bağımlı)
- `completeness_pct_max` — bütünlük yüzdesi < N (STEP 13'e bağımlı)

- [ ] **10B-01** — Backend: contract_status + contract_expiring_days filtresi
- [ ] **10B-02** — Backend: passport/seaman_book expiry filtresi (documents JOIN)
- [ ] **10B-03** — Backend: has_no_documents basit filtresi
- [ ] **10B-04** — Backend: testler
- [ ] **10B-05** — Frontend: gelişmiş filtre paneli
- [ ] **10B-06** — Validation + log kaydı

> **Not:** `document_type_missing` ve `completeness_pct` STEP 13 tamamlanana kadar eklenmez.

---

## STEP 11 — Asenkron Upload Pipeline

> OCR'dan ÖNCE zorunlu. Senkron upload 100+ dosyada timeout riski taşıyor.

- [ ] **11-01** — Mimari karar: Celery+Redis mi, FastAPI BackgroundTasks mi? (kod değil, analiz)
- [ ] **11-02** — `docker-compose.yml`'e gerekli servis ekleme
- [ ] **11-03** — Backend: Upload endpoint → "kaydet + kuyruğa at" (senkron işlemi kuyruğa taşı)
- [ ] **11-04** — Backend: Document modeline `processing_status` alanı (queued/processing/done/failed) — **migration gerekir**
- [ ] **11-05** — Frontend: Upload sonrası "işleniyor" polling
- [ ] **11-06** — Yük testi: 100+ dosya aynı anda
- [ ] **11-07** — Validation + log kaydı

---

## STEP 12 — OCR Entegrasyonu

> STEP 11'e bağımlıdır. Taranmış PDF'ler için metin çıkarma.

- [ ] **12-01** — Backend Dockerfile'a Tesseract ekleme
- [ ] **12-02** — `pytesseract` + görüntü işleme fonksiyonu
- [ ] **12-03** — `document_processing.py`'ye entegrasyon (metin çıkaramazsa OCR fallback)
- [ ] **12-04** — Test: gerçek taranmış belge ile
- [ ] **12-05** — Validation + log kaydı

---

## STEP 13 — Rank → Gerekli Belge Şeması

> STEP 14'ün önkoşulu. Bağımsız, kendi başına değer üretir.

- [ ] **13-01** — Yeni tablo: `document_requirements` (rank_category, required_doc_type, is_mandatory) — **migration**
- [ ] **13-02** — Backend: CRUD endpoint'leri
- [ ] **13-03** — Seed data: temel rank'lar için başlangıç gereksinimleri (Kaptan, Vardiya Zabit, Makine vb.)
- [ ] **13-04** — Validation + log kaydı

---

## STEP 14 — Eksik Belge Sistemi

> STEP 13'e bağımlıdır.

- [ ] **14-01** — Backend: Personel bazında "eksik belge" hesaplama fonksiyonu
- [ ] **14-02** — Frontend: Personel detay ekranına "Eksik Belgeler" bölümü
- [ ] **14-03** — Dashboard: "Eksik belgeli personel sayısı" kartı
- [ ] **14-04** — Validation + log kaydı

---

## STEP 15 — Gelişmiş Belge Türü Tanıma

> OCR sonrasında anlamlı. Gerçek ihtiyaca göre scope netleşecek.

- [ ] **15-01** — Mevcut regex tespitinin doğruluğunu ölç (kaç belge "other" düşüyor?)
- [ ] **15-02** — `seaman_book` belge tipi ekle (şu an model ve processing.py'de yok)
- [ ] **15-03** — Gerekirse sınıflandırma katmanı (ihtiyaca göre planlanacak)

---

## STEP 16 — Performans / Ölçekleme

> Sürekli, ama STEP 10'dan itibaren düşünülüyor. Somut checkpoint'ler.

- [ ] **16-01** — Database index kontrolü (passport_number, seaman_book_number için index eksik)
- [ ] **16-02** — `pg_trgm` extension ile fuzzy isim arama (opsiyonel)
- [ ] **16-03** — Yük testi: 2000 personel + 10000 belge sahte veri ile

---

## STEP 17 — Mobil Uygulama

> Büyük, kendi alt-roadmap'ini gerektirecek. Başlık olarak duruyor.

- [ ] Bu FAZ'a gelince ayrı `MOBILE_ROADMAP.md` açılacak.

---

## SIRA (kesinleşmiş — 2026-08-17)

```
✅ CHECKPOINT B-devam  (13 Docker unit tests)
✅ CHECKPOINT C        (lint 0 errors)
✅ BUG-2 FIX           (54 passed, 0 failed)
✅ CHECKPOINT E        (8A scope kesinleşti)
⏳ CHECKPOINT D        ← ŞU AN BURASI (git commit)
        ↓
STEP 10A (Temel filtreler — 8A'dan bağımsız, hemen başlanabilir)
        ↓
STEP 8A  (Match Engine — backend, sistemin kalbi)
        ↓
STEP 8B  (Pending Eşleşme UI — 8A'ya bağımlı)
        ↓
STEP 9   (Audit Log UI — küçük, 8B ile paralel yapılabilir)
        ↓
STEP 10B (Belge/Sözleşme filtreleri — 8A + 10A sonrası)
        ↓
STEP 11  (Asenkron Pipeline — OCR'dan önce ZORUNLU)
        ↓
STEP 12  (OCR)
        ↓
STEP 13 → STEP 14 (Rank şeması → Eksik belge — birbirine bağımlı)
        ↓
STEP 15  (Gelişmiş belge tanıma)
        ↓
STEP 16  (Performans / Ölçekleme)
        ↓
STEP 17  (Mobil)
```

**Bağımsızlık notu:**
- STEP 10A, STEP 8A beklemeden başlanabilir
- STEP 9 (Audit Log UI), STEP 8A ile paralel yürütülebilir
- STEP 10B, STEP 8A + 10A'dan sonra gelir

---

## DİĞER AI ARAÇLARI İÇİN NOT

Bu checkpoint'lerden birini ChatGPT veya başka bir AI ile yaparsan:

1. Bu dosyayı ona ver
2. Yaptığı checkpoint'i `DEVELOPMENT_LOG.md`'ye aynı formatta (mevcut kayıtlara bak) yazdır
3. Bu dosyada `[ ]` → `✅` yap
4. Bana geri döndüğünde "şu checkpoint'i X aracıyla yaptım" de — gerçek kodu inceleyip doğrularım

---

## TEST ORTAMI NOTU (doğrulanmış — 2026-08-17)

**İki ayrı test suite — birbirini tamamlar, çelişmez:**

| Suite | Konum | Komut | Sayı | Kapsam |
|---|---|---|---|---|
| Integration | `tests/` (root) | `.venv/Scripts/python.exe -m pytest tests/ -q` | **41** | HTTP endpoint, DB, audit, upload |
| Unit | `backend/tests/` | `docker compose run --rm backend pytest -q` | **13** | normalize, match_crew, extract_name |
| **Toplam** | | | **70 passed, 0 failed** | |

**STEP 10A backend sonrası baseline (2026-08-17):** 70 passed, 0 failed ✅

Çalışma ortamı farkı:
- Docker container: sadece `backend/` kopyalanıyor → `backend/tests/` görünür (13 unit test)
- Host `.venv`: root `pytest.ini` kullanılıyor → `tests/` görünür (41 integration test)

---

## MATCH ENGINE (STEP 8A) — MEVCUT vs HEDEF KARŞILAŞTIRMA

### Mevcut `match_crew()` Kodu (doğrulanmış, 2026-08-17)

```python
# document_processing.py, satır 215-303
candidates = session.query(CrewMember).all()  # ← KRİTİK PERFORMANS SORUNU

for crew in candidates:
    score = 0
    # Passport: exact match → +100, eşleşmezse continue (ELEME)
    # Seaman book: exact match → +100, eşleşmezse continue (ELEME)
    # Email: exact match → +70
    # İsim fuzzy (SequenceMatcher):
    #   ≥ 0.999 → +95 | ≥ 0.98 → +75 | ≥ 0.80 → +45
    # DOB: exact match → +30

# Karar: score=0 → unmatched | top-2nd < 20 → pending | ≥90 → matched
```

### Hedef (8A sonrası)

| Değişim | Önce | Sonra |
|---|---|---|
| SQL sorgusu | `session.query(CrewMember).all()` | SQL indexed filtering |
| Fuzzy lib | difflib.SequenceMatcher | rapidfuzz.token_sort_ratio |
| Confidence | ≥90 auto / <90 pending | 95-100 auto / 75-94 review / <75 pending |
| Ambiguity threshold | <20 puan fark | <15 puan fark (parametrik) |
| Test kapsamı | 5 test (doküman upload odaklı) | +9 match-specific test (+1 rapidfuzz sonrası) |

---

*Roadmap sonu — C:\CREWINTEL gerçek kodu ile doğrulanmış. Tahmin veya eski rapor bilgisi yok.*
