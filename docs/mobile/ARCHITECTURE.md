# CREWINTEL MOBILE — MİMARİ TASARIM (ÜRÜN + SİSTEM)

> Durum: **v2 — KARAR VERİLDİ, M1 başladı.** Revizyon kararları için `docs/mobile/DECISIONS.md`.
> Tarih: 2026-08-18 · Faz: Mobile Design (Phase M0 → M1)

---

## 1. ÖZET

CREWINTEL Mobile, masaüstü CREWINTEL'den **ayrı bir sistem değil**, onun mobil istemcisidir.

**Temel ilke: "Bir sistem, iki istemci, tek gerçek veri kaynağı."**

```
                 ┌──────────────────────────┐
                 │     CREWINTEL BACKEND    │
                 │  FastAPI + PostgreSQL    │
                 │  + Storage + Redis(i)    │
                 └────────────┬─────────────┘
                              │ HTTPS / REST (+ WebSocket)
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
   ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
   │  MASAÜSTÜ WEB   │ │  MOBİL APP   │ │  WhatsApp /  │
   │  (mevcut Vite)  │ │  (yeni)      │ │  Webhook     │
   └─────────────────┘ └──────────────┘ └──────────────┘
```

Mevcut kodda bunun omurgası **zaten var** (doğrulandı):

| Parça | Mevcut durum |
|---|---|
| `User` + rol sistemi (`admin/hr/viewer/crew`) | ✅ `app/models/user.py`, `api/deps.py` |
| JWT + bcrypt + rate limiter | ✅ `app/core/security.py`, `api/routes/auth.py` |
| Crew self-service portal (`/api/portal/*`) | ✅ `api/routes/portal.py` — profil, belge yükleme (onay kuyruğu), iş ilanları, başvuru, iş arıyorum |
| İş ilanı + başvuru havuzu | ✅ `models/job.py`, `api/routes/jobs.py` |
| Bildirim modeli | ✅ `models/notification.py`, `api/routes/notifications.py` |
| WhatsApp gönderim kuyruğu + webhook | ✅ `models/job.py` (WhatsAppMessage), webhook route |
| Uygunluk motoru (`/api/crew/eligible`) | ✅ Phase 4B |

**Yani mobil uygulamanın işi:** backend'i yeniden yazmak değil; (a) mobil API katmanını genişletmek, (b) push bildirim + mesajlaşma gibi eksik parçaları eklemek, (c) React Native istemciyi inşa etmek.

---

## 2. ÜÇ KULLANICI TİPİ (MOBİL)

Mobil uygulamada rol **yeni bir rol tanımı gerektirmez** — mevcut rol + flag kombinasyonundan türetilir:

| Tip | Mevcut karşılık | Ayırt edici durum |
|---|---|---|
| **ADMIN** | `admin` / `hr` | Kullanıcı yönetim ekranı; portföydeki herkese erişim |
| **İŞ ARAYAN PERSONEL** | `crew` + `job_seeking = true` | Aday havuzunda; ilanları görür, başvurur |
| **PORTFÖY PERSONELİ** | `crew` + `job_seeking = false` + aktif atama/kontrat | Kendi gemisi, kontratı, belgeleri; öneri ilanları |

Üçü de **aynı `crew` rolüyle** giriş yapar; kullanıcının gördüğü ekran seti `job_seeking`, `availability`, aktif atama ve kontrat durumundan türetilir. Bu, mevcut yetkilendirme modelini bozmadan mobilde üç farklı deneyim sunmamızı sağlar.

> Not: Mobil uygulamada "iş arayan" ve "portföy" ayrımı **veritabanında yeni rol** değil, **durum** olarak ele alınır. Böylece admin masaüstünden personelin durumunu değiştirdiğinde mobil deneyim otomatik güncellenir.

---

## 3. YETKİ MATRİSİ (MOBİL)

| Özellik | Admin | İş Arayan | Portföy Personeli |
|---|:---:|:---:|:---:|
| Giriş / profil görüntüleme | ✅ | ✅ (kendi) | ✅ (kendi) |
| Profil düzenleme | ✅ (hepsi) | ✅ (kendi iletişim + tercihler) | ✅ (kendi iletişim) |
| Belge görüntüleme | ✅ (hepsi) | ✅ (kendi) | ✅ (kendi) |
| Belge yükleme | ✅ (yönetir) | ✅ (kendi → onay kuyruğu) | ✅ (kendi → onay kuyruğu) |
| Belge onaylama/reddetme | ✅ | ❌ | ❌ |
| İş ilanı listesi | ✅ | ✅ | ✅ |
| İş ilanı oluşturma/düzenleme | ✅ | ❌ | ❌ |
| İş başvurusu | ❌ (yönetir) | ✅ | ✅ (öneri üzerinden) |
| Başvuru takibi | ✅ (havuz) | ✅ (kendi) | ✅ (kendi) |
| "İş arıyorum" anahtarı | ✅ (yönetir) | ✅ (kendisi açar/kapatır) | ✅ |
| Aktif gemi / kontrat görüntüleme | ✅ | — | ✅ (kendi) |
| Mesajlaşma | ✅ (tüm personel) | ✅ (admin ile) | ✅ (admin ile) |
| Bildirim alma | ✅ | ✅ | ✅ |
| Personel arama / tüm liste | ✅ | ❌ | ❌ |
| Uygun aday bulma | ✅ | ❌ | ❌ |
| Dashboard istatistikleri | ✅ | kendi özeti | kendi özeti |

**Kritik kural:** Mobil uygulamada hiçbir yetki kontrolü sadece UI'da yapılmaz. Backend `require_roles` + `crew_member_id` eşleşmesi ile **her isteği** doğrular (IDOR koruması: crew kullanıcısı yalnızca kendi `crew_member_id`'sine erişebilir).

---

## 4. MODÜL MİMARİSİ

```
MOBİL UYGULAMA MODÜLLERİ
├── AUTH
│   ├── Login / Logout / Oturum
│   ├── Kayıt (self-registration → admin onayı)
│   ├── Şifre sıfırlama (admin onaylı veya mail)
│   └── Cihaz kaydı (push token)
├── HOME (role-göre dashboard)
│   ├── İş Arayan: yeni ilanlar, uygun ilanlar, belge uyarıları
│   ├── Portföy: aktif gemi, kontrat geri sayımı, öneri ilanlar
│   └── Admin: bugün özeti (expiring docs, başvurular, onay bekleyenler)
├── PROFILE (maritime professional profile)
│   ├── Kişisel bilgiler
│   ├── Denizcilik profili (rank, deneyim, gemi tipleri, diller)
│   ├── İş tercihleri (aranan pozisyon, bölge, maaş, müsaitlik tarihi)
│   └── İletişim güncelleme
├── DOCUMENTS
│   ├── Belge listesi (durum: valid/expiring/expired/pending)
│   ├── Belge yükleme (PDF/foto → onay kuyruğu)
│   ├── Belge görüntüleme/indirme
│   └── Süre uyarıları
├── CONTRACTS
│   ├── Aktif kontrat (geri sayım)
│   ├── Kontrat geçmişi
│   └── Bitiş yaklaşınca öneri ilanlar
├── JOBS
│   ├── İlan listesi + arama + filtre
│   ├── İlan detayı
│   ├── Başvur (tek dokunuş)
│   └── Başvurularım (durum takibi)
├── MESSAGING
│   ├── Konuşma listesi
│   ├── Mesaj + dosya paylaşımı
│   └── Okundu durumu
├── NOTIFICATIONS
│   ├── Sistem bildirimleri (belge/kontrat/ilan/onay)
│   └── Push notification (uygulama kapalıyken)
└── ADMIN (sadece admin/hr)
    ├── Bugün özeti
    ├── Personel arama
    ├── Başvuru havuzu (incele/ön eleme)
    ├── Belge onay kuyruğu (onayla/reddet)
    ├── İlan yönetimi (aç/kapat/yayınla)
    └── Uygun aday önerileri
```

---

## 5. OFF-LINE İLKELERİ (GEMİDE İNTERNET YOK)

Denizci her zaman hızlı internete sahip değildir → **offline-first** tasarım:

```
UYGULAMA (yerel)
├── AsyncStorage / SQLite: profil, belge meta, ilanlar, mesajlar
└── Sync kuyruğu: internet gelince gönderilecek işlemler

İNTERNET GELDİĞİNDE
  yerel veri ──sync──▶ CREWINTEL API ──▶ PostgreSQL
```

**MVP kuralı:** Okuma işlemleri (profil, belge listesi, ilan listesi, mesaj geçmişi) yerel önbellekten sunulur, arka planda tazelenir. Yazma işlemleri (başvuru, belge yükleme, mesaj) çevrimiçiyken yapılır; çevrimdışıysa kuyruğa alınır ve senkron edilir. Belge PDF'lerinin kendisi indirilir ve cihazda saklanır (küçük boyut limiti ile).

---

## 6. PUSH BİLDİRİM AKIŞI

```
Admin (web) veya sistem zamanlayıcı
        │
        ▼
Backend NotificationService
        │
        ├── Notification tablosu (kalıcı, okundu/okunmadı)
        └── Push gönderimi
              ├── Expo Push API / FCM (Android) + APNs (iOS)
              └── user_devices tablosundaki token'lara
                    ▼
              Personelin telefonu (uygulama kapalıyken bile)
```

Örnek tetikleyiciler (backend'de zamanlayıcı/istek sonrası):
- Belge 30/14/7 gün kala süresi dolacak → `medical belgeniz 15 gün sonra doluyor`
- Kontrat 60/30/14/7 gün kala → `kontratınız 30 gün içinde sona eriyor`
- Yeni uygun ilan yayınlandı → `profilinize uygun yeni ilan: Chief Officer`
- Belge onaylandı/reddedildi → `yüklediğiniz belge onaylandı`
- Admin mesajı → `CREWINTEL'den yeni mesajınız var`

---

## 7. TEKNOLOJİ SEÇİMİ

| Katman | Seçim | Gerekçe |
|---|---|---|
| Mobil çatı | **React Native + Expo (TypeScript)** | Mevcut frontend React tabanlı; tek kod tabanı Android+iOS; EAS Build ile mağaza dağıtımı kolay |
| Backend | **Mevcut FastAPI (genişletilecek)** | Yeni backend YOK. API-first yaklaşım |
| Veritabanı | **Mevcut PostgreSQL** | Tek veri kaynağı |
| Push | **expo-notifications (FCM + APNs)** | Expo üzerinden her iki platform |
| Token saklama | **expo-secure-store** | JWT cihazda güvenli |
| State | **TanStack Query + Zustand** | Sunucu state / istemci state ayrımı |
| Navigasyon | **expo-router** | Dosya tabanlı, basit |
| Mesajlaşma | Backend REST (MVP) → WebSocket (v2) | Kademeli |

**İlk hedef: Android (Play Store).** iOS sonra TestFlight ile.

---

## 8. GÜVENLİK MODELİ

1. **HTTPS zorunlu** — üretimde yalnızca `https://` (Named Tunnel / domain + SSL).
2. **JWT** mevcut altyapı; mobilde token `SecureStore`'da, asla AsyncStorage'da değil.
3. **RBAC server-side** — tüm mobil uçlar `require_roles` + `crew_member_id` doğrulaması.
4. **IDOR koruması** — crew kullanıcısı `crew_id`'sini parametre olarak gönderemez; backend token'daki `user.crew_member_id`'yi kullanır.
5. **Kayıt akışı** — self-registration `pending` kullanıcı oluşturur; admin onaylamadan giriş yapamaz, onaylanınca `crew` rolü + `crew_member` kaydı aktif olur.
6. **Belge erişimi** — indirme uçları token ister; crew yalnızca kendi belgelerini indirebilir.
7. **Audit** — mobil kayıt, başvuru, belge yükleme, mesaj, onay işlemleri `audit_logs`'a yazılır (user identity ile).
8. **Rate limiting** — login zaten sınırlı; kayıt ve mesaj uçlarına da sınır eklenir.

---

## 8.5 v2 DEĞİŞİKLİKLERİ (41 öneri sonrası)

1. **Üç tip = rol + durum** (yeni rol yok) — `job_seeking`, `availability`, aktif kontrat türetimi.
2. **`available_from`** + iş tercihleri (`job_preferences` JSON, yapısal maaş alanları) eklendi.
3. **Matching:** mevcut `eligibility.score_crew` kural-bazlı motoru ilan eşleştirmede kullanılır (AI değil).
4. **Mesajlaşma REST** (M1); WebSocket M2+. `messages.kind`: chat/system/job_alert/document_alert/contract_alert.
5. **Offline:** M1'de READ önbellek, WRITE çevrimiçi; senkron kuyruk M2+.
6. **Kayıt:** self-registration (min. alan) → admin onayı.
7. **OCR yok** (M1); belge tipi kullanıcı seçer + admin onayı.
8. **Hesap silme = deaktivasyon** (`is_active=false`), veri silme yok.
9. **Eğlence modülleri** (müzik/oyun/kitap/foto/harita/sosyal) M4 — fizibilite `DECISIONS.md` §1.

## 9. FAZ PLANI (M0 → M4)

| Faz | İçerik | Çıktı |
|---|---|---|
| **M0 (BU DOKÜMAN)** | Mimari + mühendislik tasarımı | Onaylanacak tasarım |
| **M1 — MVP** | Backend: mobile API genişletme, kayıt akışı, push altyapısı, migration 0010. Mobil: Auth, Home, Profil, Belgeler, İlanlar+Başvuru, Bildirimler | Play Store'da çalışan ilk sürüm (Android) |
| **M2 — Portföy** | Aktif gemi/kontrat ekranı, kontrat geri sayımı, öneri ilanlar, mesajlaşma | Çalışan personel için tam deneyim |
| **M3 — Admin mobil** | Başvuru havuzu, belge onay kuyruğu, ilan yönetimi, uygun aday, dashboard | Admin telefonda müdahale edebilir |
| **M4 — Zeka + Ekosistem** | Akıllı eşleştirme önerileri, QR Crew ID, joining checklist, seyir/travel bilgileri, offline senkron | Farklılaşan ürün |

**Kural:** Her faz bitince pytest + build + canlı doğrulama + `DEVELOPMENT_LOG.md` kaydı. Mevcut 199 test ve masaüstü özellikleri hiçbir fazda bozulmaz.

---

## 10. AÇIK KARARLAR (ONAY GEREKLİ)

1. **İlk platform:** Android mi yoksa iOS+Android birlikte mi? (Öneri: önce Android)
2. **Kayıt:** Herkes uygulamadan kayıt olabilsin mi, yoksa admin mi oluştursun? (Öneri: self-registration + admin onayı)
3. **Mesajlaşma:** MVP'de sadece admin↔personel ikili mesajlaşma yeterli mi?
4. **Marka:** Uygulama adı **"CREWINTEL CREW"** (ChatGPT önerisi) uygun mu?
5. **Mevcut portal API'si** (`/api/portal/*`) mobilde aynen kullanılsın mı, yoksa `/api/mobile/*` ayrı namespace mi? (Öneri: portal'ı genişlet, çift API tutma)

---

## 11. RİSKLER

| Risk | Seviye | Azaltma |
|---|---|---|
| Push bildirim altyapısı (FCM/APNs hesap gerekir) | ORTA | Expo Push ile tek entegrasyon; Google hesabı yeterli (MVP) |
| Cihazda token güvenliği | ORTA | SecureStore + kısa ömürlü token |
| Mağaza onay süreci | DÜŞÜK | Kişisel veri (pasaport) → KVKK/GDPR uyum notu, gizlilik politikası |
| Offline senkron çakışmaları | ORTA | M1'de yazma işlemleri çevrimiçi; offline sadece okuma |
| Mevcut sistemi bozma riski | DÜŞÜK | Tüm yeni uçlar ayrı router; mevcut route'lar değişmez; regression testleri |
