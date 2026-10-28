# CREWINTEL — Kurulum Rehberi (Başla Buradan)

Merhaba! Bu klasör, CREWINTEL programını **hiç bilgisayar bilmeyen** birinin bile
kurabilmesi için yazıldı. Sırayla oku, atlama.

## Bu program nedir?

CREWINTEL, gemi personeli (crew) yönetimi için bir program. İçinde:

- **Personel kartları** (pasaport, gemiadamı cüzdanı, sertifikalar, sağlık raporları)
- **Gemiler ve gemi kadrosu** (kim hangi gemide, hangi pozisyonda)
- **Kontratlar** (başlangıç/bitiş tarihleri, süresi yaklaşanlar)
- **Belge tarama/eşleştirme** (PDF/TXT yükleyince belgeyi tanıyıp personele bağlar)
- **İş ilanları** (ilan aç, başvuru topla, WhatsApp/e-posta ile duyur)
- **Personel portalı** (personel kendi belgelerini görür, ilanlara başvurur)
- **Mobil uygulama** (aynı sistemin telefon sürümü)

Program kendi bilgisayarında çalışır; internete veri göndermez. Veriler senin
bilgisayarındaki bir veritabanında durur.

## Kurulum kaç dakika sürer?

- İnternetten programları indirmek: **15–30 dakika** (internet hızına bağlı)
- Kurulumu çalıştırmak: **5–10 dakika** (ilk seferde biraz uzun)
- Sonraki açılışlar: **30 saniye**

## Sırayla yapılacaklar

| Adım | Dosya | Ne yapacaksın |
|---|---|---|
| 1 | `01-GEREKLI-PROGRAMLAR.md` | Bilgisayara kurulması gereken programları indireceksin |
| 2 | `02-KURULUM-ADIM-ADIM.md` | Projeyi kopyalayıp `kur.bat` dosyasına çift tıklayacaksın |
| 3 | `03-ILK-GIRIS-VE-KULLANIM.md` | İlk girişi yapacak, ekranları tanıyacaksın |
| 4 | `04-SORUN-GIDERME.md` | Bir şey ters giderse burada çözümü var |
| 5 | `05-YEDEKLEME-VE-GUNCELLEME.md` | Verilerini nasıl yedekleyeceğini öğreneceksin |
| 6 | `06-MOBIL-UYGULAMA.md` | (İsteğe bağlı) Telefon sürümünü kuracaksın |
| 7 | `07-SIFRE-VE-HESAP.md` | Şifreni unutursan / yeni kullanıcı açacaksan |

## Çift tıklanacak hazır dosyalar

| Dosya | Ne yapar |
|---|---|
| `kur.bat` | İlk kurulumu yapar (Docker imajlarını oluşturur, veritabanını hazırlar) |
| `baslat.bat` | Programı başlatır |
| `durdur.bat` | Programı kapatır |
| `sifre-sifirla.bat` | Şifre unutulduğunda yeni şifre üretir |
| `demo-veri-yukle.bat` | Örnek gemi/personel verisi ekler (deneme için) |
| `demo-veri-sil.bat` | Örnek verileri temizler |
| `sifirdan-kur.bat` | Her şeyi sıfırdan kurar (verileri siler, dikkatli kullan) |
| `sorun-raporu.bat` | Sorun bildirirken göndereceğin raporu oluşturur |

## Çok kısa özet (acele edenler için)

1. **Docker Desktop**'ı kur, bilgisayarı yeniden başlat, Docker'ı aç.
2. Proje klasörünü masaüstüne kopyala.
3. Klasörün içindeki `KURULUM\kur.bat` dosyasına **çift tıkla**.
4. Siyah pencere "KURULUM TAMAMLANDI" yazana kadar bekle.
5. Tarayıcı açılır → `http://localhost:5173` → kullanıcı: `.env` dosyasındaki
   `ADMIN_EMAIL`, şifre: `ADMIN_PASSWORD` (ilk kurulumda sorulur).
6. Şifreyi unuttuysan: `KURULUM\sifre-sifirla.bat` dosyasına çift tıkla
   (açıklama: `07-SIFRE-VE-HESAP.md`).

> **Not:** Bu rehberdeki komutları yazarken Türkçe karakter kullanma. Klasör
> adlarında boşluk olabilir, sorun değil — tırnak işareti kullanıyoruz.

Bir sonraki dosya: **`01-GEREKLI-PROGRAMLAR.md`**
