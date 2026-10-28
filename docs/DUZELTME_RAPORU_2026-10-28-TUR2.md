# CREWINTEL — İkinci Tur Düzeltme Raporu (28.10.2026)

Bu turda istenen üç iş yapıldı: **(1)** yarım kalan maddeler tamamlandı,
**(2)** kullanıcı + yazılımcı gözüyle kapsamlı hata analizi yapıldı ve bulunanlar
onarıldı, **(3)** temiz kod çalışması yapıldı ve depo GitHub'a hazırlandı.

---

## 1. Şifre sorunu (acil ihtiyaç)

Şifre unutulduğunda kullanılabilecek bir araç yazıldı:

- `backend/scripts/sifre_sifirla.py` — komut satırı aracı
  (`--liste`, `--olustur`, `--sifre` seçenekleri)
- `KURULUM/sifre-sifirla.bat` — çift tıklanabilir kısayol
- `KURULUM/07-SIFRE-VE-HESAP.md` — hiç bilmeyen biri için adım adım rehber

Kullanımdaki yönetici hesabı doğrulandı: **admin@crewintel.example**. Bu hesabın
şifresi ekrandaki kayıtla aynıdır ve giriş testi başarılıdır. Şifre unutulursa
yukarıdaki araç yeni şifre üretir; her işlem `audit_logs` tablosuna yazılır.

---

## 2. Bulunan ve onarılan hatalar

| # | Hata | Etki | Onarım |
|---|---|---|---|
| 1 | **`renderPortal()` içinde React hook çağrısı** (rules-of-hooks hatası) | Portal ekranından başka sayfaya geçildiğinde hook sayısı değişir; uygulama çökebilir | Portal bağımsız `components/PortalPage.jsx` bileşenine taşındı |
| 2 | **Personel portalı sonsuz "yükleniyor"** | Hesabı bir personel kaydına bağlı olmayan kullanıcı hiçbir şey göremiyor, hata da göremiyor | Hata durumu eklendi: çevrilmiş, çözüm anlatan uyarı ekranı |
| 3 | **"crew" rolü tüm yönetici menülerini görüyor, hepsi 403 dönüyordu** | Personel 10 menü görüp hiçbirine giremiyordu | Personel rolünde menüde yalnızca "Portalım" gösteriliyor |
| 4 | **Sunucu hata mesajları Türkçe, arayüz başka dildeyken ham görünüyordu** (ör. İngilizce arayüzde "E-posta veya şifre hatalı.") | Çok dilli kullanımda dil tutarsızlığı | `utils/apiError.js` yardımcı fonksiyonu; 23 çağrı noktası buna bağlandı |
| 5 | **Operasyon Merkezi görev listesi sunucudan Türkçe geliyordu** ("25 belge onay/inceleme bekliyor") | Aynı dil sorunu | API görevlere `text_key` + `params` ekliyor, arayüz 4 dilde çeviriyor (eski `text` alanı geriye dönük korundu) |
| 6 | **Atama formunda "Vazgeç" yoktu** | Kullanıcı yalnızca sağ üstteki X ile çıkabiliyordu | Vazgeç + Ata düğmeleri eklendi |
| 7 | **Ayarlar'da iki düğme de "Ayarları Kaydet"** | Hangisinin neyi kaydettiği belirsiz | Bildirim formu artık "Bildirim Ayarlarını Kaydet" |
| 8 | **86 sabit Türkçe metin** (placeholder, etiket, ipucu) | Dil değiştirilince ekranlar karışık kalıyordu | Tamamı i18n'e taşındı; 4 dilde (tr/en/ru/ar) karşılıkları yazıldı |
| 9 | **"IMO belirtilmemiş", "WhatsApp Kuyruğu", kuyruk mesajları** çevrilmemişti | Aynı sorun | i18n'e taşındı |
| 10 | `auth.invalidEmail` anahtarı kodda vardı, sözlüklerde yoktu | Geçersiz e-postada anahtar adı görünüyordu | 4 dile eklendi |

Ek olarak **ölü kod** temizlendi: kullanılmayan 5 fonksiyon
(`goToFilteredDocs`, `formatFileSize`, `retryUpload`, `uploadSingleFile`,
`approveDocument`, `rejectDocument`), 5 kullanılmayan state, `ROLE_MAP`,
13 kullanılmayan `catch` parametresi.

---

## 3. Doğrulama (kanıtlar)

| Kontrol | Komut | Sonuç |
|---|---|---|
| Frontend derleme | `npx vite build` | ✅ hatasız derlendi |
| Frontend lint | `npx oxlint src/...` | ✅ **0 hata**, 30 uyarıdan 1'e indi (kalan: `useEffect` bağımlılık önerisi) |
| Backend lint | `ruff check app scripts --select F,E9,W6` | ✅ 0 hata (önce 31) |
| Backend testleri | `pytest -q` (Docker) | ✅ 45/45 geçti |
| API taraması | `scripts/api_smoke.py` | ✅ 39 GET ucu, **0 hata** |
| i18n denetimi | `scripts/i18n_audit.py` | ✅ 4 dilde eksik anahtar: 0 |
| Tarayıcı senaryosu | gerçek arayüz | ✅ aşağıdaki adımlar |

Tarayıcıda kullanıcı gibi denenen akış:
yanlış şifreyle giriş denemesi (doğru hata mesajı) → doğru giriş → panel →
Personel / Gemiler / Gemi Personeli / Kontratlar / Belgeler / Uygunluk / İlanlar /
Mesajlar / Ayarlar ekranları → atama formu aç/kapat → **yeni personel hesabı
oluşturma (personel kaydı bağlayarak)** → çıkış → o hesapla giriş →
portal profili, "İş Arıyorum" aç/kapat, telefon kaydetme, belge listesi →
dil değiştirme (Türkçe / İngilizce / Rusça / Arapça-RTL).

---

## 4. Temiz kod durumu

- Arayüzde 5.020 satırlık tek dosya hâlâ var; ancak portal ayrıştırıldı ve
  `config.js`, `utils/apiError.js`, `components/PortalPage.jsx` modülleri oluştu.
- Tüm Python modülleri docstring + tip ipuçlu; model ilişkileri artık
  `TYPE_CHECKING` bloğu ile tiplendi (statik analiz temiz).
- Kullanılmayan import/değişken kalmadı; `ruff` ve `oxlint` temiz.
- Kalan bilinen borç: `App.jsx`'in ekran bileşenlerine bölünmesi ve
  `useEffect` bağımlılık listesinin `useCallback` ile düzenlenmesi.
  Bunlar çalışan davranışı bozmamak için bilinçli olarak sonraya bırakıldı.

---

## 5. Depo (GitHub) durumu

Yerel depo ile GitHub arasındaki fark incelendi:

- Yerel `master`: **1 commit ileride, 69 commit geride**.
- GitHub'daki `master` içinde yerelde **hiç bulunmayan** dosyalar var:
  `backend/ai/*` modülleri, kişisel CV dosyaları, eski Kotlin `mobile-app/`,
  `CLAUDE.md`. Ayrıca GitHub'da `KURULUM/` ve yeni `mobile/` (Expo) klasörü yok.
- Bu nedenle **zorla üzerine yazma yapılmadı** (uzaktaki AI modülleri ve eski
  sürüm kaybolurdu). Bunun yerine yerel çalışan sürüm ayrı bir dalda yayınlandı.

Karar: `master` dalına dokunulmadı; temiz ve çalışan sürüm yeni bir dal olarak
yüklendi. `master`'ı da bu sürüme geçirmek isterseniz bilinçli bir karar
gerekiyor (uzaktaki `backend/ai` dosyaları silinecek, CV'ler kaldırılacak).
