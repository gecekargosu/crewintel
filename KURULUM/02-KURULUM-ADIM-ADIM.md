# 2. Adım — Kurulumu Yapmak

Bu adımı **sırayla** yap. Her adımın sonunda ne görmen gerektiği yazıyor.

---

## Adım 1 — Docker'ın çalıştığını doğrula

1. Başlat menüsüne `Docker` yaz, **Docker Desktop**'ı aç.
2. Sol alt köşede **"Engine running"** (yeşil) yazısını görene kadar bekle
   (ilk açılışta 1–3 dakika sürebilir).

> Balina ikonu kırmızıysa Docker henüz hazır değildir, bekle.

---

## Adım 2 — Proje klasörünü bilgisayarına kopyala

**Seçenek A — GitHub'dan indirme (önerilen):**

1. Tarayıcıda <https://github.com/gecekargosu/crewintel> adresini aç.
2. Yeşil **`<> Code`** düğmesine bas → **Download ZIP**.
3. İnen `crewintel-main.zip` dosyasına sağ tıkla → **Tümünü ayıkla**
   (Extract All) → hedef olarak **Masaüstü**'nü seç.
4. Masaüstünde oluşan `crewintel-main` klasörünün adını `CREWINTEL` yap
   (sağ tık → Yeniden adlandır).

**Seçenek B — hazır klasörü kopyalama:**

1. Sana verilen `CREWINTEL` klasörünü **C:\CREWINTEL** olacak şekilde kopyala.
   (Program klasörünün içinde `KURULUM`, `backend`, `frontend` klasörleri
   görünüyor olmalı.)

> **Önemli:** Klasörü **OneDrive/Google Drive** gibi otomatik eşitlenen bir
> klasöre koymayın; dosya izinleri bozulup kurulum hata verebilir.

---

## Adım 3 — Ayar dosyasını oluştur

1. `CREWINTEL` klasörünü aç.
2. `.env.example` dosyasını kopyala (Ctrl+C) ve aynı klasöre yapıştır (Ctrl+V).
3. Kopyanın adını **`.env`** yap — sadece `.env`, başka ek yok.
   - Windows "Dosya adı uzantısı değişebilir" uyarısı verirse **Evet** de.
   - Dosya uzantılarını göremiyorsan: Dosya Gezgini → **Görünüm** →
     **Dosya adı uzantıları** kutusunu işaretle.

> Kolay yol: `KURULUM\kur.bat` dosyası bu adımı senin yerine yapar. O zaman bu
> adımı atlayabilirsin.

4. `.env` dosyasını Not Defteri ile aç ve şu satırları doldur:

   ```
   POSTGRES_PASSWORD=buraya_kendi_sifreni_yaz
   JWT_SECRET_KEY=buraya_uzun_rastgele_bir_yazi_yaz
   ADMIN_EMAIL=admin@crewintel.com
   ADMIN_PASSWORD=buraya_kendi_yonetici_sifreni_yaz
   ```

   - `POSTGRES_PASSWORD`: veritabanı şifresi (en az 8 karakter).
   - `JWT_SECRET_KEY`: rastgele uzun bir yazı (ör. `a8f3k2m9x7q1...`).
   - `ADMIN_EMAIL` / `ADMIN_PASSWORD`: programa **ilk girişte** kullanacağın
     yönetici hesabı. Şifreyi bir yere not et!

---

## Adım 4 — Kurulumu çalıştır

1. `KURULUM` klasörünü aç.
2. **`kur.bat`** dosyasına **çift tıkla**.
3. Siyah bir pencere açılır. Şunları yapar:
   - Docker'ın çalışıp çalışmadığını kontrol eder
   - `.env` yoksa oluşturur
   - Programın 3 parçasını (veritabanı, sunucu, arayüz) indirir ve başlatır
   - Hazır olunca tarayıcıyı açar
4. **İlk kurulum 5–15 dakika sürebilir** (internetten indirme yapılır).
   Pencereyi **kapatma**.
5. `KURULUM TAMAMLANDI` yazısını görünce işlem bitti.

> "Windows protected your PC" uyarısı çıkarsa: **More info** → **Run anyway**.
> Bu uyarı, dosyanın imzasız bir betik olmasından kaynaklanır.

---

## Adım 5 — Programa gir

1. Tarayıcı kendiliğinden açılmazsa adres çubuğuna yaz: `http://localhost:5173`
2. **E-posta**: `.env` dosyasındaki `ADMIN_EMAIL`
3. **Şifre**: `.env` dosyasındaki `ADMIN_PASSWORD`
4. **GİRİŞ YAP** düğmesine bas.

Ekranda turuncu bir "Hoş geldin" kutusu ve personel/gemi sayıları görürsen
kurulum **başarılı**.

---

## Adım 6 — Demo verisini yükle (isteğe bağlı ama önerilir)

Program boş açılır. Nasıl göründüğünü görmek için örnek veri yükleyebilirsin:

1. `KURULUM` klasöründeki **`demo-veri-yukle.bat`** dosyasına çift tıkla.
2. 10 personel, 4 gemi, kontratlar ve örnek belgeler eklenir.

> Demo verisini **silmek** için: `demo-veri-sil.bat` (dikkat: tüm personel ve
> belgeleri siler, sadece deneme kurulumlarında kullan).

---

## Kurulumu durdurmak / yeniden başlatmak

| Ne istiyorsun | Yapacağın |
|---|---|
| Programı kapat | `KURULUM\durdur.bat` |
| Tekrar aç | `KURULUM\baslat.bat` |
| Bilgisayar her açıldığında çalışsın | Docker Desktop ayarlarında "Start Docker Desktop when you sign in" işaretli olsun; program konteynerleri otomatik başlar |
| Her şeyi sıfırla (veriler silinir) | `KURULUM\sifirdan-kur.bat` |

Bir sonraki dosya: **`03-ILK-GIRIS-VE-KULLANIM.md`**
