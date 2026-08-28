# CREWINTEL Mobile — Android Admin App

Crew Management sisteminin Android admin uygulaması. Backend API'sine bağlanarak tüm admin fonksiyonlarını telefondan yönetmenizi sağlar.

## Özellikler

- 🔐 JWT ile giriş (admin/hr/viewer rolleri)
- 📊 Dashboard — özet kartlar, uyarılar
- 👤 Personel listesi + detay (arama, filtreleme)
- 📄 Belgeler listesi + eşleşme durumu
- 🚢 Gemiler listesi
- 🤖 AI Analiz + Eşleştirme
- 📧 E-posta gönderimi
- 💬 WhatsApp ile mesaj
- ⚙️ Sunucu adresi ayarı

## Gereksinimler

- Android Studio Hedgehog+ (veya Komodo)
- JDK 17
- Android SDK 34
- Fiziksel cihaz veya emülatör

## Build & Install

### Yöntem 1: Android Studio ile

1. Android Studio'u aç
2. `File → Open → mobile-app/` klasörünü seç
3. Gradle sync tamamlanana kadar bekle
4. `Run → Run 'app'` (veya Shift+F10)
5. USB debugging açık Xiaomi 15T Pro'ya bağla

### Yöntem 2: Komut satırı ile

```bash
cd mobile-app

# Debug APK oluştur
./gradlew assembleDebug

# APK konumu
# app/build/outputs/apk/debug/app-debug.apk

# USB ile yükle (adb kurulu olmalı)
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Yöntem 3: Wireless ADB (Xiaomi 15T Pro)

```bash
# Telefonda: Ayarlar → Ek ayarlar → Geliştirici seçenekleri → Kablosuz hata ayıklama
# Phone IP'sini bul (Ayarlar → Wi-Fi → Gelişmiş)

adb connect <PHONE_IP>:5555
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Backend Bağlantısı

Uygulama sadece **HTTP/HTTPS** üzerinden backend API'sine bağlanır. PostgreSQL'e doğrudan bağlanmaz.

### Laptop'ta backend'in her yerden erişilebilir olması için:

1. Laptopun IP adresini bul:
   ```bash
   # Windows
   ipconfig
   # IPv4 Adresi: 192.168.1.xxx
   ```

2. Uygulamada giriş ekranına `http://192.168.1.xxx:8000` yaz (laptop IP'si)

3. Aynı Wi-Fi ağına bağlı olmalısın

### Varsayılan giris bilgileri:

| Kullanıcı | E-posta | Şifre | Rol |
|-----------|---------|-------|-----|
| Admin | admin@crewintel.example | (DB'den kontrol et) | admin |
| HR | hr.live@crewintel.example | (DB'den kontrol et) | hr |
| Viewer | viewer.live@crewintel.example | (DB'den kontrol et) | viewer |

## Uygulama Yapısı

```
mobile-app/
├── app/
│   ├── src/main/
│   │   ├── java/com/crewintel/mobile/
│   │   │   ├── api/           # Retrofit API service
│   │   │   ├── models/        # Data modelleri
│   │   │   ├── screens/       # Activity'ler
│   │   │   └── utils/         # PrefsManager, helpers
│   │   ├── res/
│   │   │   ├── layout/        # XML layout'lar
│   │   │   ├── values/        # Tema, renkler, string'ler
│   │   │   └── xml/           # Network security config
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
├── build.gradle.kts
├── settings.gradle.kts
└── README.md
```

## API Endpoint'leri

Uygulama şu backend endpoint'lerini kullanır:

| Endpoint | Amaç |
|----------|------|
| `POST /api/auth/login` | JWT token al |
| `GET /health` | Sağlık kontrolü |
| `GET /api/dashboard/summary` | Dashboard özeti |
| `GET /api/crew/` | Personel listesi |
| `GET /api/crew/{id}` | Personel detayı |
| `GET /api/documents/` | Belge listesi |
| `GET /api/ships/` | Gemi listesi |
| `GET /api/contracts/` | Kontrat listesi |
| `POST /api/ai/analyze` | AI belge analizi |
| `POST /api/ai/match` | AI eşleştirme |
| `POST /api/notifications/send-email` | E-posta gönder |
| `GET /api/audit-logs/` | Audit log |

## Troubleshooting

### "Sunucuya bağlanılamıyor" hatası
- Laptop ve telefon aynı Wi-Fi'de mi?
- Backend çalışıyor mu? `curl http://LAPTOP_IP:8000/health`
- Firewall port 8000'e izin veriyor mu?

### "E-posta veya şifre hatalı"
- E-posta adresini kontrol et (DB'deki tam adres)
- Şifreyi kontrol et

### APK install başarısız
- telefonda "Bilinmeyen kaynaklara izin ver" açık mı?
- USB debugging açık mı?
