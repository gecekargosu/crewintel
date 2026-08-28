# 🧪 CREWINTEL — İNSAN TESTİ KONTROL LİSTESİ

> **Amaç:** Pazartesi sunumundan önce gerçek kullanıcı perspektifinden test
> **Tarih:** 2026-08-28
> **Test ortamı:** Docker (`docker compose up -d --build`) → `http://localhost:5173`

---

## 🔐 A. GİRİŞ SİSTEMİ

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| A1 | `http://localhost:5173` aç | Login ekranı görünüyor (CREWINTEL logosu, Email/Password, LOGIN butonu) | ⬜ |
| A2 | Yanlış şifre gir → LOGIN tıkla | "Geçersiz e-posta veya şifre" hata mesajı | ⬜ |
| A3 | Doğru email + şifre gir → LOGIN | Dashboard açılıyor | ⬜ |
| A4 | Sayfa yenile → Dashboard hâlâ açık mı? | Token korunuyor, tekrar login gerekmez | ⬜ |
| A5 | Logout yap | Login ekranına dönüyor | ⬜ |
| A6 | 10 kere yanlış şifre gir (aynı email) | 429 Rate Limit hatası | ⬜ |

---

## 👥 B. PERSONEL (CREW)

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| B1 | Personel sayfasına git | Liste yükleniyor, personel kartları görünüyor | ⬜ |
| B2 | "Personel Ekle" → form doldur → Kaydet | Yeni personel oluştu, listede görünüyor | ⬜ |
| B3 | Personel adına tıkla → detay sayfası | Tüm bilgiler görünüyor (pozisyon, uyruk, ehliyet, telefon, email) | ⬜ |
| B4 | Personel düzenle → pozisyon değiştir → Kaydet | Değişiklik korunuyor | ⬜ |
| B5 | Personel sil → Onay iste → Onayla | Personel listeden kalktı | ⬜ |
| B6 | Arama kutusuna isim yaz | Gerçek zamanlı filtreleme çalışıyor | ⬜ |
| B7 | Pozisyon filtresi seç → Filtrele | Sadece ilgili pozisyondaki personel görünüyor | ⬜ |
| B8 | CSV Export tıkla | CSV dosyası indiriliyor | ⬜ |

---

## 🚢 C. GEMİLER

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| C1 | Gemi sayfasına git | Gemi listesi yükleniyor | ⬜ |
| C2 | "Gemi Ekle" → IMO numarası, isim, tip gir → Kaydet | Yeni gemi oluştu | ⬜ |
| C3 | Gemi detayına tıkla | Gemi bilgileri + kadro planı görünüyor | ⬜ |
| C4 | Kadro pozisyonu ekle (örn. "Kaptan - 2") | Pozisyon eklendi, açık/k dolu sayıları doğru | ⬜ |
| C5 | Pozisyon sil | Pozisyon listeden kalktı | ⬜ |

---

## 📄 D. BELGELER

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| D1 | Belgeler sayfasına git | Belge listesi yükleniyor | ⬜ |
| D2 | PDF dosyası sürükle-bırak ile yükle | "Yüklendi" mesajı, listede görünüyor | ⬜ |
| D3 | Birden fazla dosya seç → yükle | Toplu yükleme çalışıyor, progress bar görünüyor | ⬜ |
| D4 | Belge tipi filtresi (örn. "Pasaport") | Sadece pasaport belgeleri görünüyor | ⬜ |
| D5 | Eşleştirme durumu filtresi ("pending") | Sadece bekleyen belgeler görünüyor | ⬜ |
| D6 | Belge detayına tıkla | Belge bilgileri, eşleşme durumu, personel bağlantısı görünüyor | ⬜ |
| D7 | Belge indir | PDF dosyası indiriliyor | ⬜ |

---

## 📋 E. KONTRATLAR

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| E1 | Kontrat sayfasına git | Kontrat listesi yükleniyor | ⬜ |
| E2 | "Kontrat Ekle" → personel + gemi seç → tarih aralığı gir | Kontrat oluştu | ⬜ |
| E3 | Yaklaşan süre sonu filtresi (30 gün) | 30 gün içinde bitecek kontratlar görünüyor | ⬜ |

---

## 📊 F. DASHBOARD

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| F1 | Dashboard'a git | Özet kartları görünüyor (toplam personel, gemi, belge) | ⬜ |
| F2 | Expiration kartları | expired / urgent / approaching / valid sayıları görünüyor | ⬜ |
| F3 | Görev listesi | Yaklaşan süre sonları ve açık kadro pozisyonları listeleniyor | ⬜ |

---

## 🤖 G. AI MODÜLLERİ

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| G1 | `curl http://localhost:8000/api/ai/health` | `llm_available: true` | ⬜ |
| G2 | `curl -X POST http://localhost:8000/api/ai/analyze -H "Content-Type: application/json" -d '{"text":"Name: John Smith, Passport: U1234567"}'` | document_type, person_name, confidence dönüyor | ⬜ |

---

## ⚙️ H. AYARLAR

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| H1 | Ayarlar sayfasına git | Ayarlar yükleniyor | ⬜ |
| H2 | WhatsApp admin numarası gir → Kaydet | Numara kaydedildi | ⬜ |
| H3 | Geçersiz numara gir → Kaydet | Hata mesajı (400) | ⬜ |

---

## 🌍 İ. ÇEVİRİ (i18n)

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| İ1 | Dil değiştir (TR → EN) | Tüm menüler ve metinler İngilizce | ⬜ |
| İ2 | Tekrar TR'ye çevir | Türkçe metinler geri geldi | ⬜ |
| İ3 | Sayfa yenile → dil seçimi korunuyor mu? | Evet | ⬜ |

---

## 📱 J. RESPONSIVE (MOBİL GÖRÜNÜM)

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| J1 | Tarayıcı genişliğini 768px'e küçült | Mobil görünüm aktif oluyor | ⬜ |
| J2 | Hamburger menü aç | Tüm sayfa linkleri görünüyor | ⬜ |
| J3 | Bir sayfaya git → menüyü kapat | Sayfa doğru yükleniyor | ⬜ |

---

## 🔒 K. YETKİLENDİRME (RBAC)

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| K1 | Viewer hesabıyla giriş yap | Dashboard açılıyor | ⬜ |
| K2 | Viewer ile "Personel Ekle" tıkla | Buton görünmüyor veya 403 hatası | ⬜ |
| K3 | Viewer ile belge yükle | Başarısız (403) | ⬜ |
| K4 | Viewer ile Audit Log sayfasına git | Erişim engellendi (403) | ⬜ |
| K5 | Admin ile her şeyi yapabiliyor mu? | CRUD, silme, ekleme tamamen çalışmalı | ⬜ |
| K6 | Viewer ile `curl -X POST http://localhost:8000/api/ai/analyze -H "Authorization: Bearer VIEWER_TOKEN" -d '{"text":"test"}'` | 403 Forbidden | ⬜ |
| K7 | Token olmadan AI endpoint çağır | 401 Unauthorized | ⬜ |

---

## 🐳 L. DOCKER BAŞLANGICI

| # | Test | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| L1 | `docker compose down && docker compose up -d --build` | 3 konteyner ayağa kalkıyor (frontend, backend, postgres) | ⬜ |
| L2 | `curl http://localhost:8000/health` | `{"status":"healthy"}` | ⬜ |
| L3 | `curl http://localhost:5173` | HTML dönüyor | ⬜ |
| L4 | `curl http://localhost:8000/api/ai/health` | `llm_available: true` | ⬜ |

---

## 📝 TEST SONUÇ TABLOSU

| Kategori | Toplam | Geçen | Başarısız | Not |
|----------|--------|-------|-----------|-----|
| A. Giriş | 6 | | | |
| B. Personel | 8 | | | |
| C. Gemiler | 5 | | | |
| D. Belgeler | 7 | | | |
| E. Kontratlar | 3 | | | |
| F. Dashboard | 3 | | | |
| G. AI | 2 | | | |
| H. Ayarlar | 3 | | | |
| İ. Çeviri | 3 | | | |
| J. Responsive | 3 | | | |
| K. RBAC | 7 | | | |
| L. Docker | 4 | | | |
| **TOPLAM** | **54** | | | |

---

## ⚠️ BİLİNEN SINIRLILIKLAR

1. ~~**AI endpoint'lerinde RBAC yok**~~ ✅ Düzeltildi (2026-08-28, P0 fix) — Viewer/crew → 403, unauth → 401
2. **App.jsx monolitik** — 5066 satır tek dosya, refactor edilmeli
3. **Frontend'de AI paneli yok** — Backend hazır ama arayüzde bağlantı yok
4. **Rate limiting memory'de** — Backend restart sonrası sıfırlanıyor
5. **WebSocket/real-time yok** — Bildirimler için sayfa yenileme gerekiyor
6. **2 migration'da boş downgrade** (0003, 0004) — geri alınamaz
7. **CI/CD yok** — testler otomatik tetiklenmiyor

---

## ✅ BAŞARI KRİTERLERİ

- Tüm **Kategori A-D** testleri geçmeli (giriş, personel, gemi, belge = temel işlevler)
- **Kategori L** (Docker) temiz başlangıç yapabilmeli
- **Kategori K** (RBAC) en azından admin/viewer ayrımı çalışmalı
- Kritik hata (crash, veri kaybı, beyaz ekran) olmamalı
- En az 45/52 test geçmeli (%86+)
