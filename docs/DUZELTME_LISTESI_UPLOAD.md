# CREWINTEL — Dosya Yükleme & Dönüşüm Düzeltme Listesi
> Tarih: 2026-10-04 · Kapsam: belge yükleme hattı (madde 1–8 kullanıcı talepleri)
> Uygulama sırası: analiz → kod → test → Docker → veri → uygulamalı doğrulama → push

## TESPİT EDİLEN HATALAR (kök nedenler)

### H1 — Frontend dosyaları `.pdf/.txt` dışını SESSİZCE reddediyordu (madde 4, 5, 6)
- **Kök neden:** `App.jsx` → `addStagedFiles()` içinde `ALLOWED_EXT = [".pdf", ".txt"]`.
  JPEG/DOCX/XLSX dosyaları hiçbir hata vermeden listeden eleniyordu; kullanıcı
  "yükledim ama listede çıkmıyor" diyordu.
- **Ek:** reddetme mesajı `lastBatchSummary.detail` alanına yazılıyor ama render'da
  hiç gösterilmiyordu → kullanıcı neden çıkmadığını göremiyordu.
- **Düzeltme:** ALLOWED_EXT 18 formata genişletildi; `detail` mesajı özet alanında
  kırmızı uyarıyla gösteriliyor.

### H2 — Dosya seçim diyaloğu (`accept`) sadece `.pdf,.txt` (madde 6)
- GERMAN SKY klasöründeki PDF/Word/Excel/JPEG dosyaları seçim penceresinde
  görünmediği için "dosyayı atamıyorum" sorunu yaşanıyordu.
- **Düzeltme:** `accept` 18 uzantıya genişletildi.

### H3 — Klasör sürükle-bırak desteklenmiyordu (madde 1, 6)
- `handleDrop` sadece `dataTransfer.files` okuyordu; klasör drop'unda boş geliyordu.
- **Düzeltme:** `webkitGetAsEntry` ile recursive klasör taraması +
  "📁 Klasör Seç" (`webkitdirectory`) butonu (alt klasörler dahil tüm dosyalar).

### H4 — Backend `ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".txt"}` (madde 4, 8)
- JPEG/DOCX/XLSX `415 Unsupported Media Type` ile batch'te "failed" oluyordu.
- **Düzeltme:** 18 uzantı + magic-byte doğrulaması (OLE2/ZIP/JPEG/PNG/PDF imzaları).

### H5 — Hiçbir yerde PDF dönüştürme yoktu (madde 2, 8)
- **Düzeltme:**
  - `convert_to_pdf()` servisi: DOC/DOCX/ODT/RTF/XLS/XLSX/ODS (LibreOffice headless),
    resim (Pillow, A4), TXT (fpdf2 + Türkçe font).
  - **Otomatik dönüşüm:** PDF olmayan her belge upload sırasında PDF'e çevrilip
    arşivde PDF olarak saklanıyor (`store_document_file`), checksum orijinalden.
  - `POST /api/documents/convert` ucu: tek dosya → PDF, çoklu → ZIP indir.
  - UI'da "🔄 PDF'e Çevir" butonu.

### H6 — Resimlerden/ taramalı PDF'lerden metin okunamıyordu (madde 3)
- **Düzeltme:** tesseract OCR (eng+tur) — resimler + metin katmanı olmayan PDF'ler
  (pdf2image + tesseract). Docker'a `tesseract-ocr`, `poppler-utils`, `libreoffice-*`.

### H7 — Eski `.doc/.xls/.rtf` extract edilemiyordu (madde 1, 8)
- **Düzeltme:** LibreOffice ile PDF'e çevirip pypdf ile metin çıkarma; başarısızsa
  fpdf2 fallback.

### H8 — fpdf2 `set_text_direction` AttributeError (düzeltme sırasında bulundu)
- fpdf2'de olmayan API → fallback PDF üretimi patlıyordu; satır kaldırıldı.

### H9 — Test: `.txt` artık PDF olarak saklanıyor (davranış değişikliği)
- `test_download_serves_extension_based_media_type` güncellendi; ilke (tip uzantıdan
  türetilir) korundu, içerik `%PDF` doğrulaması eklendi.

### H10 — Crew listesi `limit=500` ile 422 (seed script)
- API sınırı 200; temizlik script'i crew listesini okuyamıyordu → sayfa sayfa
  `limit=200` ile düzeltildi.

### H11 — Toplu yüklemede `500 Internal Server Error` (madde 4)
- **Kök neden:** bazı PDF/XLSX metinlerinde `\x00` (NUL byte) vardı; PostgreSQL
  `text fields cannot contain NUL` DataError fırlatıyordu → tüm chunk 500 oluyordu
  ve hiçbir belge listeye düşmüyordu ("yükledim ama listede yok" ikinci nedeni).
- **Düzeltme:** `extract_text` sarmalayıcısı tüm kaynaklardan gelen metni NUL'dan
  arındırıyor. 221 dosyalık arşivin chunk2'si bu fix ile yeniden yüklendi.

### H12 — Eşleştirme oranı çok düşüktü (madde 6)
- **Ölçüm (düzeltme öncesi):** 187 belge → **11 eşleşen / 49 inceleme / 127 eşleşmeyen**.
- **Kök nedenler:**
  1. Aday üretimi yalnızca `extract_name` çıktısına bağlıydı; isim çıkarımı çoğu
     belgede gürültü üretiyordu (`"La Autoridad"`, `"Med Cert"`, `"Whatsapp 2026…"`).
  2. Belge **gövdesindeki gerçek personel adı** aday aramasında hiç kullanılmıyordu.
  3. `mehmet cetin` ↔ `mehmet cetiner` gibi sınırıs alt-dize eşleşmesi yanlış aday
     üretiyordu (kelime sınırı yoktu).
- **Düzeltme (`match_engine.py`):**
  - `crew_name_in_text()` — personelin tam adı (normalize, kelime sınırı aralı,
    normal + ters sıra) belge metninde geçiyorsa aday + `text_name` (90) sinyali.
  - `text_name_parts` (45) — ad ve soyad metinde ayrı ayrı geçiyorsa (bitişik değil)
    → inceleme eşiğini aşar, auto-match etmez.
  - `filename_full` 45→50 (dosya adında ≥%50 aday token örtüşmesi).
  - Token fuzzy eşiği 0.80 → 0.72 (`ALI`/`ALY` varyasyonları kaçmıyordu).
- **Sonuç (aynı 187 belge, aynı motorla yeniden işlendi):**
  **58 eşleşen / 25 inceleme / 104 eşleşmeyen** (11 → 58, **5.3x**).
- **Tavan analizi:** 187 belgenin yalnızca 71'inde listedeki 22 personelden birinin
  adı geçiyor (49 tam + 8 kısmi + 14 sadece dosya adında). Kalan 104 belgede
  roster'daki hiç kimse anılmıyor → personel listesine eklenmeden eşleştirilemez.
  İncelemedeki 25 belge dosya-adı kanıtına sahip; manuel onayla eşleştirilebilir.

### H13 — Eski `.doc/.xls` + OCR sonrası NUL/bayt artıkları (madde 3, 8)
- LibreOffice/OCR çıktısı bazı belgelerde ikili artık taşıyordu → H11 ile birlikte
  temizleniyor.

## DOĞRULANAN UYGULAMALI TESTLER
1. Lokal: ck örnekleri validate/extract/convert (docx47.9K metin, xlsx2K, jpeg→PDF OK)
2. Docker: `COC.jpeg` → OCR metin OK · `scanned.pdf` (taramalı) → OCR OK ·
   `contract.docx` → LibreOffice 164KB PDF OK
3. `pytest tests/` → **282 passed, 2 skipped**
4. `oxlint` 0 hata · `vite build` OK5. GERMAN SKY temizlik: documents 0, ships 1 (MV GERMAN SKY), crew 22 (gerçek isimler)
6. ck toplu yükleme: 221 dosya (97 pdf, 64 jpeg, 31 xlsx, 20 docx, 5 jpg, 4 jfif)
7. Match motoru yeniden işleyiş: **58 matched / 25 review / 104 unmatched**
   (örn. `MLC CONTRACT FOR BOSUN PABIT SHARMA.xlsx` → crew#166, 165 puan;
   `Panama COC 2.12.2030.pdf` → crew#176, 90 puan — metin içi tam isim)
8. Yüklenemeyen 3 dosya → **H14 ile çözüldü** (artık üçü de yükleniyor):
   `Afiq Baxsiyev evraklar pdf (1).pdf` (51MB), `Documents for Ch Off Yousef.pdf`
   (23MB), `PANAMA MEDICAL CERT.pdf` (aslında JPEG — uzantısı düzeltildi).

### H14 — 3 dosya kalıcı olarak reddediliyordu (boyut + uzantı sahteliği)
- **Kök nedenler:**
  1. `MAX_UPLOAD_SIZE = 20MB` (validate_upload) ve `max_upload_size_mb = 25`
     (batch) — 51MB ve 23MB'lık gerçek arşiv taramaları 413 ile düşüyordu.
  2. `PANAMA MEDICAL CERT.pdf` içeriği JPEG (`FFD8 FFE0 JFIF`) → magic-byte
     415 ile reddediyordu; dosya aslında yanlış adlandırılmış geçerli bir görsel.
- **Düzeltme:**
  - Limitler **100MB**'a çekildi: `MAX_UPLOAD_SIZE`, `max_upload_size_mb`,
    `docker-compose MAX_UPLOAD_SIZE_MB`, `.env.example` ×2, `installer/setup.ps1`,
    `frontend/nginx.conf client_max_body_size 100m` (hepsi aynı değer).
  - `validate_upload()` artık içerik **izin verilen başka bir formata** aitse
    reddetmiyor, uzantıyı içeriğe göre düzeltip geri döner (`mislabeled.pdf`
    → `mislabeled.jpg`). Sahte/hiçbir formata uymayan içerik yine 415.
- **Uygulamalı doğrulama (canlı API):** üçü de `HTTP 201`:
  `PANAMA MEDICAL CERT.jpg` (146KB), `Documents for Ch Off Yousef.pdf` (23MB),
  `Afiq Baxsiyev evraklar pdf (1).pdf` (51MB → crew#180, **165 puanla eşleşti**).
- **Test:** `test_upload_mislabeled_but_valid_content_fixes_extension` ve
  `test_upload_still_rejects_content_matching_no_known_type` eklendi → 284 passed.

## DOCKER UPGRADE (backend Dockerfile)
- `tesseract-ocr tesseract-ocr-eng tesseract-ocr-tur` — OCR
- `libreoffice-writer libreoffice-calc` — DOC/DOCX/XLS/XLSX → PDF
- `poppler-utils` — pdftotext / pdf2image
- `fonts-liberation` — PDF font çıktıları
- Python: `python-docx openpyxl Pillow pytesseract pdf2image fpdf2`
