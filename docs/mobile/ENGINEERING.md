# CREWINTEL MOBILE — MÜHENDİSLİK TASARIMI

> Durum: **v2 — M1 backend uygulaması başladı.** Kararlar: `docs/mobile/DECISIONS.md`.
> Tarih: 2026-08-18 · Faz: Mobile Design (Phase M0 → M1)
> Temel: `docs/mobile/ARCHITECTURE.md`

---

## 1. GENEL BAKIŞ

Mevcut FastAPI backend **genişletilir**, yeni backend yazılmaz. Mevcut `/api/portal/*` uçları mobilin temeli olarak korunur ve üzerine eksik uçlar eklenir. Mobil istemci `mobile/` klasöründe Expo (React Native + TypeScript) projesi olarak inşa edilir.

```
backend/app
├── api/routes/
│   ├── portal.py        (MEVCUT — genişletilecek: mesajlaşma, kontrat/me, cihaz)
│   ├── auth.py          (MEVCUT — genişletilecek: kayıt akışı, refresh)
│   ├── jobs.py          (MEVCUT — mobil aynen kullanır)
│   ├── notifications.py (MEVCUT — mobil aynen kullanır)
│   └── ...
├── models/
│   ├── user.py          (MEVCUT)
│   ├── job.py           (MEVCUT)
│   └── YENİ: user_device.py, message.py
├── services/
│   ├── push.py          (YENİ — Expo/FCM gönderim)
│   └── notification.py  (MEVCUT — push çağrısı eklenir)
└── alembic/versions/
    └── 0010_mobile.sql  (YENİ migration)

mobile/
├── app/                 (expo-router ekranları)
├── src/
│   ├── api/             (REST client + token yönetimi)
│   ├── store/           (Zustand)
│   ├── components/
│   ├── hooks/           (TanStack Query)
│   └── utils/
├── app.json
└── package.json
```

---

## 2. VERİTABANI — MIGRATION 0010 (TEK, GERİYE DÖNÜK UYUMLU)

Mevcut migration head: `20260818_0009`. Yeni migration: `20260818_0010_mobile`.

### 2.1 `crew_members` — yeni alanlar (v2: yapısal maaş — karar #7)

| Alan | Tip | Açıklama |
|---|---|---|
| `available_from` | `Date NULL` | İş aramaya/müsaitliğe başlayabileceği tarih |
| `job_preferences` | `JSON NULL` | Aranan pozisyonlar, gemi tipleri, bölge, kontrat süresi |
| `vessel_types_experience` | `String NULL` | Çalıştığı gemi tipleri (virgülle) |
| `expected_salary_min` | `Integer NULL` | Maaş alt sınırı (örn. 3000) |
| `expected_salary_max` | `Integer NULL` | Maaş üst sınırı (örn. 4000) |
| `expected_salary_currency` | `String NULL` | Para birimi (örn. USD) |
| `expected_salary_period` | `String NULL` | Dönem (monthly / per_contract) |

### 2.2 Yeni tablo `user_devices` — push bildirim token'ları

```sql
CREATE TABLE user_devices (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform    VARCHAR(20) NOT NULL,          -- android | ios
    push_token  VARCHAR(255) NOT NULL,
    device_name VARCHAR(100),
    last_seen   TIMESTAMP,
    created_at  TIMESTAMP DEFAULT now(),
    UNIQUE (user_id, push_token)
);
CREATE INDEX ix_user_devices_user ON user_devices(user_id);
```

### 2.3 Yeni tablo `conversations` + `messages` — admin ↔ personel mesajlaşma (v2: kind — karar #11)

```sql
CREATE TABLE conversations (
    id           SERIAL PRIMARY KEY,
    participant_a INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- admin/hr
    participant_b INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- crew
    subject      VARCHAR(200),
    last_message_at TIMESTAMP,
    created_at   TIMESTAMP DEFAULT now()
);

CREATE TABLE messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_user_id  INTEGER NOT NULL REFERENCES users(id),
    kind            VARCHAR(30) NOT NULL DEFAULT 'chat',  -- chat/system/job_alert/document_alert/contract_alert
    body            TEXT,
    attachment_path VARCHAR(300),      -- opsiyonel dosya (storage/)
    read_at         TIMESTAMP,
    created_at      TIMESTAMP DEFAULT now()
);
CREATE INDEX ix_messages_conversation ON messages(conversation_id, created_at);
```

### 2.4 `user_devices` + `job_applications` (v2 netleştirme — karar #23/24)

`user_devices` tablosu aynen uygulanır (karar #24: `UNIQUE(user_id, push_token)` ile duplicate koruması;
`DeviceNotRegistered` yanıtında token silinir).

`job_applications` yeni alanlar:

| Alan | Tip | Açıklama |
|---|---|---|
| `match_score` | `Integer NULL` | Başvuru anında hesaplanan uygunluk skoru (0-100) |
| `applied_from` | `VARCHAR(20) DEFAULT 'portal'` | `portal` / `mobile` / `admin` |

### 2.5 Not

- Hiçbir mevcut tablo/kolon silinmez, nullable eklemeler yapılır.
- Migration `downgrade`'i tanımlanır (test ortamında doğrulanır).
- Mevcut 715 belge, 59 personel, 10 gemi, 20 atama, 20 kontrat, 6 kullanıcı **etkilenmez**.

---

## 3. BACKEND API KONTRATI (MOBİL)

> Tüm uçlar `Authorization: Bearer <JWT>` ister. Rol + sahiplik doğrulaması `api/deps.py` üzerinden yapılır. Crew kullanıcısı yalnızca kendi kayıtlarına erişir (IDOR yok).

### 3.1 Auth / Kayıt

| Method | Uç | Rol | Açıklama |
|---|---|---|---|
| POST | `/api/auth/login` | herkes | Mevcut. Mobil aynen kullanır |
| POST | `/api/auth/register` | **YENİ** | Self-registration: ad, soyad, email, telefon, şifre, uyruk, doğum tarihi → `crew_member` + `user(role=crew, is_active=false)` oluşturur; admin onayına düşer; yanıt: `{"status":"pending_review"}` |
| POST | `/api/auth/refresh` | **YENİ** | Refresh token döndürür (opsiyonel M2; ilk sürümde access token 8 saat, mobil yeniden giriş ister) |
| GET | `/api/auth/me` | herkes | Mevcut kullanıcı + rol + `crew_member_id` |

Admin tarafı (mevcut `/api/auth/users` genişletilir):
- PATCH `/api/auth/users/{id}/approve` → kayıt onayla (crew_member + user aktif)
- PATCH `/api/auth/users/{id}` → şifre/rol/aktiflik (mevcut)

### 3.2 Profil & Portal (portal.py genişletilir)

| Method | Uç | Rol | Açıklama |
|---|---|---|---|
| GET | `/api/portal/me` | crew | Mevcut — profil + belgeler |
| GET | `/api/portal/me/full` | **YENİ** | Profil + belgeler + aktif kontrat + aktif gemi + son atama + uygunluk skoru + `job_preferences` |
| PUT | `/api/portal/contact` | crew | Mevcut — telefon/email güncelle |
| PATCH | `/api/portal/job-seeking` | crew | Mevcut — iş arıyorum anahtarı |
| PUT | `/api/portal/preferences` | **YENİ** | `job_preferences`, `available_from`, `expected_salary`, `vessel_types_experience` güncelle |
| POST | `/api/portal/documents` | crew | Mevcut — self-service belge yükleme → `pending_approval` |
| GET | `/api/portal/documents` | crew | **YENİ** — belge listesi (durum hesaplı: valid/expiring/expired/pending) |
| GET | `/api/portal/documents/{id}/file` | crew (sahip) | **YENİ** — kendi belgesini indir |
| GET | `/api/portal/contracts/me` | crew | **YENİ** — aktif kontrat + geri sayım günü + sonraki aday ilanlar |
| GET | `/api/portal/vessel/me` | crew | **YENİ** — aktif atamadan gemi bilgisi |

### 3.3 İlanlar & Başvuru (jobs.py mevcut + küçük ekleme)

| Method | Uç | Rol | Açıklama |
|---|---|---|---|
| GET | `/api/portal/jobs` | crew | Mevcut — yayındaki ilanlar + benim başvuru durumum |
| GET | `/api/jobs/{id}` | staff, crew | Mevcut detay |
| POST | `/api/portal/jobs/{id}/apply` | crew | Mevcut — başvuru; `match_score` hesabı eklenir |
| GET | `/api/portal/applications` | crew | **YENİ** — başvurularım + durum (applied/shortlisted/rejected/...) |
| GET | `/api/portal/jobs/recommended` | crew | **YENİ** — job_seeking ise profiline uygun ilanlar (mevcut uygunluk mantığıyla skorlu) |

### 3.4 Bildirimler (notifications.py mevcut)

| Method | Uç | Rol | Açıklama |
|---|---|---|---|
| GET | `/api/notifications` | herkes | Mevcut |
| PATCH | `/api/notifications/{id}/read` | sahip | Mevcut |
| POST | `/api/devices` | herkes | **YENİ** — push token kaydet (`user_devices`) |
| DELETE | `/api/devices/{token}` | sahip | **YENİ** — çıkışta token sil |

### 3.5 Mesajlaşma (YENİ — `messages.py` router)

| Method | Uç | Rol | Açıklama |
|---|---|---|---|
| GET | `/api/messages/conversations` | herkes | Konuşma listesi (kendi katılımı) |
| POST | `/api/messages/conversations` | admin/hr | Personelle konuşma başlat |
| GET | `/api/messages/conversations/{id}` | katılımcı | Mesajlar (sayfalı) |
| POST | `/api/messages/conversations/{id}` | katılımcı | Mesaj gönder (metin veya dosya) |
| PATCH | `/api/messages/{id}/read` | alıcı | Okundu işaretle |

### 3.6 Admin mobil (mevcut uçlar aynen kullanılır)

Admin mobil, masaüstünün mevcut rol-korumalı uçlarını çağırır:
`/api/dashboard`, `/api/crew?search=`, `/api/jobs`, `/api/documents?match_status=pending_approval`, `/api/crew/eligible`, `/api/audit-logs`.

---

## 4. MOBİL UYGULAMA — PROJE YAPISI (Expo)

```
mobile/
├── app/                        # expo-router (dosya = ekran)
│   ├── _layout.tsx             # root layout + AuthProvider
│   ├── (auth)/login.tsx
│   ├── (auth)/register.tsx
│   ├── (tabs)/
│   │   ├── _layout.tsx         # rol-bazlı tab bar
│   │   ├── index.tsx           # HOME (rol-göre)
│   │   ├── jobs.tsx            # İlanlar + detay + başvuru
│   │   ├── documents.tsx       # Belgeler + yükle
│   │   ├── messages.tsx        # Mesajlar
│   │   └── profile.tsx         # Profil + tercihler
│   └── admin/                  # sadece admin/hr (route guard)
│       ├── index.tsx           # Bugün özeti
│       ├── applications.tsx    # Başvuru havuzu
│       ├── approvals.tsx       # Belge onay kuyruğu
│       └── personnel.tsx       # Personel arama
├── src/
│   ├── api/client.ts           # fetch/axios + JWT interceptor + 401 yönlendirme
│   ├── api/endpoints.ts        # tip güvenli uç çağrıları
│   ├── store/auth.ts           # Zustand: token, user, role
│   ├── store/sync.ts           # offline kuyruk (yazma işlemleri)
│   ├── hooks/useJobs.ts        # TanStack Query
│   ├── hooks/useDocuments.ts
│   ├── hooks/useNotifications.ts
│   ├── components/…            # yeniden kullanılabilir UI
│   └── utils/format.ts         # tarih/süre formatları, durum etiketleri
├── app.json                    # Expo config (scheme, push, ikon)
└── package.json
```

**Kritik kütüphaneler (MVP):**
- `expo`, `expo-router`, `expo-secure-store`, `expo-notifications`, `expo-document-picker`, `expo-image-picker`, `expo-file-system`
- `@tanstack/react-query`, `zustand`
- Native module eklenmez (managed workflow — EAS Build yeterli)

**Token yönetimi:**
```
login → JWT → expo-secure-store (AsyncStorage DEĞİL)
401 yanıtı → token sil → (auth)/login ekranına yönlendir
```

**Rol-bazlı tab bar:**
```
crew + job_seeking=false + aktif kontrat  →  HOME(gemi/kontrat) | BELGELER | İLANLAR | MESAJLAR | PROFİL
crew + job_seeking=true                    →  HOME(iş arama)     | İLANLAR | BAŞVURULARIM | MESAJLAR | PROFİL
admin/hr                                   →  HOME(bugün)        | PERSONEL | BAŞVURULAR | ONAYLAR | AYARLAR
```

---

## 5. PUSH BİLDİRİM — MÜHENDİSLİK AKIŞI

```
expo-notifications (mobil)
   ├── bildirim izni iste → Expo Push Token al
   └── POST /api/devices { platform, push_token }

Backend services/push.py
   ├── send_to_user(user_id, title, body, data)
   ├── user_devices tablosundan token'ları topla
   └── POST https://exp.host/--/api/v2/push/send (Expo Push API)
        └── yanıt: ok / DeviceNotRegistered (token sil)

Tetikleyiciler (mevcut notification servisi + yeni zamanlayıcı)
   ├── belge süresi 30/14/7 gün kala
   ├── kontrat 60/30/14/7 gün kala
   ├── yeni uygun ilan (job_seeking + skor >= eşik)
   ├── belge onayı/reddi
   └── yeni mesaj
```

- MVP'de **Expo Push API** yeterli (Google FCM hesabı bile gerekmez; Expo üzerinden gider). İleride FCM'ye geçilebilir.
- Uygulama açıkken bildirim geldiğinde yerel `notifications` listesi de tazelenir (tek veri kaynağı: Notification tablosu).

---

## 6. OFFLINE SENKRON (M1 KAPSAMINDA SINIRLI)

- **M1:** Okuma önbelleği (TanStack Query `staleTime` + AsyncStorage persist). Yazma işlemleri çevrimiçi zorunlu; çevrimdışıysa "İnternet bağlantısı gerekli" uyarısı.
- **M2+:** `store/sync.ts` — başvuru, mesaj, belge yükleme gibi işlemler yerel kuyruğa alınır; `expo-network` ile bağlantı geldiğinde sırayla gönderilir, başarılı olanlar kuyruktan düşer.

---

## 7. DOSYA YÜKLEME / İNDİRME

- Yükleme: `expo-document-picker` (PDF) + `expo-image-picker` (fotoğraf → pasaport/medikal fotoğrafları). Fotoğraflar backend'e `multipart` ile gider; backend mevcut `store_file` + `extract_text` + `extract_metadata` pipeline'ını kullanır (belge tipi algılama hazır).
- **M1 kısıtı:** fotoğraftan OCR yok — `document_type` kullanıcı seçer, `match_status=pending_approval`, admin onaylar. (OCR, ileride mevcut document_processing'e PyMuPDF/Tesseract ile eklenebilir — bu ayrı karar.)
- İndirme: `expo-file-system` ile belgeyi cihaza indir, `expo-sharing` ile paylaş/aç.

---

## 8. GÜVENLİK UYGULAMASI (MÜHENDİSLİK)

1. **IDOR:** Tüm crew uçları `crew = db.get(CrewMember, current_user.crew_member_id)` kullanır; `crew_id` path/query parametresi **kabul edilmez**.
2. **Kayıt:** `POST /auth/register` → 409 duplicate email kontrolü, `is_active=false`, admin onayı; onaysız kullanıcı `login`'de 403 alır.
3. **Mesaj erişimi:** conversation katılımcı kontrolü her GET/POST'ta yapılır.
4. **CORS:** Mobil native uygulama CORS'a tabi değildir (tarayıcı değil), ama web fallback için mevcut CORS korunur.
5. **Rate limit:** login'e ek olarak register (5/saat/IP) ve mesaj (30/dk/kullanıcı) sınırları.
6. **Audit:** register, approve, apply, document upload, message, override işlemleri `log_event` ile `audit_logs`'a yazılır.
7. **Veri minimizasyonu:** mobil yanıtlarda pasaport numarası gibi hassas alanlar yalnızca sahibine ve admin'e döner; viewer'a maskelenir.

---

## 9. TEST STRATEJİSİ

### Backend (pytest — mevcut 199 + yeni)
- `test_mobile_register.py` — kayıt, duplicate email, onaysız giriş 403, admin onayı sonrası giriş
- `test_mobile_portal.py` — `/me/full`, `/preferences`, `/contracts/me`, `/vessel/me`
- `test_mobile_documents.py` — kendi belgesini indirme 200, başkasınınki 403/404
- `test_mobile_jobs.py` — recommend, apply + match_score, duplicate apply 409
- `test_mobile_messages.py` — konuşma başlatma, katılımcı dışı erişim 403, okundu
- `test_mobile_devices.py` — push token kayıt/sil, auth'suz 401
- `test_mobile_rbac.py` — viewer/admin uçlarına crew erişimi 403, admin onay uçlarına viewer 403

### Mobil (Jest + React Native Testing Library)
- Token saklama/401 yönlendirme
- Rol-bazlı tab bar render
- Belge durumu etiketleri (valid/expiring/expired) — backend'den gelen veriyle
- Offline kuyruk davranışı (M2)

### E2E / Kabul
- Gerçek cihaz/emülatör: kayıt → onay → login → belge yükle → ilan gör → başvur → mesaj → push bildirim
- Mevcut masaüstü regression: **pytest 199 + frontend build PASS her faz sonunda**

---

## 10. DEPLOYMENT (MOBİL)

```
1. EAS Build (expo.dev) → Android AAB üret
2. Google Play Console → Internal Testing (kapalı test) → Production
3. iOS (M2+): Apple Developer hesabı → TestFlight → App Store
4. Backend: mevcut domain + Named Tunnel/SSL üzerinden https://api.freebuff.com (veya mevcut tünel)
   → mobil app.json'da API_BASE_URL env ile
5. Secret yönetimi: EAS env (app.config.ts'de process.env.EXPO_PUBLIC_API_URL), backend .env
```

---

## 11. UYGULAMA SIRASI (KOD YAZILACAĞI ZAMAN)

```
ADIM 1   Migration 0010 (crew_members ek alanlar, user_devices, conversations, messages)
ADIM 2   auth.py: register + approve; deps: crew sahiplik yardımcıları
ADIM 3   portal.py: /me/full, /preferences, /contracts/me, /vessel/me, /documents, /documents/{id}/file
ADIM 4   jobs.py: apply match_score, /portal/applications, /portal/jobs/recommended
ADIM 5   messages.py router + models
ADIM 6   devices.py + services/push.py + notification servisine push çağrıları
ADIM 7   Backend testleri (bölüm 9) → pytest hepsi yeşil
ADIM 8   mobile/ Expo projesi iskeleti (auth, tabs, api client, secure store)
ADIM 9   Home/Profil/Belgeler/İlanlar/Başvuru ekranları (M1)
ADIM 10  Push entegrasyonu + bildirim ekranı
ADIM 11  EAS Build → Android test sürümü → canlı doğrulama
ADIM 12  DEVELOPMENT_LOG + doküman güncelleme
```

---

## 12. KAPSAM DIŞI (ŞU AN DEĞİL)

- OCR ile fotoğraflı belge okuma (ayrı karar gerekir — Tesseract/cloud OCR)
- WebSocket gerçek zamanlı mesajlaşma (MVP REST; v2 WebSocket)
- AI asistan / doğal dil sorguları
- QR Crew ID, joining checklist, seyir bilgileri (M4)
- FCM direkt entegrasyon (MVP Expo Push yeterli)
