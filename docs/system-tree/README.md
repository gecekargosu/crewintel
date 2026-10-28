# CREWINTEL — SİSTEM MİMARİSİ AĞACI

Bu dokümantasyon, CREWINTEL'in **gerçek mevcut kodundan** çıkarılmıştır.
Var olmayan özellikler "varmış gibi" yazılmamıştır.

> Güncelleme tarihi: 2026-08-18 (Phase 8 — WhatsApp Business API altyapısı + İş İlanları & Yayın)

## Ana Ağaç

```text
CREWINTEL
│
├── FRONTEND  (frontend/src/App.jsx — tek sayfa uygulama, Vite + React)
│   ├── Giriş / Auth
│   │   ├── login ekranı (email + şifre)
│   │   ├── JWT access token (localStorage)
│   │   └── logout / token expiry → login'e dönüş
│   ├── Dashboard
│   │   ├── özet kartlar (personel, gemi, aktif personel)
│   │   ├── belge geçerlilik durumu (expired/urgent/approaching/valid/no_date)
│   │   ├── Operasyon Merkezi (bugünkü işler — tıklanabilir kartlar)
│   │   └── sistem durumu (gemi animasyonu — aktif/kapalı)
│   ├── Personel
│   │   ├── liste (arama, filtre — müsaitlik dahil, FİLTRELE/TEMİZLE)
│   │   ├── detay (kimlik, belgeler, atamalar, kontratlar, uygunluk rozeti)
│   │   ├── CRUD modal'ları
│   │   ├── seçim kutuları + Toplu E-posta
│   │   └── viewer/crew için hassas alan maskeleme (pasaport, seaman book)
│   ├── Belgeler
│   │   ├── liste + filtre (tip, durum, süre — FİLTRELE/TEMİZLE)
│   │   ├── yükleme (PDF/TXT, tek + toplu)
│   │   ├── Match Engine sonuçları (matched/review/unmatched/conflict)
│   │   ├── review kuyruğu + manuel eşleştirme
│   │   └── onay kuyruğu (pending_approval → onayla/reddet)
│   ├── Gemiler
│   │   ├── liste + detay
│   │   ├── kadro pozisyonları (ShipPosition — gereken/dolu/açık)
│   │   └── gemi personeli listesi (tıklanabilir → personel detayı)
│   ├── Atamalar (gemi personeli)
│   │   ├── personel ↔ gemi atama CRUD
│   │   └── satırlar tıklanabilir → personel detayı
│   ├── Kontratlar
│   │   ├── liste + detay + CRUD
│   │   └── bitiş tarihi filtreleri (7/30/90 gün — dashboard'dan gelir)
│   ├── Uygunluk
│   │   ├── pozisyon bazlı aday listesi (skor + belge durumu + kırılım)
│   │   └── "Bu gemiye kimi gönderebilirim?" arama
│   ├── Kadro
│   │   └── gemi pozisyonları + açık pozisyon görünümü
│   ├── İş İlanları & Yayın
│   │   ├── ilan formu (temel bilgiler + gereksinimler + durum)
│   │   ├── Yayınla paneli (Crew Portal / WhatsApp / Instagram / Facebook)
│   │   ├── WhatsApp personel seçimi + wa.me click-to-chat
│   │   ├── yayın geçmişi + retry
│   │   └── Başvuru Havuzu (İncele/Onayla/Reddet)
│   ├── İletişim
│   │   ├── telefonu olan personel listesi
│   │   └── kişi başı WhatsApp'tan Mesaj (wa.me)
│   ├── Crew Portal (personel rolü)
│   │   ├── profil + kendi belgeleri
│   │   ├── İş Arıyorum anahtarı
│   │   ├── iş ilanları listesi + Başvur
│   │   └── iletişim güncelleme (telefon/email)
│   ├── Bildirimler
│   │   └── zil ikonu + okunmamış sayaç + okundu işaretleme
│   └── Ayarlar
│       ├── Şirket görünümü (ad + logo)
│       ├── Bildirim Ayarları (SMTP + WhatsApp Business API alanları)
│       └── Kullanıcı Yönetimi (rol, bağlı personel, aktif/pasif)
│
├── BACKEND  (backend/app — FastAPI)
│   ├── main.py — uygulama + router kayıtları + CORS
│   ├── api/routes/
│   │   ├── auth.py        — login, JWT, kullanıcı CRUD, rol kontrolü
│   │   ├── crew.py        — personel CRUD + filtre + maskeleme + eligibility
│   │   ├── documents.py   — belge CRUD + upload + match + onay/red + review
│   │   ├── ships.py       — gemi CRUD + kadro pozisyonları
│   │   ├── assignments.py — personel-gemi atama CRUD
│   │   ├── contracts.py   — kontrat CRUD + bitiş filtreleri
│   │   ├── dashboard.py   — özet + Operasyon Merkezi görevleri
│   │   ├── expiration.py  — belge geçerlilik hesapları
│   │   ├── jobs.py        — iş ilanı CRUD + yayın + şablon + WhatsApp webhook
│   │   ├── notifications.py — bildirim üretimi + e-posta kuyruğu
│   │   ├── portal.py      — crew portal (profil, ilan, başvuru, belge yükleme)
│   │   ├── settings.py    — uygulama ayarları (SMTP/WhatsApp, masked)
│   │   └── audit_logs.py  — denetim kayıtları
│   ├── services/
│   │   ├── match_engine.py      — belge→personel eşleştirme (skor + aday)
│   │   ├── document_processing.py — PDF/TXT text extraction + sınıflandırma
│   │   ├── document_service.py  — belge kayıt/storage işlemleri
│   │   ├── eligibility.py       — uygunluk motoru (belge + deneyim + müsaitlik)
│   │   ├── expiration_service.py — expired/urgent/approaching sınırları
│   │   ├── notifications.py     — SMTP gönderim + ayar yükleme
│   │   ├── whatsapp.py          — WhatsApp Business API provider + kuyruk
│   │   └── audit.py             — log_event yardımcısı
│   ├── models/  (SQLAlchemy)
│   │   ├── user.py, crew_member.py, document.py, ship.py, ship_position.py
│   │   ├── assignment.py, contract.py, notification.py, setting.py
│   │   ├── job.py (JobPosting, JobApplication, JobTemplate, JobPublication,
│   │   │           WhatsAppMessage, JobImage)
│   │   └── audit_log.py, document_match.py
│   └── core/ — security (hash, JWT), deps (rol bağımlılıkları), config
│
├── DATABASE  (PostgreSQL + Alembic — backend/alembic/versions/)
│   ├── 0001 → 0009 migration'ları (head: 20260818_0009)
│   ├── tablolar: users, crew_members, documents, ships, ship_positions,
│   │   assignments, contracts, notifications, app_settings, audit_logs,
│   │   document_matches, job_postings, job_applications, job_templates,
│   │   job_publications, whatsapp_messages, job_images
│   └── indeksler: passport_number, seaman_book_number, email, name,
│       document_type, match_status, expiry_date, crew_member_id
│
├── STORAGE  (STORAGE_PATH — Docker volume)
│   ├── uploads/ — orijinal belge dosyaları (UUID filename)
│   └── job_images/ — üretilen ilan görselleri
│
├── AUTH / SECURITY
│   ├── roller: admin / hr / viewer / crew
│   ├── JWT (access token, expiration, SECRET_KEY .env'den)
│   ├── password hash (bcrypt benzeri — rounds)
│   ├── crew izolasyonu (portal sadece kendi crew_member_id)
│   ├── viewer/crew maskeleme + yazma yasağı (API seviyesinde)
│   ├── rate limit (login denemeleri)
│   └── WhatsApp token DB'de masked, asla frontend'e/loglara yazılmaz
│
├── EXTERNAL INTEGRATIONS
│   ├── WhatsApp Business API (Meta Graph v21.0) — altyapı hazır, token bekliyor
│   │   ├── send_text (graph.facebook.com/v21.0/{phone_id}/messages)
│   │   ├── webhook /api/webhooks/whatsapp (verify + receive)
│   │   └── kuyruk (whatsapp_messages) + retry + duplicate koruması
│   ├── SMTP (e-posta kuyruğu — SMTP ayarı girilince gönderim başlar)
│   ├── Instagram / Facebook — CONFIGURATION REQUIRED (token yoksa skipped,
│   │   sahte başarı üretilmez)
│   └── Cloudflare Quick Tunnel (trycloudflare) — mevcut public erişim
│
├── MOBILE / CREW PORTAL
│   ├── PWA uyumlu web portalı (responsive — 375/390/430/768px test edildi)
│   └── crew: profil, belgeler, İş Arıyorum, ilanlar, başvuru
│
└── INFRASTRUCTURE
    ├── docker-compose.yml — backend / frontend / postgres
    ├── healthcheck'ler (backend /health + /health/database, postgres pg_isready)
    ├── PostgreSQL host'a açık DEĞİL (container içi)
    ├── frontend: Vite dev server (public allowedHosts trycloudflare için açık)
    └── tests — backend/.venv pytest: 198 test (root tests/ + backend/tests/)
```

## Detaylı Alt Ağaçlar

- [BACKEND.md](BACKEND.md) — route → service → model ilişkileri
- [FRONTEND.md](FRONTEND.md) — ekran → state → API çağrısı haritası
- [DATABASE.md](DATABASE.md) — tablo/ilişki/indeks özeti
- [INTEGRATIONS.md](INTEGRATIONS.md) — WhatsApp/SMTP/sosyal medya durumu
