# 3. Adım — İlk Giriş ve Kullanım

## İlk giriş

1. Tarayıcıyı aç, adres çubuğuna yaz: `http://localhost:5173`
2. E-posta ve şifre: `.env` dosyasındaki `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
   - Varsayılan: `admin@crewintel.com` / `Admin1234!` (kurulumda değiştirmediysen)
3. **GİRİŞ YAP**'a bas.

İlk girişte sistem yönetici hesabını otomatik oluşturur. Ekranda turuncu bir
"Hoş geldin" kutusu ve sayaçlar görürsün.

> Şifreyi unuttuysan: `04-SORUN-GIDERME.md` → "Şifremi unuttum".

---

## Sol menüdeki ekranlar (yukarıdan aşağı)

| Menü | Ne işe yarar |
|---|---|
| **Panel (Dashboard)** | Genel özet: kaç personel, kaç gemi, süresi yaklaşan belgeler/kontratlar |
| **Personel** | Personel listesi, yeni personel ekleme, detay kartı |
| **Gemiler** | Gemi listesi ve gemi detayı (kadro, atamalar) |
| **Atamalar** | Kim hangi gemide, hangi tarihler arasında |
| **Kontratlar** | Kontrat süreleri, bitiş tarihleri |
| **Belgeler** | Yüklenen belgeler, eşleştirme, süre durumu |
| **Uygunluk (Eligibility)** | Hangi personel hangi gemi/pozisyon için uygun |
| **İş İlanları** | İlan aç, başvuru topla, duyur |
| **İletişim** | Personelle mesajlaşma, e-posta gönderme |
| **Ayarlar** | Şirket adı, logo, e-posta/şifre değiştirme |

---

## İlk 10 dakikada yapılması önerilenler

1. **Ayarlar** → Şirket adını ve logoyu gir → **Kaydet**. (Sol üstte görünür.)
2. **Gemiler** → **Yeni Gemi** → bir gemi ekle (ad, IMO numarası, bayrak).
3. **Personel** → **Yeni Personel** → bir personel ekle.
4. **Kontratlar** → o personel için kontrat oluştur (başlangıç/bitiş tarihi).
5. **Atamalar** → personeli gemiye ata.
6. **Belgeler** → **Belge Yükle** → pasaport/sertifika dosyası (PDF veya TXT)
   seç. Program belgeyi okuyup türünü tahmin eder; **onayla** dediğinde
   personele bağlanır.
7. **Panel** → sayıların güncellendiğini kontrol et.

### Belge yükleme kuralları

- Dosya boyutu en fazla **25 MB**.
- Desteklenen türler: **PDF** ve **TXT**. (Telefonla taranan belgeleri
  genellikle PDF olarak kaydedebilirsin.)
- Yüklenen dosyalar bilgisayarındaki `storage` klasöründe durur.
- Personelin kendi yüklediği belgeler **"onay bekliyor"** durumunda gelir;
  yönetici onaylayana kadar geçerli sayılmaz.

> Taranmış (resim) PDF'lerde metin okunamayabilir. Bu durumda belge türünü
> listeden elle seçebilirsin.

---

## Personel (crew) hesabı ile giriş

Personel kendi hesabıyla girdiğinde farklı bir ekran görür: kendi belgeleri,
kontratı, gemisi, başvurabileceği ilanlar ve mesajlar. Bu hesabı **Personel**
kartından "Portal erişimi" ile oluşturabilirsin.

---

## Günlük kullanım

| Ne yapmak istiyorsun | Nereye gideceksin |
|---|---|
| Yeni personel işe alındı | Personel → Yeni Personel |
| Belge süresi bitiyor | Panel'deki uyarılar / Belgeler → süre durumu |
| Personeli gemiye bindirdin | Atamalar → Yeni Atama |
| Kontrat yenilenecek | Kontratlar → ilgili kontratı düzenle |
| İlan açıp duyuracağım | İş İlanları → Yeni İlan → WhatsApp/E-posta |
| Personele yazı göndereceğim | İletişim → kişiyi seç → mesaj/e-posta |

Programı kapatmak için `KURULUM\durdur.bat`, tekrar açmak için
`KURULUM\baslat.bat` dosyasına çift tıkla. Tarayıcı sekmesini kapatman
programı durdurmaz.

Bir sonraki dosya: **`04-SORUN-GIDERME.md`**
