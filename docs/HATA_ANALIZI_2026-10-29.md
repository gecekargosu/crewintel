# Hata Analizi ve Düzeltme Raporu — 29.10.2026

Bu rapor, masaüstü (web) ve mobil uygulamanın **hem kullanıcı hem yazılımcı
gözüyle** uçtan uca denenmesiyle bulunan hataları, yapılan düzeltmeleri ve
doğrulama adımlarını içerir.

Test ortamı: Docker (backend + PostgreSQL + nginx üzerinde derlenmiş arayüz),
Expo web önizlemesi (`mobile/`), gerçek veritabanı kopyası (22 personel).

---

## 1. Masaüstü (yönetici paneli)

| # | Bulgu | Etki | Düzeltme |
|---|---|---|---|
| D1 | Toplu e-posta penceresinde metin `{t('ui.emailWillSend')}` olarak **ham** görünüyordu | Kullanıcı çeviri anahtarını okuyordu | `t()` çağrısına çevrildi; çoklu alıcı için `ui.emailWillSendMany` anahtarı 4 dile eklendi |
| D2 | Açılış verisi yalnızca bir kez yükleniyordu (`useEffect([])`, `auth` bağımlılığı yok) | Çıkış/giriş sonrası bayat veya boş ekran | Etki `[auth]` bağımlılığına alındı; girişteki tekrarlanan `loadData()` kaldırıldı |
| D3 | `const res = await axios.post(...)` kullanılmayan değişken | Lint uyarısı | Kaldırıldı (`oxlint`: 0 uyarı, 0 hata) |
| D4 | Yüklenen belgede okunan pasaport/gemiadamı numarası **kaydedilmiyordu** (`document_number` boş) | Belge listesinde/detayda numara yok; kullanıcı elle girmek zorunda | Üç yükleme yolunda (`document_service` ×2, `portal.py`) metadata'dan yazılıyor; test eklendi |
| D5 | Belge/kontrat süre uyarıları `user_id` olmadan (genel) üretiliyordu | **Her personel başka personelin belge durumunu görüyordu** | Uyarılar personelin kendi portal hesabına yönlendirildi; portaldaki eski genel kayıtlar sahiplik filtresinden geçiriliyor; test eklendi |
| D6 | Pasaport MRZ'si yalnızca numara için okunuyordu | Taranmış/Arapça/Rusça pasaportlarda doğum ve son geçerlilik tarihi kayboluyordu | `backend/app/services/mrz.py` eklendi: TD3/TD2, ICAO kontrol basamağı doğrulaması, ad-soyad, uyruk, cinsiyet, doğum ve bitiş tarihi; etiketli alan yoksa MRZ devreye giriyor |
| D7 | Bitiş tarihi etiketleri sınırlıydı | İtalyanca/İspanyolca/Hollandaca/Çince belgelerde tarih okunamıyordu | Etiket listesi genişletildi (`scadenza`, `fecha de caducidad`, `geldig tot`, `有效期`, `срок действия` …) |

## 2. Mobil uygulama (personel)

| # | Bulgu | Etki | Düzeltme |
|---|---|---|---|
| M1 | Yönetici/İK hesabıyla giriş yapılabiliyordu; uygulama personel uçlarına gidip **her ekranda 403** alıyordu | Uygulama tamamen boş görünüyordu | Giriş sırasında rol kontrolü: personel olmayan hesap için açık mesaj, token saklanmıyor (`AuthContext`) |
| M2 | `Alert.alert` React Native Web'de hiçbir şey yapmıyor | Çıkış onayı, "belge yüklendi" ve "başvur" onayı görünmüyor; web'de çıkış yapılamıyordu | `utils/dialogs.ts` (`showAlert` / `showConfirm`) eklendi; web'de tarayıcı penceresi kullanılıyor |
| M3 | Müsaitlik rozeti gerçek veride hep "Tanımlanmamış" | Personel müsait olsa bile görünmüyordu | Backend kodları (`available`, `on_board`, `on_leave`, `not_available`) tek yerde eşlendi (`utils/availability.ts`), yeni çeviri anahtarları eklendi |
| M4 | Profil/belge/mesaj ekranlarında sabit Türkçe metinler | Rusça/Arapça personel kendi dilini göremiyordu | Tüm etiketler i18n'e taşındı, belge türü ve durumları da çevrildi |
| M5 | Dil değiştirme imkânı yoktu (çeviriler hazır ama erişilemez) | Çok dilli kullanım pratikte çalışmıyordu | Profile "Dil" kartı: 🇹🇷 / 🇬🇧 / 🇷🇺 / 🇸🇦 |
| M6 | Kayıt formunda telefon "isteğe bağlı" görünüyordu, sunucu zorunlu tutuyordu | "Field required" gibi belirsiz hata; kayıt yapılamıyordu | Telefon zorunlu + doğrulama, etiket `*`; 422 hatalarında alan adı gösteriliyor |
| M7 | Kayıt sonrası metin "e-posta ile bilgilendirileceksiniz" diyordu | SMTP kurulu değilse yanlış vaat | Metin "onaydan sonra giriş yapabilirsiniz" olarak düzeltildi (4 dil) |
| M8 | Profilde iletişim bilgisi düzenlenemiyordu | Personel telefon/e-posta değiştiremiyordu | "İletişim Bilgilerim" kartı (`PUT /api/portal/contact`) |
| M9 | Çıkış/giriş sonrası ana sayfa **0 belge** gösteriyordu | Bayat veri; kullanıcı verisi kaybolmuş sanıyordu | Ana sayfa, profil ve belgeler sekmeleri `useFocusEffect` ile her odaklanmada tazeleniyor |
| M10 | Sözleşme süresi "6 ay ay" görünüyordu | Kozmetik hata | `formatDuration` yardımcısı: sayıysa birim ekler, metinse dokunmaz |
| M11 | Başka personelin belge uyarıları ana sayfada görünüyordu | Gizlilik/UX hatası | D5 ile birlikte düzeltildi; doğrulandı |
| M12 | Şifre unutulduğunda uygulamada yönlendirme yoktu | Kullanıcı çıkmaza düşüyordu | Giriş ekranına "yöneticinizden yeni şifre isteyin" notu |

---

## 3. Doğrulama (bu turda fiilen çalıştırıldı)

**Otomatik testler**

```bash
python -m pytest -q          # 212+ test
python -m pytest tests/test_mrz.py -q            # 5 yeni MRZ testi
python -m pytest tests/test_mobile_api.py -q     # 20 test (bildirim gizliliği dahil)
```

Sonuç: **hepsi geçti**. (FPDF/PDF dönüşümü testi için yerelde `fpdf2` kuruldu;
Docker imajında zaten var.)

**Masaüstü kullanıcı senaryosu**

- Giriş → Panel (22 personel, 5 süresi dolmuş belge) → Personel → Gemiler →
  Gemi Personeli → Kontratlar → Belgeler → Uygunluk → İş İlanları → Maaş →
  Notlar → Yapay Zekâ → Mesajlar → Ayarlar: **konsol hatası yok**.
- Bildirim zili, toplu e-posta penceresi (1 ve çok alıcı metni), belge yükleme.
- Rusça etiketli + MRZ'li pasaport yüklemesi: tür `passport`, düzenlenme
  2019-03-14, son geçerlilik 2029-03-14, personel eşleşmesi %100.
- İlan oluşturma → personel başvurusu → tekrar başvuru 409 → ilan silme.

**Mobil kullanıcı senaryosu**

- Personel girişi → Ana sayfa ("Müsait", 4 belge) → İlanlar → İlan detayı
  (%48 uygunluk, "Başvurunuz Alındı") → Belgeler (çevrilmiş türler, tarih) →
  Profil (iletişim düzenleme, dil seçimi) → Rusça'ya geçiş → tüm ekranlar Rusça.
- Yönetici hesabıyla giriş denemesi: **engellendi**, açıklayıcı mesaj, token yok.
- Yeni kayıt akışı: başarı ekranı, "yönetici onayı bekliyor".

**Temizlik:** test ilanı, başvuru, test belgesi ve test kullanıcısı silindi;
veritabanı 7 kullanıcı / 22 personel durumuna döndü, deneme telefonu temizlendi.

---

## 4. Bilinen sınırlar (düzeltilmedi, bilinçli)

- **Native Android/iOS derlemesi** bu ortamda denenmedi; Expo **web** önizlemesi
  ve `tsc` kontrolü yapıldı. Telefonda denemek için `KURULUM/06-MOBIL-UYGULAMA.md`.
- **Taranmış belge OCR kalitesi** tesseract dil paketlerine bağlıdır. Metin net
  değilse tarih okunamaz; MRZ varsa tarihler yine de bulunur.
- **E-posta / WhatsApp / push / yapay zekâ** anahtar gerektirir. Anahtar yokken
  program çalışır, ilgili özellik "yapılandırılmadı" der.
- Tarayıcıdan dosya seçme penceresi otomatik test edilemedi; yükleme yolu API
  üzerinden ve mobil/desktop kod incelemesiyle doğrulandı.

---

## 5. Öneriler (sıradaki adımlar)

1. **Yedekleme otomasyonu**: `storage/` + PostgreSQL dökümünü haftalık zip'le
   (KURULUM/05'teki adımların zamanlanmış görev hâli).
2. **Belge süresi bildirimleri** için e-posta kanalını açmak (SMTP bilgileri).
3. **Mobil**: push bildirim anahtarları girildiğinde cihaz kaydı zaten hazır;
   "belgem onaylandı" bildirimi eklenebilir.
4. **Uygunluk motoru** ağırlıklarının şirket tercihine göre ayarlanabilir olması.
5. **Denetim (audit) ekranı**: kim ne zaman hangi belgeyi yükledi/sildi.
