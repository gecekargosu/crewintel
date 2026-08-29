# 🚢 UMAY Admin - Kurulum Kılavuzu

> Bu belge, bilgisayarı olmayanlar için adım adım kurulum rehberidir.

---

## 📋 Ne Lazım?

Bilgisayarınızda şu programlardan **biri** olmalı:

| Program | Gereksiz mi? |
|---------|-------------|
| Windows 10 veya 11 | ✅ Zaten var |
| İnternet bağlantısı | ✅ Zaten var |
| **Hiçbir şey başka indirmenize gerek yok!** | Otomatik indirecek |

---

## 🚀 Kurulum (3 Adım)

### Adım 1: Dosyaları İndirin

Wetransfer ile gönderilen `.zip` dosyasını bilgisayarınıza indirin.

### Adım 2: Zip'i Açın

- Zip dosyasına **çift tıklayın**
- İçindeki `install.bat` dosyasını **çift tıklayın**
- "Yönetici olarak çalıştır" seçeneğine **Evet** deyin

> ⏳ Bu noktada bilgisayarınız tüm gerekli programları otomatik olarak indirip kuracak. **10-15 dakika** sürebilir. Bilgisayarı kapatmayın veyaదip değer vermeyin.

### Adım 3: Kurulum Tamamlandı

Kurulum bittiğinde ekranınızda şöyle bir mesaj göreceksiniz:

```
✅ KURULUM TAMAMLANDI!
```

Ve tarayıcınız otomatik olarak açılacak.

---

## 🔑 Giriş Bilgileri

Uygulamaya girmek için:

| Alan | Değer |
|------|-------|
| **E-posta** | `admin@crewintel.com` |
| **Şifre** | `UmayAdmin2026!` |

---

## 📱 Telefona Kurulum

### Android Telefon İçin:

1. **Masaüstünüzde** `UMAY_Admin.apk` dosyası olacak
2. Bu dosyayı telefonunuza gönderin:
   - **USB kablo ile**: Telefona bağlayın, masaüstünden telefona kopyalayın
   - **WhatsApp ile**: Masaüstünden WhatsApp'a gönderin
   - **E-posta ile**: Kendinize e-posta ile gönderin
3. Telefonda `.apk` dosyasına tıklayın
4. "Bilinmeyen kaynaklardan yükleme" izni isterseniz **İzin Ver** deyin
5. **UMAY Admin** uygulaması yüklenecek

### Uygulamayı Açınca:

1. **Sunucu Adresi** kısmına şunu yazın:
   ```
   http://<MASAÜSTÜ_BİLGİSAYAR_IP>:8000
   ```
   
   > 💡 **IP adresini bulmak için**: Masaüstünde PowerShell açın ve `ipconfig` yazın. `Wi-Fi` bölümündeki `IPv4 Adresi` olan sayıları kullanın.
   
   > Örnek: `http://192.168.1.105:8000`

2. **E-posta**: `admin@crewintel.com`
3. **Şifre**: `UmayAdmin2026!`
4. **Giriş Yap** butonuna tıklayın

---

## 🔧 Sonraki Kullanımlar

Her uygulamayı başlatmak için:

1. Masaüstünde **"UMAY Baslat.bat"** dosyasına çift tıklayın
2. Tarayıcınızda `http://localhost:5173` adresini açın

Kapatmak için:

1. **"UMAY Durdur.bat"** dosyasına çift tıklayın

---

## ❓ Sorun mu Var?

| Sorun | Çözüm |
|-------|-------|
| "Docker bulunamadı" hatası | Bilgisayarı yeniden başlatın, tekrar `install.bat` çalıştırın |
| "Yetki hatası" | `install.bat` dosyasına sağ tıklayın → "Yönetici olarak çalıştır" |
| Telefondan bağlanamıyorum | Telefon ve bilgisayar aynı Wi-Fi'de olmalı |
| "Bu site engellendi" | Tarayıcıda `http://` yazdığınızdan emin olun (https değil) |
| Şifremi unuttum | Bana ulaşın, sıfırlayalım |

---

## 📞 Yardım

Herhangi bir sorun yaşarsanız bana yazın. Adım adım yardımcı oluruz.

---

*Son güncelleme: Ağustos 2026*
