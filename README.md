# CREWINTEL — Gemi Personeli Yönetim Sistemi

Gemi adamı (crew) özlük kayıtları, gemi atamaları, kontratlar, belge arşivi ve
belge→personel otomatik eşleştirme, iş ilanları ve personel portalı. Tek
bilgisayarda, kendi veritabanıyla çalışır.

| Parça | Teknoloji | Adres |
|---|---|---|
| Masaüstü arayüzü (tarayıcıda açılır) | React + Vite | <http://localhost:5173> |
| Sunucu (API) | Python / FastAPI | <http://localhost:8000> |
| Veritabanı | PostgreSQL 17 (Docker) | localhost:5433 |
| Mobil uygulama | Expo / React Native | `mobile/` |

---

## Hızlı kurulum (5 adım)

> Ayrıntılı, hiç bilgisayar bilmeyen biri için yazılmış rehber:
> **[KURULUM/00-BASLA-BURADAN.md](KURULUM/00-BASLA-BURADAN.md)**

1. **Docker Desktop** kur → bilgisayarı yeniden başlat → Docker'ı aç.
   <https://www.docker.com/products/docker-desktop/>
2. Bu depoyu indir (**Code → Download ZIP**) ve bir klasöre çıkar.
   Klasör yolunda Türkçe karakter / OneDrive olmasın (ör. `C:\CREWINTEL`).
3. `KURULUM\kur.bat` dosyasına **çift tıkla**. İlk kurulum 5–15 dakika sürer.
   Betik `.env` dosyasını oluşturur ve yönetici şifresini sorar.
4. Tarayıcıda <http://localhost:5173> aç.
5. `.env` içindeki `ADMIN_EMAIL` / `ADMIN_PASSWORD` ile giriş yap.

Sonraki açılışlar: `KURULUM\baslat.bat` · Kapatma: `KURULUM\durdur.bat`
Örnek veri: `KURULUM\demo-veri-yukle.bat`

### Elle kurulum (Docker bilenler için)

```bash
cp .env.example .env      # POSTGRES_PASSWORD, JWT_SECRET_KEY, ADMIN_* doldur
docker compose up -d --build
docker compose exec -T backend python -m app.db.demo   # isteğe bağlı örnek veri
```

---

## Özellikler

- **Personel**: özlük bilgileri, pasaport/gemiadamı cüzdanı, sertifikalar,
  sağlık raporları, deniz hizmeti, dil ve iletişim bilgileri.
- **Gemiler & atamalar**: gemi kadrosu, pozisyon, tarih aralığı, çakışma kontrolü.
- **Kontratlar**: başlangıç/bitiş, süresi yaklaşanlar için uyarı.
- **Belge yönetimi**: PDF, Word (DOCX), Excel (XLSX), TXT ve resim (JPG/PNG)
  yükleme (en fazla 25 MB). Metin çıkarma + OCR (Türkçe/Rusça/Arapça/İngilizce),
  otomatik belge türü tahmini, pasaport MRZ okuma (doğum/bitiş tarihi, uyruk,
  belge numarası — belgenin dili ne olursa olsun), arşivleme ve süre takibi.
- **Eşleştirme motoru**: kimlik numarası + isim + dosya adı + metin sinyalleri
  ile belgeyi personele bağlar; düşük güvenli eşleşmeler onay bekler.
- **İş ilanları & portal**: ilan aç, başvuru topla, personel kendi belgelerini
  ve kontratını görsün.
- **Mobil uygulama (personel)**: giriş, belge yükleme, ilanlar/başvurular,
  bildirimler, iletişim bilgisi düzenleme, dil seçimi. Yalnızca **personel
  (crew)** hesapları içindir; yönetici/İK hesapları masaüstü panelini kullanır.
- **İletişim**: personelle mesajlaşma, e-posta gönderme.
- **4 dil**: Türkçe, İngilizce, Rusça, Arapça (masaüstü + mobil).
- **Rol bazlı yetki**: admin / hr / viewer / crew.

---

## Klasör yapısı

```
CREWINTEL/
├── backend/          FastAPI uygulaması, modeller, belge işleme servisleri
├── frontend/         React arayüzü (Vite, Docker'da nginx ile servis edilir)
├── mobile/           Expo/React Native telefon uygulaması
├── KURULUM/          Kurulum rehberi ve .bat dosyaları  ← buradan başla
├── sample_documents/ Örnek belgeler (demo/test için)
├── scripts/          Geliştirici betikleri (seed, doğrulama)
├── tests/            API ve servis testleri (pytest)
├── docs/             Mimari, geliştirme günlüğü, yol haritası
├── storage/          Yüklenen belgeler (yedeklenmeli, depoya gitmez)
├── docker-compose.yml
└── .env.example      Ayar şablonu → .env olarak kopyalanır
```

---

## Sık kullanılan komutlar

```bash
docker compose ps                 # servisler çalışıyor mu
docker compose logs -f backend    # sunucu logları
docker compose down               # durdur
docker compose up -d --build      # kod değişince yeniden derle
```

Sağlık kontrolü: <http://localhost:8000/health> (<http://localhost:8000/health/database>)
· API dokümanı:
<http://localhost:8000/docs>

### Testler

```bash
cd backend
python -m pytest ../tests -q
```

---

## Belgeler

| Dosya | İçerik |
|---|---|
| [KURULUM/00-BASLA-BURADAN.md](KURULUM/00-BASLA-BURADAN.md) | Sıfırdan kurulum rehberi (hiç bilmeyenler için) |
| [KURULUM/04-SORUN-GIDERME.md](KURULUM/04-SORUN-GIDERME.md) | Sık karşılaşılan sorunlar ve çözümleri |
| [KURULUM/05-YEDEKLEME-VE-GUNCELLEME.md](KURULUM/05-YEDEKLEME-VE-GUNCELLEME.md) | Yedekleme, geri yükleme, güncelleme |
| [docs/HATA_ANALIZI_2026-10-29.md](docs/HATA_ANALIZI_2026-10-29.md) | **Son** kullanıcı senaryosu testi + hata/düzeltme raporu (masaüstü + mobil) |
| [docs/HATA_ANALIZI_2026-10-28.md](docs/HATA_ANALIZI_2026-10-28.md) | Önceki tur hata/düzeltme raporu |
| [docs/GITHUB_DURUM_VE_YAPILACAKLAR.md](docs/GITHUB_DURUM_VE_YAPILACAKLAR.md) | Depo durumu ve yayın öncesi yapılacaklar |

## Sorun giderme

En sık görülen 20 sorun ve çözümü: **[KURULUM/04-SORUN-GIDERME.md](KURULUM/04-SORUN-GIDERME.md)**

Kısa cevaplar:

| Belirti | Çözüm |
|---|---|
| `docker` bulunamadı | Docker Desktop kurulu değil / bilgisayar yeniden başlatılmadı |
| Sayfa açılmıyor | İlk derleme sürüyor (5–15 dk) → `docker compose ps` kontrol et |
| Giriş yapamıyorum | `.env` içindeki `ADMIN_EMAIL` / `ADMIN_PASSWORD` |
| Port dolu (5173/8000/5433) | O portu kullanan programı kapat → `baslat.bat` |
| Belge yüklenmiyor | En fazla 25 MB; PDF, DOCX, XLSX, TXT veya resim olmalı |
| Mobilde "bu uygulama personel içindir" diyor | Mobil yalnızca personel hesapları içindir; yönetici girişini masaüstünde yapın |

---

## Güvenlik notları

- `.env` dosyası **depoya eklenmez**; şifreler yalnızca sizin bilgisayarınızda.
- Üretimde `JWT_SECRET_KEY` ve `POSTGRES_PASSWORD` mutlaka değiştirilmeli.
- Yüklenen belgeler `storage/` altında tutulur ve depoya gönderilmez.
- Program internete veri göndermez; tüm veriler yerel PostgreSQL'dedir.

## Lisans

Özel proje — izinsiz dağıtılamaz.
