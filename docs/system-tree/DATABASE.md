# DATABASE AĞACI

PostgreSQL + Alembic. **Head: `20260818_0010`** (28 Ağustos 2026).

## Migration Geçmişi

| Migration | İçerik |
|---|---|
| 0001–0006 | çekirdek: users, crew_members, documents, ships, assignments, contracts, notifications, ship_positions, users.crew_member_id, crew.availability, documents.archived_at |
| 0007 | app_settings (SMTP + WhatsApp alanları, masked) |
| 0008 | job_postings, job_applications |
| 0009 | job_templates, job_publications, whatsapp_messages, job_images, job_posting yeni alanlar, crew_members.job_seeking |
| 0010 | M1 Mobile: crew_members iş tercihleri, user_devices, conversations, messages, job_applications.match_score/applied_from |

## Tablolar ve İlişkiler

```text
users
├── role (admin/hr/viewer/crew), is_active, password_hash (asla plaintext)
└── crew_member_id → crew_members.id  (crew hesabı zorunlu bağlı)

crew_members
├── documents.crew_member_id (1→N)        [belgeler]
├── assignments.crew_member_id (1→N)      [gemi atamaları]
├── contracts.crew_member_id (1→N)
├── notifications.user_id (1→N)
├── whatsapp_messages.crew_member_id (1→N)
├── job_applications.crew_member_id (1→N)
└── job_seeking (bool) — "İş Arıyorum" anahtarı

ships
├── ship_positions.ship_id (1→N)          [kadro]
├── assignments.ship_id (1→N)
└── contracts.ship_id (1→N)

documents
├── document_matches.document_id (1→N)    [eşleştirme geçmişi]
├── match_status (pending/processing/matched/review_required/unmatched/conflict/duplicate/failed/pending_approval)
└── archived_at — versiyonlama (onaylanan yeni belge eskisini arşivler)

job_postings
├── job_applications.job_posting_id (1→N)
├── job_publications.job_posting_id (1→N)  [kanal başına: crew_portal/whatsapp/instagram/facebook]
├── whatsapp_messages.job_posting_id (1→N)
└── job_images.job_posting_id (1→1)

app_settings (key/value)
├── smtp_host/port/user/password/from
├── whatsapp_admin_number / api_token / phone_id / business_account_id
├── whatsapp_api_base_url / webhook_verify_token / sender_number
└── gizli anahtarlar GET'te maskelenir (cr****fy)
```

## İndeksler

`passport_number`, `seaman_book_number`, `email`, `first_name/last_name`,
`document_type`, `match_status`, `expiry_date`, `crew_member_id` (belgeler).

## Baseline (Phase 8 öncesi doğrulanmış)

59 personel · 758 belge · 10 gemi · 20 atama · 20 kontrat · 6 kullanıcı ·
100 ship position · ~791 storage dosyası
