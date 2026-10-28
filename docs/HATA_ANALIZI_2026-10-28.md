# Hata Analizi ve Düzeltme Raporu — 28.10.2026

Bu rapor, programın **kullanıcı gibi baştan sona** denenmesiyle (tarayıcıda
gerçek tıklamalar, gerçek hesapla giriş, tüm menüler, formlar, filtreler) ve
kod incelemesiyle bulunan sorunları, yapılan düzeltmeleri ve kalan bilinen
eksikleri listeler.

**Test ortamı:** Docker Compose (postgres 17 + backend FastAPI + frontend nginx),
gerçek veritabanı kopyası (22 personel, 1 gemi, 25 belge, 8 kullanıcı),
tarayıcı 1440×900 ve 601×900 (dar ekran) çözünürlüklerinde.

---

## 1. Kritik hatalar (programı durduruyordu)

### H1 — Backend yeniden derlenince hiç açılmıyordu (Alembic revizyonu)

- **Belirti:** `docker compose build backend && up -d` sonrası konteyner
  `Restarting (255)` döngüsüne giriyor; günlükte
  `FAILED: Can't locate revision identified by '3b90f6112c93'`.
- **Sebep:** Veritabanının `alembic_version` tablosu, kodda artık bulunmayan bir
  revizyona işaret ediyordu (silinmiş bir migration). `alembic upgrade head`
  bu yüzden hiç çalışmıyordu.
- **Düzeltme:** Şema kontrol edildi (22 tablo, 0001–0010 migration'larının
  tamamı mevcut) ve sürüm gerçek başa çekildi:
  `UPDATE alembic_version SET version_num='20260818_0010';`
  Ardından servis sağlıklı açıldı (`/health` → healthy).
- **Not:** Temiz kurulumda bu sorun oluşmaz (boş veritabanı 0001'den başlar).
  Yine de `KURULUM/04-SORUN-GIDERME.md` içine çözüm eklendi.
- **Kod iyileştirme önerisi (yapılmadı):** `alembic upgrade` başarısız olduğunda
  konteynerin sonsuz restart yerine tek seferlik anlaşılır hata verip durması.

### H2 — Daraltılmış menüde ikonlar görünmüyordu (menü kullanılamıyordu)

- **Belirti:** Sol menü daraltıldığında (88 px) tüm menü öğeleri **görünmez**
  oluyor; sadece logo ve alt taraftaki düğme kalıyordu. Kullanıcı bu durumda
  hiçbir ekrana geçemiyordu.
- **Sebep:** `.nav-item` flex kabında SVG ikonlar `flex-shrink` nedeniyle
  **0 piksel genişliğe** büzülüyordu (ölçüm: ikon 22 px yerine 0×21).
  Ayrıca daraltılmış menüde ipucu (tooltip) `overflow:hidden` ile kırpılıyordu.
- **Düzeltme (`frontend/src/App.css`):**
  - `.nav-item svg, .menu-button svg { flex: 0 0 auto; width: 22px; height: 22px; }`
  - `.sidebar.closed .nav-item { width:100%; min-width:64px; min-height:46px; overflow:visible; }`
  - Daraltılmış menüde kenar boşlukları düzenlendi.
- **Doğrulama:** Daraltılmış menüde ikon 21×21, düğme 63×49; tıklanınca sayfa
  değişiyor. Ekran görüntüsüyle de kontrol edildi.

---

## 2. İşlevsel hatalar

### H3 — Uygunluk Motoru yanlış eşikle arıyordu ("sonuç bulunamadı")

- **Belirti:** "Min. Skor" kutusunda **"40+ (tümü)"** görünüyor, arama yapılıyor
  ve **hiç sonuç gelmiyor**. Oysa API 40 eşiğiyle sonuç döndürüyordu.
- **Sebep:** Durumun varsayılanı `min_score: 50` idi; `<select>` seçenekleri ise
  40/60/75/90. Tarayıcı eşleşen seçenek bulamayınca ilkini ("40+") gösteriyor,
  istek ise **50** eşiğiyle gidiyordu.
- **Düzeltme:** Varsayılan `min_score` 40 yapıldı (seçeneklerle eşleşiyor).
- **Doğrulama:** İstek `min_score=40` gidiyor, tabloda sonuç görünüyor.

### H4 — Mesajlar ekranında yanlış/tekrarlı metinler

- **Belirtiler:**
  - Sayfa başlığının altında tekrar "Mesajlar" yazıyordu.
  - WhatsApp kutusunun altında **"Belge Yükle"** yazıyordu (yanlış çeviri anahtarı).
  - İki ayrı tablo da **"Personel"** başlığıyla geliyordu; biri "Personel
    bulunamadı" derken diğeri 22 kişiyi listeliyordu (kafa karıştırıcı).
- **Düzeltme:** 4 dilde `messages.whatsappHint`, `withPhone`, `withoutPhone`,
  `adminWhatsapp`, `openWhatsapp` anahtarları eklendi; ekran bu anahtarları
  kullanıyor. Artık: "Telefonu Kayıtlı Personel (0)" / "Telefonu Kayıtlı
  Olmayan Personel (22)" ve doğru WhatsApp açıklaması.

### H5 — Sayfa alt başlıkları başlığın aynısıydı

- **Etkilenen:** Gemi Personeli (`vesselStaff`) ve Ayarlar.
- **Düzeltme:** `vesselStaff.subtitle`, `settings.subtitle` eklendi
  (4 dilde), ekranlar bunları kullanıyor.

### H6 — İngilizce/Rusça/Arapça arayüzde Türkçe kalan etiketler

- **Düzeltilenler:** "Min. Skor" ve 40+/60+/75+/90+ seçenekleri,
  "Yönetici WhatsApp", "WhatsApp'ta Aç".
- Ayrıca Rusça ve Arapça çevirilerde kalmış İngilizce **"personnel"**
  kelimesi düzeltildi ("моряка" / "بحّار").
- **Kalan (bilinen eksik):** `App.jsx` içinde hâlâ ~60 sabit Türkçe metin var
  (ör. "Tümü", "İhtiyaç", "İnceleme Gerekli", rol adları). Arayüz Türkçe
  kullanılacaksa sorun değil; tam çok dilli kullanım için bu metinlerin
  i18n anahtarlarına taşınması gerekir. **Yapılacaklar listesine eklendi.**

### H7 — Giriş hatası mesajı yanıltıcıydı

- **Belirti:** Geçersiz biçimde e-posta yazıldığında "Geçersiz e-posta veya
  şifre" deniyordu (şifre suçlanıyordu). Aslında sorun e-posta biçimiydi.
- **Düzeltme:** 422 doğrulama hatası ayrıştırılıp `auth.invalidEmail` mesajı
  gösteriliyor. Ayrıca giriş ucu e-posta biçimini katı doğrulamıyor
  (`admin@crewintel.example` gibi adreslerle giriş yapılabiliyor).

### H8 — Dokümanlarda yanlış dosya türü iddiası

- **Belirti:** README ve kurulum rehberi "PDF, Word, Excel, JPG, PNG, OCR"
  diyordu; gerçek kod (`ALLOWED_UPLOAD_EXTENSIONS`) yalnızca **.pdf ve .txt**
  kabul ediyor, OCR yok.
- **Düzeltme:** README, `KURULUM/03` ve `KURULUM/04` gerçek davranışa göre
  düzeltildi (25 MB, PDF/TXT). İleride resim/OCR desteği istenirse
  `python-docx`, `openpyxl`, `Pillow`, `pytesseract` eklenmesi gerekir.

---

## 3. Denenip sorunsuz bulunan akışlar

| Akış | Sonuç |
|---|---|
| Giriş / çıkış (admin) | ✅ Oturum açılıyor, çıkışta yerel oturum siliniyor |
| Panel | ✅ 22 personel, 1/1 gemi, belge geçerlilik sayaçları, "Bugünkü İşler" |
| Personel listesi | ✅ 22 kayıt, arama/filtre (MAHMOUD → 2 sonuç), TEMİZLE |
| Yeni personel formu | ✅ Açılıyor, zorunlu alan doğrulaması çalışıyor, Vazgeç kapatıyor |
| Gemi listesi + gemi detayı | ✅ Filo, kadro planı, atama listesi |
| Atama (Ata) formu | ✅ Açılıyor, boş gönderim engelleniyor, X ile kapanıyor |
| Kontratlar | ✅ Liste + yeni kontrat formu (Vazgeç/Kaydet) |
| Belgeler | ✅ 25 belge, tür/eşleşme/geçerlilik filtreleri, indirme |
| Uygunluk Motoru | ✅ (H3 düzeltmesinden sonra) puanlı sonuç listesi |
| İş İlanları | ✅ Liste, şablon/başvuru/WhatsApp sekmeleri, yeni ilan formu |
| Mesajlar | ✅ Telefonu olan/olmayan personel ayrımı, WhatsApp bağlantısı |
| Ayarlar | ✅ Hesap, şifre, şirket görünümü, SMTP, kullanıcı listesi |
| Dil değiştirme | ✅ TR → EN anında; seçim tarayıcıda saklanıyor |
| Dar ekran (601 px) | ✅ Menü daralıyor, içerik tek kolona iniyor |

**API dumanı testi (curl):** `/health`, `/health/database`,
`/api/auth/login`, `/api/crew/`, `/api/ships/`, `/api/assignments/`,
`/api/contracts/`, `/api/documents/`, `/api/crew/eligible`,
`/api/dashboard/summary` → hepsi 200.

---

## 4. Bilinen eksikler / sonraki adımlar

1. **Menü etiketleri:** ~60 sabit Türkçe metin i18n'e taşınmalı (H6).
2. **Belge formatları:** Yalnızca PDF/TXT. Resim (JPG/PNG), Word/Excel ve OCR
   desteği isteniyorsa bağımlılıklar + `validate_upload` + arayüz `accept`
   güncellenmeli.
3. **Atama formu:** Vazgeç düğmesi yok (yalnızca sağ üstteki X). Eklenmesi
   kullanıcı dostu olur.
4. **Ayarlar ekranı:** İki ayrı "Ayarları Kaydet" düğmesi var (görünüm +
   bildirimler); etiketleri ayrıştırılmalı.
5. **Erişilebilirlik:** Bazı ikon düğmelerinde `aria-label` yok
   (modal kapatma, menü aç/kapa).
6. **Migration koruması:** Bilinmeyen Alembic revizyonunda konteyner restart
   döngüsüne giriyor; başlangıç betiğine anlaşılır hata mesajı eklenmeli.
7. **Otomatik yedek:** `KURULUM/05` içinde anlatıldı; istenirse betikle
   otomatikleştirilebilir.

---

## 5. Bu oturumda değişen dosyalar

- `frontend/src/App.css` — dar menü ikon düzeltmesi
- `frontend/src/App.jsx` — uygunluk eşiği, mesajlar metinleri, alt başlıklar,
  giriş hata mesajı
- `frontend/src/i18n/locales/{tr,en,ru,ar}.ts` — yeni çeviri anahtarları
- `README.md`, `KURULUM/03`, `KURULUM/04` — belge türü/sınır düzeltmeleri
- `backend/.env.example`, `backend/app/api/routes/auth.py` (önceki oturum),
  `backend/app/db/demo.py`, `sample_documents/`, `KURULUM/*` (kurulum paketi)
