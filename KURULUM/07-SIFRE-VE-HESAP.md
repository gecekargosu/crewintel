# 07 — ŞİFRE SIFIRLAMA VE HESAP İŞLEMLERİ

> Bu dosya, **şifresini unutan** veya **yeni bir kullanıcı açması gereken** kişi içindir.
> Hiç bilgisayar bilmeyen biri için yazıldı: adımları sırayla yapın.

---

## 1. En kolay yol: hazır dosyayı çalıştır

1. **CREWINTEL klasörünü** açın (içinde `docker-compose.yml` olan klasör).
2. `KURULUM` klasörüne girin.
3. **`sifre-sifirla.bat`** dosyasına **çift tıklayın**.
4. Siyah bir pencere açılacak. Kayıtlı hesapların listesi görünecek.
5. **"Şifresi sıfırlanacak e-posta adresini yazın:"** satırına, örneğin:
   ```
   admin@crewintel.example
   ```
   yazıp **Enter** tuşuna basın.
6. Ekranda şuna benzer bir satır çıkacak:
   ```
   Şifre güncellendi: admin@crewintel.example (rol: admin, hesap aktif)
     ŞİFRE: k7Rt!mQ2xLp9Wz4a
   ```
7. **`ŞİFRE:` satırındaki değeri bir yere yazın.** Bu şifre ekranda bir daha gösterilmez.
8. Programa girip e-postanızla bu yeni şifreyi kullanın.

> **Not:** Program kapalıysa araç "CREWINTEL çalışmıyor" der. O zaman önce
> `baslat.bat` dosyasını çalıştırıp 1–2 dakika bekleyin, sonra tekrar deneyin.

---

## 2. Şifreyi kendim belirlemek istiyorum

`KURULUM` klasöründe boş bir yere **Shift + sağ tık** → "PowerShell penceresini burada aç"
diyin ve şu komutu yazın (kendi şifrenizi tırnak içine koyun):

```powershell
docker exec crewintel-backend python -m scripts.sifre_sifirla admin@crewintel.example --sifre "KendiSifrem123!"
```

Kurallar: en az **8 karakter**. Türkçe karakter kullanmayın, aksi halde bazı
tarayıcılarda giriş sorun çıkarabilir.

---

## 3. Hiç hesap yok / hepsi silinmiş

Yeni bir yönetici hesabı oluşturmak için:

```powershell
docker exec crewintel-backend python -m scripts.sifre_sifirla yeni@firma.com --olustur --ad "Adınız Soyadınız"
```

Ekranda verilen şifreyle giriş yapın.

---

## 4. Kullanıcı listesini görmek

Hangi hesaplar var, hangisinin şifresi tanımlı değil:

```powershell
docker exec crewintel-backend python -m scripts.sifre_sifirla --liste
```

`ŞİFRE` kolonunda **YOK** yazan hesap giriş yapamaz; 2. veya 3. adımla şifre atayın.

---

## 5. Program içinden şifre değiştirme (normal yol)

Programı açın → sol menüden **Ayarlar** → **Hesabım** kartı → **Şifre Değiştir**.
Burada **mevcut şifrenizi** bilmeniz gerekir. Bilmiyorsanız yukarıdaki 1. adımı kullanın.

---

## 6. Yeni personel hesabı açma (personel portalı için)

1. Yönetici hesabıyla giriş yapın.
2. **Ayarlar** → **Kullanıcı Yönetimi** bölümüne inin.
3. Formu doldurun:
   - **Ad Soyad**: personelin adı
   - **E-posta**: personelin giriş adresi
   - **Şifre**: en az 8 karakter
   - **Rol**: **Personel** seçin
4. Rolü "Personel" yapınca altında **personel listesi** açılır.
   Oradan doğru kişiyi seçin (bu adım zorunludur).
5. **Kullanıcı Ekle** düğmesine basın.
6. Personel, kendi e-postası ve şifresiyle giriş yapınca **yalnızca kendi portalını** görür:
   profili, belgeleri, iş ilanları ve başvuruları.

> **Sık yapılan hata:** Rol "Personel" seçilip listeden kişi seçilmezse portal
> "Portalınız açılamadı — Hesabınız bir personel kaydına bağlı değil" uyarısı verir.
> Çözüm: o kullanıcıyı silip yukarıdaki adımları tekrarlayın ve personel kaydını seçin.

---

## 7. Güvenlik notları

- Şifreler veritabanında **şifrelenmiş (bcrypt)** olarak tutulur; kimse okuyamaz.
- Betikle yapılan her sıfırlama **denetim kaydına** (audit log) yazılır.
- Şifreyi e-posta/WhatsApp ile paylaşmayın; sözlü iletin.
- Kurulumu arkadaşınıza verirken **`.env` dosyasını paylaşmayın**, sadece program
  klasörünü kopyalayın ve ilk girişte şifreyi değiştirin.
