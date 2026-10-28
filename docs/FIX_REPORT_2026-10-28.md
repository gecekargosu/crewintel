# CREWINTEL — Hata Tespit ve Onarım Raporu (28.10.2026)

Bu oturumda masaüstü (React + FastAPI) ve mobil (Expo/React Native) uygulamaları
birlikte incelendi; tespit edilen hatalar düzeltildi ve her düzeltme gerçek API
çağrılarıyla doğrulandı.

## Ortam

| Bileşen | Adres | Not |
|---|---|---|
| Yerel API (güncel kod) | `http://127.0.0.1:8001` | `backend/.venv` + `crewintel-dev-db` (5434) |
| Masaüstü arayüz (kaynak) | `http://127.0.0.1:5174` | Vite dev server, `VITE_API_URL=...:8001` |
| Docker yığını | `http://127.0.0.1:5173` / `:8000` | **Farklı klasörden** (`C:\CREWINTEL`) çalışıyor, bu düzeltmeleri içermiyor |

## 1. Belge yüklemede 500 çökmesi (kritik)

`DocumentService.upload_documents()` → `MatchEngine` aday sorgusunda ulusal kimlik
numarası (`national_id`) bulunan belgelerde PostgreSQL JSONB üzerinde geçersiz SQL
üretiliyordu; uç 500 dönüyordu. Aday karşılaştırması artık Python tarafında
normalize edilerek yapılıyor (`app/services/match_engine.py`).

Doğrulama: 7 test belgesi tek istekte yüklenir → `201`.

## 2. Belge tipi yanlış sınıflandırılıyordu (kritik)

İki ayrı sınıflandırıcı vardı ve **"ilk eşleşen anahtar kelime kazanır"** mantığıyla
çalışan ikincisi doğru sonucu eziyordu:

- İş sözleşmesi, gövdesinde "medical certificate" geçtiği için **`medical`** oluyordu.
- Sağlık raporu, içinde "STCW" geçtiği için **`stcw`** oluyordu.

Düzeltme:
- `document_processing.classify_document_type()` tek doğru kaynak: başlık bölgesi
  (ilk 3 dolu satır), dosya adı ve gövde ayrı ağırlıklarla puanlanıyor; en yüksek
  skor kazanıyor. Dosya adı en güçlü sinyal (bir CV gövdesinde "medical" geçmesi
  onu sağlık raporu yapmaz).
- `match_engine.DocumentClassifier` artık bu fonksiyona devrediyor; genişletilmiş
  (alias) tipler yalnızca sonuç `other` ise, aynı ağırlıklı mantıkla aranıyor.

Doğrulama: `CREWINTEL_Test_Dokumanlari` (7) + `CREWINTEL_Karmasik_Test` (10)
belgesinin tamamı doğru tip alıyor (contract, seaman_book, goc, medical, cv,
passport, stcw).

## 3. Pasaport numarası hiç çıkarılamıyordu

Test pasaportunda numara "Document Number: T12345678" etiketiyle ve MRZ satırında
geçiyor; çıkarıcı yalnızca "Passport Number" arıyordu → `passport_number = null`,
dolayısıyla güçlü kimlik eşleşmesi hiç kurulamıyordu.

Düzeltme (`extract_metadata`): belge tipi doğrulanmışsa genel "Document Number"
etiketi ve TD3 MRZ'nin ikinci satırının ilk 9 karakteri kabul ediliyor. Genel etiket
yalnızca `passport` / `seaman_book` tipinde kullanılıyor; böylece bir sözleşmenin
"Contract Number" alanı pasaport numarası sanılmıyor.

Doğrulama: `Passport_Mehmet_Kaya.txt` → `pp=T12345678`; sözleşme → `pp=None`.

## 4. Mobil uygulama API katmanı backend ile uyuşmuyordu (kritik)

`mobile/services/api.ts` içindeki çağrıların büyük kısmı var olmayan uçlara gidiyordu.
Hepsi gerçek sözleşmeye çekildi:

| Mobil çağrı (eski) | Yeni / doğru uç |
|---|---|
| `GET /api/crew/me` | `GET /api/portal/me` |
| `PATCH /api/crew/me` | `PUT /api/portal/contact` |
| `PUT /api/crew/me/preferences` | `PUT /api/portal/preferences` |
| `GET/POST /api/crew/me/documents` | `GET/POST /api/portal/documents` |
| `GET /api/jobs` (crew'e 403) | `GET /api/portal/jobs` |
| `GET /api/jobs/{id}` | `GET /api/portal/jobs/{id}` |
| `POST /api/jobs/{id}/apply` | `POST /api/portal/jobs/{id}/apply` |
| `GET /api/jobs/recommended` | `GET /api/portal/jobs/recommended` |
| `GET /api/portal/me/applications` | `GET /api/portal/applications` |
| `GET /api/portal/me/contracts` | `GET /api/portal/contracts/me` |
| `GET /api/portal/me/vessel` | `GET /api/portal/vessel/me` |
| `GET /api/messages/{id}` | `GET /api/messages/conversations/{id}` |
| `POST /api/messages/{id}` + `{text}` | `POST /api/messages/conversations/{id}` + `{body}` |
| `POST /api/messages/conversations` + `{participant_id}` | `{crew_user_id}` |
| `GET /api/notifications` | `GET /api/portal/notifications` (yeni) |
| `PATCH /api/notifications/{id}/read` | `POST /api/portal/notifications/{id}/read` (yeni) |
| `POST /api/devices/register` | `POST /api/devices` |

Ek olarak API katmanı yanıtları ekranların beklediği şekle normalize ediyor
(`meFull` düz profil, konuşmalar `participant_name`, mesaj listesi dizi).

## 5. Güvenlik: personel bildirimleri

Personelin kendi bildirimlerini okuyabilmesi için yönetim ucunu (`/api/notifications`)
açmak yerine crew rolüne özel `/api/portal/notifications` uçları eklendi. Yönetim ucu
tekrar `admin/hr/viewer` ile sınırlı; `tests/test_audit_fixes.py` içindeki
"crew yönetim uçlarına erişemez" testi korunuyor.

## 6. Mobil arayüzde görünmez renkler / yanlış alanlar

- `colors.grey100..grey900`, `colors.white`, `colors.black` paletlerde yoktu →
  `undefined` renk (görünmez input/ayırıcı). `constants/Colors.ts` içine eklendi.
- Sohbet ekranı `item.text` / `sender_id` okuyordu; API `body` / `sender_user_id`
  döndürüyor → mesajlar boş görünüyordu. Düzeltildi.
- `messagesAPI.messages()` dizi bekliyordu, API `{conversation, messages}` dönüyordu.
- Ana ekran `n.is_read` / `profile.availability_status` okuyordu; alanlar `read`,
  `availability` → API katmanında eşlendi.
- İş ilanı listesi `salary_min/salary_max/company_name/status/created_at` bekliyordu;
  portal ucu `salary/currency/ship_name/application_status/application_deadline`
  döndürüyor → ekranlar gerçek alanlara bağlandı.
- `StyleSheet.absoluteFillObject` tip hatası ve eksik `firstMessageHint` çeviri
  anahtarı giderildi. `tsc --noEmit` artık **hatasız**.

## 7. Masaüstü arayüz düzeltmeleri

- Panel başlığı "Hoş geldin," iki kez ve isimsiz görünüyordu (`auth?.full_name`
  yanlış yol). `auth?.user?.full_name` + yeni `dashboard.subtitle` altyazısı.
- Belgeler tablosu ham kod gösteriyordu: `cv`, `medical`, `review_required`,
  `no_date`… Artık `documentTypes.*`, `matchStatus.*`, `expiryStatus.*` sözlükleriyle
  çevriliyor; tip filtresi de tamamen çevrildi (`goc` anahtarı 4 dile eklendi).
- 4 dilde eksik 7 çeviri anahtarı eklendi (`applications.applied`, `common.archived`,
  `common.open`, `common.selected`, `crew.selectPerson`, `documents.missingDocuments`,
  `jobs.addNew`). `scripts/i18n_audit.py` → **0 eksik**.

## 8. Giriş (login) sağlamlaştırması

- E-posta karşılaştırması büyük/küçük harf ve boşluk duyarsız
  (`ADMIN@crewintel.com  ` ile giriş çalışıyor).
- Kilit sayacı yalnızca **hatalı** denemelerde artıyor; doğru şifreyle gelen istek
  kilitli IP'de 429 yemiyor.

## 9. Yeni doğrulama betikleri

| Betik | Ne yapar |
|---|---|
| `scripts/api_smoke.py` | Yönetim uçlarının duman testi |
| `scripts/mobile_api_check.py` | Mobil API katmanının **her** çağrısını gerçek crew hesabıyla dener + crew'in yönetim uçlarına erişemediğini doğrular |
| `scripts/dev_verify_fixes.py` | Yükleme/500, sınıflandırma ve portal uçları |
| `scripts/i18n_audit.py` | Kullanılan ama tanımsız çeviri anahtarlarını bulur |

## Doğrulama sonuçları

| Kontrol | Sonuç |
|---|---|
| `pytest tests` | **173 passed** |
| `scripts/mobile_api_check.py` | **Tüm kontroller geçti** |
| `scripts/i18n_audit.py` | 4 dilde **0 eksik anahtar** |
| `cd mobile && tsc --noEmit` | **0 hata** |
| `cd frontend && vite build` | Başarılı |
| Masaüstü arayüz (tarayıcı) | Giriş, panel, personel, belgeler, uygunluk motoru açıldı; konsol hatası yok |

## Açık konular / dikkat

1. **Docker yığını eski koddan çalışıyor.** `crewintel-backend` / `crewintel-frontend`
   konteynerleri `C:\CREWINTEL` klasöründen üretilmiş; bu projedeki düzeltmeleri
   içermiyor. Güncellemek için bu klasörde `docker compose up -d --build` çalıştırmak
   gerekir (aynı proje adı ve veri hacmi korunur) veya değişen dosyalar
   `C:\CREWINTEL` altına kopyalanmalı.
2. **Personel kayıtları mükerrer.** Dev veritabanında 1–10 arası kayıtlar 11–20 olarak
   ikinci kez eklenmiş (Toplam Personel: 20). Seed betiği tekrar çalıştırıldığında
   var olan kayıtları atlamıyor.
3. **Test belgeleri ile seed verisi uyuşmuyor.** `CREWINTEL_Test_Dokumanlari`
   içindeki Mehmet Kaya'nın doğum tarihi 15.03.1988; veritabanındaki Mehmet Kaya
   12.04.1980. Eşleştirme motoru bunu doğru şekilde "çelişki" sayıp
   `review_required` bırakıyor (otomatik bağlamıyor). Otomatik eşleşme senaryosu
   test edilecekse belge veya seed verisi aynı kişiyi göstermeli.
4. **Mobil uygulama cihazda/emülatörde çalıştırılmadı.** Doğrulama API sözleşmesi
   ve TypeScript derlemesi düzeyinde yapıldı. Cihazda denemek için
   `EXPO_PUBLIC_API_URL=http://<bilgisayar-ip>:8001 npx expo start` gerekir
   (`localhost` telefonun kendisidir).
