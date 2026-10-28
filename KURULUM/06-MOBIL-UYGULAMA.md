# 6. Adım — Mobil Uygulama (isteğe bağlı)

Mobil uygulama, masaüstü programın **aynı veritabanını** kullanır. Yani
bilgisayardaki program açıkken telefon da aynı personel, gemi ve belgeleri görür.

> Mobil uygulama **Expo** ile yazılmış (React Native). Telefona kurmak için
> iki yol var: **A) Expo Go ile hemen denemek** (en kolay), **B) APK üretip
> kurmak** (kalıcı).

---

## Ön koşullar

1. Masaüstü program **çalışıyor** olmalı (`baslat.bat`).
2. Bilgisayarda **Node.js LTS** kurulu olmalı: <https://nodejs.org/>
3. Telefon ve bilgisayar **aynı Wi-Fi ağında** olmalı.
4. Telefonda **Expo Go** uygulaması (App Store / Google Play, ücretsiz).

---

## A) Expo Go ile çalıştırma (5 dakika)

### 1) Bilgisayarın yerel IP adresini bul

`cmd` aç → `ipconfig` → **IPv4 Address** satırı (ör. `192.168.1.34`).

### 2) Backend'i ağa aç

Program zaten `0.0.0.0:8000` dinliyor, yani ağdan erişilebilir. Windows
Güvenlik Duvarı sorarsa **İzin ver** de. Vermezsen:
Windows Defender Güvenlik Duvarı → **Gelişmiş ayarlar** → **Gelen Kuralları** →
**Yeni Kural** → Port → TCP → `8000,5173` → Bağlantıya izin ver.

### 3) Mobil klasöründe bağımlılıkları kur

`mobile` klasöründe `cmd` aç:

```
npm install
```

### 4) API adresini tanımla ve başlat

```
set EXPO_PUBLIC_API_URL=http://192.168.1.34:8000
npx expo start
```

> `192.168.1.34` yerine kendi IP'ni yaz. Bu satır **her yeni cmd penceresinde**
> tekrar girilmelidir.

### 5) Telefonda aç

- Ekranda bir **QR kod** çıkar.
- Android: **Expo Go** uygulamasını aç → **Scan QR code**.
- iPhone: Kamera uygulamasıyla QR'ı okut → açılan bağlantıya dokun.
- Uygulama yüklenince giriş ekranı gelir. **Masaüstü programdaki e-posta ve
  şifre** ile giriş yap.

> Telefon bağlanamıyorsa: `npx expo start --tunnel` komutunu dene (internet
> üzerinden tünel açar, Wi-Fi şartı kalkar, biraz yavaştır).

---

## B) APK üretip telefona kurmak (kalıcı)

Kurulum dosyası (APK) üretmek için ücretsiz bir Expo hesabı gerekir:
<https://expo.dev/signup>

```
npm install -g eas-cli
eas login
cd mobile
eas build -p android --profile preview
```

- Derleme bulutta yapılır, **10–20 dakika** sürer.
- Bitince bir indirme bağlantısı verir; APK'yı telefona indirip kur
  ("Bilinmeyen kaynaklara izin ver" isteyebilir).
- iPhone için `.ipa` üretmek Apple Developer hesabı gerektirir (ücretli).

> APK içindeki API adresi **derleme sırasında** sabitlenir. Bilgisayarın IP'si
> değişirse uygulama bağlanamaz. Sabit bir adres için `EXPO_PUBLIC_API_URL`
> değerini `eas.json` içine yaz veya bilgisayara sabit IP ver.

---

## Mobil uygulamada neler var?

> **Önemli:** Mobil uygulama **yalnızca personel (crew) hesapları** içindir.
> Yönetici/İK hesabıyla giriş denenirse uygulama "Bu uygulama personel içindir"
> uyarısı verir ve oturum açmaz. Yönetici işlemleri masaüstü panelinden yapılır.

| Sekme | İçerik |
|---|---|
| **Ana Sayfa** | Özet kartlar, süresi yaklaşan belgeler, kısayollar |
| **İlanlar** | Açık ilanlar, ilan detayı, başvuru |
| **Başvurular** | Yaptığın başvuruların durumu |
| **Belgeler** | Kendi belgelerin; PDF/Word/Excel/fotoğraf yükleme (yönetici onayına gider) |
| **Mesajlar** | Şirketle yazışma |
| **Profil** | Kendi bilgilerin, belgelerin, kontratın, gemin, iletişim bilgisi düzenleme, dil seçimi |

Dil değiştirme: **Profil → Dil** (Türkçe / İngilizce / Rusça / Arapça).

Personel hesabı nasıl açılır? Masaüstünde **Ayarlar → Kullanıcılar → Yeni
Kullanıcı**: rol `crew`, ilgili personel seçilir. Şifresini unutan personel için
`KURULUM/07-SIFRE-VE-HESAP.md`.

---

## Mobil sorun giderme

| Sorun | Çözüm |
|---|---|
| "Network request failed" | `EXPO_PUBLIC_API_URL` yanlış; IP'yi kontrol et, telefonla aynı Wi-Fi'de ol, güvenlik duvarını aç. |
| QR okutuldu ama uygulama açılmıyor | Telefon ve bilgisayar farklı ağda. `--tunnel` ile dene. |
| Giriş yapamıyorum | Personel (crew) hesabı gerekir; yönetici hesabı mobilde çalışmaz. Hesap yoksa masaüstünden oluştur. |
| "Bu uygulama personel içindir" uyarısı | Yönetici/İK hesabıyla giriş denendi. Personel hesabıyla giriş yapın. |
| Belgeler boş görünüyor | Sayfayı aşağı çekip yenileyin (uygulama sekmeye dönüldüğünde kendisi de tazeler). |
| Beyaz ekran | `npx expo start --clear` ile önbelleği temizle. |
| Değişiklikler görünmüyor | Terminalde `r` tuşuna bas (reload). |

---

## Klasör yapısı (merak edenler için)

```
CREWINTEL/
├── backend/     → sunucu (Python/FastAPI) + veritabanı modelleri
├── frontend/    → masaüstü arayüzü (React, tarayıcıda açılır)
├── mobile/      → telefon uygulaması (Expo/React Native)
├── KURULUM/     → bu rehber ve .bat dosyaları
├── storage/     → yüklenen belgeler (yedeklenmeli!)
└── docker-compose.yml → üç parçayı birlikte çalıştırır
```
