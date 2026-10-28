# GitHub Deposu — Durum Tespiti ve Yapılacaklar

**Depo:** <https://github.com/gecekargosu/crewintel> (public, varsayılan dal `master`)
**İnceleme tarihi:** 28.10.2026
**İnceleme yöntemi:** GitHub API ile depo ağacı indirildi (292 dosya, 10,5 MB) ve
yerel çalışma klasörüyle karşılaştırıldı.

---

## 1. Özet

Depo **çalışıyor ama güncel değil ve dağınık.** En büyük sorun: depodaki kod,
bilgisayarınızdaki güncel sürümün **gerisinde**. Depoda telefon uygulaması
Kotlin (`mobile-app/`), güncel sürümde ise Expo/React Native (`mobile/`).
Kurulum rehberi (`KURULUM/`) depoda **hiç yok**, yani indiren kişi programı
kuramıyor. Ayrıca depo kökünde kişisel CV dosyaları ve ekran görüntüleri var.

---

## 2. Tespit edilen hatalı / gereksiz yüklemeler

| # | Dosya / klasör | Boyut | Sorun | Yapılacak |
|---|---|---|---|---|
| 1 | `YAZILIM_Cengiz_Kilic_AI_Software_CV_EN.docx` | 39 KB | Kişisel CV, projeyle ilgisiz | Depodan çıkar |
| 2 | `YAZILIM_Cengiz_Kilic_YZ_Yazilim_CV_TR.docx` | 39 KB | Kişisel CV | Depodan çıkar |
| 3 | `cengiz_kilic_cv_final.pdf` / `.html` | 70 KB | Kişisel CV | Depodan çıkar |
| 4 | `cengiz_kilic_cv_tr.docx` / `.pdf` / `.html` | 100 KB | Kişisel CV | Depodan çıkar |
| 5 | `cv_en_content.txt`, `cv_tr_content.txt` | küçük | CV içeriği | Depodan çıkar |
| 6 | `generate_cv_final.py`, `generate_docx.py`, `generate_docx_final.py`, `make_docx_cv.py` | küçük | CV üretme betikleri, projeyle ilgisiz | Depodan çıkar |
| 7 | `screen.png`, `phone_screen.png`, `ui_dump.xml` | ~200 KB | Test artığı ekran görüntüleri | Depodan çıkar |
| 8 | `installer/UMAY_Admin.apk` | **7,3 MB** | Derlenmiş APK; her sürümde depo şişer, kaynağı yok | Depodan çıkar, sürüm notuna bağlantı koy |
| 9 | `mobile-app/` (120 dosya) | — | **Eski** Kotlin uygulaması; güncel `mobile/` (Expo) ile çakışıyor | Kaldır veya `legacy/` altına al |
| 10 | `social-downloader/` | — | Projeyle ilgisiz ayrı servis | Ayrı depoya taşı |
| 11 | `docs/DEVELOPMENT_LOG.backup-2026-08-13.md` | 26 KB | Yedek dosya | Sil |
| 12 | `docs/ROADMAP/_backup_2026-08-13/` (3 dosya) | — | Yedek dosyalar | Sil |
| 13 | `project-tree.txt` (yerelde takipli) | 1 MB | Otomatik üretilen ağaç dökümü | `.gitignore` + depodan çıkar |
| 14 | `storage/` (yerelde 54 dosya takipli) | — | Yüklenen **gerçek belgeler**; gizlilik riski | `git rm --cached` ile takipten çıkar |
| 15 | `CREWINTEL_AUDIT.txt` (2 MB), `CREWINTEL_CURRENT_STATE.txt`, `_RECOVERY_*`, `CREWINTEL_HANDOFF_*` | ~4 MB | Geliştirme artıkları (yerelde takipsiz, iyi) | Yüklemeye dahil etme |
| 16 | `mobile.zip` (143 MB), `backups/`, `mobile/node_modules/`, `mobile/dist/` | çok büyük | Yerelde duruyor; yanlışlıkla eklenirse GitHub reddeder | `.gitignore`'a eklendi |
| 17 | `e ps`, `backend;C`, `duplicate_test*.txt` | küçük | Yanlışlıkla oluşmuş dosyalar | `.gitignore`'a eklendi |

> **İyi haber:** Depoda `.env` dosyası **yok** (doğru), `.env.example` var,
> `.gitignore` mevcut ve test şifreleri dışında sızmış bir anahtar/parola
> bulunmadı. Yani acil bir güvenlik ihlali yok; sorun düzen ve güncellik.

---

## 3. Güncellik farkı (depo ↔ bilgisayarınız)

Depoda **olmayan**, yerelde olan başlıca parçalar:

- `mobile/` — Expo/React Native telefon uygulaması (5 sekme, 4 dil)
- `KURULUM/` — kurulum rehberi + 7 `.bat` betiği (indiren kişi için şart)
- `sample_documents/` — demo için örnek belgeler
- `backend/app/api/routes/` içinde `jobs`, `messages`, `notifications`,
  `portal`, `auth`, `settings` gibi yeni uçlar
- `frontend/src/i18n/` — Türkçe/İngilizce/Rusça/Arapça çeviriler
- `tests/test_audit_fixes.py`, `scripts/dev_seed_local.py`, `scripts/dev_verify_fixes.py`
- `docker-compose.prod.yml`, `backend/app/db/demo.py`

Depoda **olan**, yerelde olmayan: `mobile-app/` (Kotlin), `social-downloader/`,
`installer/` (APK), CV dosyaları, Playwright yapılandırmaları.

Sonuç: depo **eski bir sürümü** yayınlıyor. İndiren kişi ne güncel arayüzü ne
de kurulum rehberini görür.

---

## 4. Yapılacaklar listesi (sırayla)

### A. Zorunlu (depo kurulabilir olsun diye)

- [x] Kök `README.md` yazıldı — kurulum, özellikler, sorun giderme, klasör yapısı
- [x] `.gitignore` genişletildi — `mobile/node_modules`, `mobile/dist`, `*.apk`,
      `*.zip`, CV dosyaları, ekran görüntüleri, `storage/`, `mobile-app/`,
      `social-downloader/`, `*.sql`, `sorun-raporu.txt`
- [x] `KURULUM/` klasörü tamamlandı (00–06 numaralı rehberler + `kur.bat`,
      `baslat.bat`, `durdur.bat`, `demo-veri-yukle.bat`, `demo-veri-sil.bat`,
      `sifirdan-kur.bat`, `sorun-raporu.bat`)
- [x] `sample_documents/` eklendi (demo kurulumun boş kalmaması için)
- [x] `.env.example` içinde tüm anahtarlar açıklamalı
- [ ] Depoyu güncel kodla yeniden yükle (aşağıdaki 5. bölüm)
- [ ] Eski sürümü `legacy` etiketiyle sakla, `master`'ı güncel sürüme çevir

### B. Temizlik

- [ ] CV dosyalarını ve CV üretme betiklerini depodan çıkar
- [ ] `screen.png`, `phone_screen.png`, `ui_dump.xml` çıkar
- [ ] `installer/UMAY_Admin.apk` çıkar (7 MB) → sürüm notlarında bağlantı ver
- [ ] `mobile-app/` (Kotlin) kaldır veya `legacy/mobile-app/` altına al
- [ ] `social-downloader/` ayrı depoya taşı
- [ ] `docs/*backup*` ve `docs/ROADMAP/_backup_*` sil
- [ ] `project-tree.txt` ve `storage/` takipten çıkar

### C. İyileştirme (isteğe bağlı)

- [ ] README'ye 2–3 ekran görüntüsü ekle (`docs/images/` altında, küçültülmüş)
- [ ] Sürüm etiketi (tag) kullan: `v1.0.0` — indiren kişi sabit sürüm alır
- [ ] GitHub **Releases** bölümüne hazır ZIP koy (kurulum klasörü dahil)
- [ ] `LICENSE` dosyası ekle (özel/ticari ise "All rights reserved" metni)
- [ ] GitHub Actions ile `pytest` çalıştır (her push'ta test)
- [ ] Dal koruması: `master`'a doğrudan push yerine PR kullan

---

## 5. Güncel sürümü depoya yükleme (adım adım)

Depoda eski sürüm olduğu için üzerine eklemek karışıklık yaratır. En temizi
**temiz bir dal** oluşturup onu `master` yapmak.

### 5.1. Yerelde hazırlık

```bash
cd "C:/CREWINTEL"            # proje klasörün
git remote add origin https://github.com/gecekargosu/crewintel.git
git fetch origin
```

Depoda takipli ama artık gereksiz dosyaları **sadece takipten** çıkar
(bilgisayardan silinmez):

```bash
git rm -r --cached storage project-tree.txt
```

### 5.2. Temiz dal oluştur

```bash
git checkout --orphan temiz-surum
git add .
git status                   # listeyi gözden geçir: node_modules, zip, apk OLMAMALI
git commit -m "CREWINTEL v1.0: güncel masaüstü + mobil + kurulum rehberi"
```

> `git status` çıktısında `mobile/node_modules`, `mobile.zip`, `*.apk`,
> `storage/` görürsen **dur**; `.gitignore` çalışmıyor demektir.

### 5.3. Yükle ve eski sürümü yedekle

```bash
git branch eski-surum origin/master    # eski hâli sakla
git push origin temiz-surum
```

GitHub'da **Compare & pull request** → `temiz-surum` → `master` → **Merge**.
Bir sorun çıkarsa `eski-surum` dalına dönerek geri alabilirsin.

### 5.4. Kontrol

1. Depoyu **gizli sekmede** aç (çıkış yapmış hâlinle) →
   <https://github.com/gecekargosu/crewintel>
2. README görünüyor mu, `KURULUM/` klasörü var mı?
3. **Code → Download ZIP** → başka bir klasöre çıkar →
   `KURULUM\kur.bat` gerçekten çalışıyor mu? (En önemli test bu.)
4. Depo boyutu 50 MB'ın altında mı? (Settings → boyut bilgisi)

---

## 6. Notlar

- Depo **public**. İçine gerçek personel verisi, müşteri adı, gerçek belge
  konulmamalı. `storage/` ve `sample_documents/` dışındaki belgeler depoya
  girmemeli; `sample_documents/` içindekiler tamamen kurgusal örneklendir.
- `.env` dosyası hiçbir zaman yüklenmemeli. Yanlışlıkla yüklendiyse: değerleri
  değiştir (şifre/JWT), sonra geçmişten temizle (`git filter-repo`).
- Büyük dosya (>50 MB) yüklemesi GitHub tarafından reddedilir; `mobile.zip`
  (143 MB) bu yüzden asla eklenmemeli.
- Depo açıklaması ve konu etiketleri (`topics`) eklenebilir:
  `fastapi`, `react`, `expo`, `postgresql`, `maritime`, `crew-management`.
