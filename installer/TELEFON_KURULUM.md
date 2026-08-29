# 📱 UMAY Admin - Telefon Kurulum Rehberi

## APK Nasıl Yüklenir?

### Yöntem 1: USB Kablo (En Kolay)

1. Telefonu bilgisayara **USB kablo** ile bağlayın
2. Telefonda **"Dosya Aktarımı"** modunu seçin
3. Bilgisayarda **Bu Bilgisayar** → **Telefonunuz** → **DCIM** veya **Downloads** klasörüne gidin
4. Masaüstündeki `UMAY_Admin.apk` dosyasını bu klasöre kopyalayın
5. Telefonda **Dosya Yöneticisi** uygulamasını açın
6. Kopyaladığınız `.apk` dosyasına tıklayın
7. "Bilinmeyen kaynaklardan yükleme" izni isterseniz **İzin Ver** deyin

### Yöntem 2: WhatsApp / E-posta

1. Masaüstündeki `UMAY_Admin.apk` dosyasını **WhatsApp**'tan kendinize gönderin
2. Telefonda WhatsApp'ı açın, gelen `.apk` dosyasına tıklayın
3. Yükleme adımlarını takip edin

---

## Uygulama Ayarları

Uygulamayı açınca **Sunucu Adresi** isteyecek.

### IP Adresini Bulma

1. Masaüstü bilgisayarda **PowerShell** açın
2. Şu komutu yazın: `ipconfig`
3. **Wi-Fi** bölümüne bakın
4. **IPv4 Adresi** yazan satırı bulun (örnegin: `192.168.1.105`)
5. Telefondaki uygulamaya şunu yazın:
   ```
   http://192.168.1.105:8000
   ```
   (kendi IP adresinizi yazın)

### Giriş

| Alan | Değer |
|------|-------|
| E-posta | `admin@crewintel.com` |
| Şifre | `UmayAdmin2026!` |

---

## ⚠️ Önemli Notlar

- Telefon ve bilgisayar **aynı Wi-Fi** ağında olmalı
- `http://` yazın, `https://` değil
- Bağlantı kesilirse uygulamayı kapatıp tekrar açın
