# BACKEND AĞACI

## Route → Service → Model

```text
/api/auth
├── POST /login                     → auth.py            → User (JWT)
├── POST /users                     → auth.py            → User (admin/hr)
├── PATCH /users/{id}               → auth.py            → User
├── DELETE /users/{id}              → auth.py            → User (admin)
└── GET  /me                        → auth.py            → User

/api/crew
├── GET  /                          → crew.py            → CrewMember (+filtre: availability, position, search)
├── GET  /eligible                  → eligibility.py     → CrewMember + skor
├── GET  /export, /import/*         → crew.py            → CSV
├── POST /, PATCH /{id}, DELETE /{id} → crew.py          → CrewMember
└── GET  /{id}                      → crew.py            → CrewMember (+maskeleme viewer/crew)

/api/documents
├── POST /upload, /bulk-upload      → documents.py + document_service.py → Document
├── POST /match                     → documents.py + match_engine.py     → DocumentMatch
├── GET  /review                    → documents.py       → Document (review kuyruğu)
├── POST /{id}/approve, /reject     → documents.py       → Document (onay kuyruğu, eski arşiv)
├── POST /{id}/manual-match         → documents.py       → Document
├── GET  /{id}/download             → documents.py       → FileResponse
├── DELETE /{id}                    → documents.py       → Document + storage
└── GET  /                          → documents.py       → Document (pagination + filtre)

/api/ships
├── GET/POST /                      → ships.py           → Ship
├── GET/PATCH/DELETE /{id}          → ships.py           → Ship
├── GET  /{id}/staffing             → ships.py           → ShipPosition + dolu/açık
├── POST /{id}/positions            → ships.py           → ShipPosition (upsert)
└── DELETE /positions/{id}          → ships.py           → ShipPosition

/api/assignments                    → assignments.py     → Assignment
/api/contracts                      → contracts.py       → Contract (+7/30/90 gün filtre)
/api/expiration                     → expiration.py      → Document (expired/urgent/approaching)
/api/dashboard/summary              → dashboard.py       → özet + görevler (tıklanabilir kart verisi)
/api/audit-logs                     → audit_logs.py      → AuditLog

/api/jobs
├── GET/POST /                      → jobs.py            → JobPosting
├── GET/PATCH/DELETE /{id}          → jobs.py            → JobPosting
├── POST /{id}/apply                → jobs.py            → JobApplication
├── GET /applications/all           → jobs.py            → JobApplication (havuz)
├── PATCH /applications/{id}        → jobs.py            → JobApplication (durum)
├── POST /{id}/publish              → jobs.py + whatsapp.py → JobPublication + WhatsAppMessage
├── GET /{id}/publications          → jobs.py            → JobPublication
├── POST /{id}/publications/{ch}/retry → jobs.py         → JobPublication
├── GET /{id}/whatsapp-messages     → jobs.py            → WhatsAppMessage
├── POST /{id}/image, GET /{id}/image → jobs.py          → JobImage
└── /api/job-templates (CRUD)       → jobs.py            → JobTemplate

/api/webhooks/whatsapp
├── GET  (hub.* verify)             → jobs.py            → challenge döner (Meta doğrulaması)
└── POST (mesaj alımı)              → jobs.py            → log + kabul (belge alma akışı sonraki faz)

/api/notifications
├── GET /, POST /generate           → notifications.py   → Notification
├── POST /{id}/read                 → notifications.py   → Notification
└── POST /send-bulk, /send-one      → notifications.py   → e-posta kuyruğu (SMTP yoksa pending)

/api/portal  (crew rolü — izole)
├── GET /me                         → portal.py          → kendi profil + belgeler
├── PUT /contact                    → portal.py          → telefon/email güncelle
├── PATCH /job-seeking              → portal.py          → job_seeking anahtarı
├── GET /jobs, POST /jobs/{id}/apply → portal.py         → JobPosting/JobApplication
└── POST /documents                 → portal.py          → kendi belge yükleme (pending_approval)

/api/settings
├── GET/PUT /                       → settings.py        → AppSetting (admin; masked)
├── GET /contact                    → settings.py        → whatsapp_admin_number (herkese okunur)
└── GET /notif-public               → settings.py        → SMTP/WhatsApp yapılandırılmış mı (boolean)
```

## WhatsApp Provider (app/services/whatsapp.py)

```text
normalize_phone()      → +90 532 327 61 21 → 905323276121
WhatsAppProvider
├── is_configured()    → token + phone_id var mı?
├── send_text()        → Graph API v21.0 POST (httpx)
├── process_queue()    → pending mesajları dener → sent/failed/skipped/remaining
└── queue_job_broadcast() → ilan→personel kuyruğu (duplicate korumalı)
```

Kritik davranış: **token yoksa sahte başarı ÜRETİLMEZ** — mesaj `pending` kalır,
publication `queued` + açıklayıcı hata yazılır.

## AI Module (backend/ai/ + routes/ai.py)

```text
/api/ai
├── GET  /health                    → ai.py             → llm_available durumu
├── POST /analyze                    → ai.py + llm_client → belge analizi (Groq LLM)
├── POST /analyze/upload             → ai.py + llm_client → PDF upload + analiz
├── POST /match                      → ai.py + crew_matcher → personel-belge eşleştirme
├── POST /anomalies                  → ai.py + anomaly_detector → anomali tespiti
├── POST /recommend                  → ai.py + recommendation → öneri motoru
└── POST /summarize                  → ai.py + summarizer → belge özetleme
```

### AI Services (backend/ai/)

```text
llm_client.py        → Groq API client (httpx, GROQ_API_KEY required)
document_analyzer.py → PDF → structured analysis (belge tipi, alan çıkarma)
crew_matcher.py      → Belge-personel eşleştirme (scoring)
anomaly_detector.py  → Belge tutarsızlık tespiti
recommendation.py    → Öneri motoru
summarizer.py        → Belge özetleme
```

Gereksinimler: `GROQ_API_KEY` env variable (docker-compose.yml'de tanımlı).
Model: `llama-3.3-70b-versatile` (Groq).

Kritik düzeltme (2026-08-28): `ai/` repo kökünden `backend/ai/`'ye taşındı,
sys.path hack kaldırıldı. Docker build context artık doğru kopyalıyor.
