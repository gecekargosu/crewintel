# FRONTEND AĞACI

Tek sayfa uygulama: `frontend/src/App.jsx` (Vite + React, state `useState`).
API URL: `const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"`.

## Ekran → State → API

```text
Login                        auth (token)               POST /api/auth/login
Dashboard                    dashboard                   GET /api/dashboard/summary
Personel listesi             crew + crewFilters          GET /api/crew/?search=&position=&availability=
Personel detayı              selectedCrew                GET /api/crew/{id} + /api/crew/{id}/eligible
Belgeler                     documents + docFilters      GET /api/documents/?type=&status=&expiry=
Belge yükleme                uploadState                 POST /api/documents/bulk-upload
Review kuyruğu               reviewQueue                 GET /api/documents/review
Gemiler                      ships                       GET /api/ships + /{id}/staffing
Atamalar                     assignments                 GET/POST/PATCH/DELETE /api/assignments
Kontratlar                   contracts + contractFilter  GET /api/contracts/?ending_within=
Uygunluk                     eligibleResults             GET /api/crew/eligible?position=
Kadro                        ships + staffing            GET /api/ships/{id}/staffing
İş İlanları & Yayın          jobs + publishState         GET/POST /api/jobs + /{id}/publish
İletişim                     contactList                 GET /api/settings/contact + /api/crew/
Crew Portal                  portalMe + portalJobs       GET /api/portal/me + /jobs
Ayarlar                      appSettings + notifSettings GET/PUT /api/settings + /api/auth/users
```

## Rol Bazlı UI Davranışı

| Rol | Yazma | Görüntüleme | Portal |
|---|---|---|---|
| admin | tam | tam (maskesiz) | hayır |
| hr | tam | tam (maskesiz) | hayır |
| viewer | yok (butonlar gizli + API 403) | tam (maskeleme) | hayır |
| crew | kendi belge yükleme + iletişim | kendi verisi | evet |

Maskeleme: viewer/crew personel detayında `U6****34` / `TR**********46`.

## Kritik UX Akışları (Phase 7+)

- Gemi detayı / atama satırları → tıklama → personel detayı
- Dashboard Operasyon Merkezi kartları → "Git →" → ilgili sayfa + otomatik filtre
  (örn. "Müsait Personel" → Personel + `availability=available`)
- Filtreler: seçim + **FİLTRELE** butonu (anında uygulama), **TEMİZLE** (sıfırla)
- WhatsApp: İletişim sayfası + wa.me click-to-chat linkleri
- İş İlanları: form → Yayınla paneli (kanal seçimi) → yayın geçmişi + retry
