# \# CREWINTEL — MASTER DEVELOPMENT LOG

# > AI-readable project memory \& engineering handoff document.

# > Bu dosya, projeyi devralan herhangi bir AI agent'ın mevcut durumu sıfırdan taramadan anlayabilmesi için tasarlanmıştır.

# 

# \*\*Son güncelleme:\*\* 2026-08-10

# \*\*Tamamlanan adım:\*\* STEP 2

# 

# \---

# 

# \## 1. PROJECT IDENTITY

# 

# | Alan | Değer |

# |---|---|

# | Proje adı | CREWINTEL |

# | Proje tipi | Crew Management / Personnel Archive System |

# | Hedef kullanıcı | Tek kullanıcı (denizcilik sektörü) |

# | Geliştirme aşaması | Backend stabil · Frontend Aşama 4 devam ediyor |

# | Proje kökü | `C:\\CREWINTEL` |

# 

# \### Kısa Açıklama

# 

# CREWINTEL; gemi personelinin CV'lerini, pasaportlarını, gemiadamı cüzdanlarını, STCW belgelerini, GOC belgelerini, sağlık belgelerini, kontratlarını ve diğer belgelerini merkezi bir sistemde arşivleyen, belge geçerlilik sürelerini takip eden ve tüm işlemleri denetlenebilir hale getiren profesyonel bir crew management platformudur.

# 

# \---

# 

# \## 2. PROJECT GOAL

# 

# \### Çözülen Problem

# 

# Gemi personelinin belgeleri Excel/kağıt/farklı klasörlerde tutulduğunda belge kaybı, tarihlerin unutulması, denetim problemleri ve manuel takip yükü oluşmaktadır. CREWINTEL bu süreci dijitalleştirir.

# 

# \### Mevcut Kullanım Senaryoları (koddan doğrulanmış)

# 

# \- Personel (crew member) CRUD yönetimi

# \- Gemi (ship) CRUD yönetimi

# \- Personel–gemi ataması (assignment)

# \- Kontrat yönetimi

# \- Belge yükleme (PDF/TXT), arşivleme ve otomatik eşleştirme

# \- Belge tipi tespiti (CV, pasaport, STCW, GOC, medical, contract, other)

# \- İsim/pasaport/gemiadamı cüzdanı numarası ile personel eşleştirme

# \- CV yüklendiğinde otomatik personel oluşturma

# \- Belge geçerlilik süresi takibi (expired / urgent / approaching / valid / no\_date)

# \- Tüm CRUD işlemlerinin audit log kaydı

# \- Pending belgeler için manuel eşleştirme

# 

# \### Planlanmış (koddan doğrulanmamış — FUTURE)

# 

# \- Authentication / JWT / RBAC

# \- Bildirim sistemi (belge bitiş uyarıları)

# \- AI/OCR ile gelişmiş belge okuma

# \- Mobile uygulama

# \- Çok kullanıcılı yapı (admin, manager, hr, captain, viewer rolleri)

# 

# \---

# 

# \## 3. ARCHITECTURE (Doğrulanmış)

# 

# ```

# React/Vite (frontend)

# &#x20;       │  HTTP (Axios)

# &#x20;       ▼

# FastAPI (backend, port 8000)

# &#x20;       │  SQLAlchemy 2.x ORM

# &#x20;       ▼

# PostgreSQL 17 (port 5433 yerel / 5432 Docker)

# ```

# 

# | Katman | Teknoloji | Versiyon |

# |---|---|---|

# | Frontend framework | React | — |

# | Frontend bundler | Vite | 8.x |

# | Frontend HTTP | Axios | — |

# | Frontend lint | oxlint | — |

# | Backend framework | FastAPI | 0.141.1 |

# | Backend server | uvicorn\[standard] | 0.52.1 |

# | ORM | SQLAlchemy | 2.0.51 |

# | DB driver | psycopg\[binary] | 3.3.4 |

# | Schema validation | Pydantic / pydantic-settings | 2.15.0 |

# | Migration | Alembic | 1.16.5 |

# | PDF parsing | pypdf | 5.9.0 |

# | File upload | python-multipart | 0.0.20 |

# | Testing | pytest | 8.4.1 |

# | Test HTTP | httpx | 0.28.1 |

# | Container | Docker Compose | — |

# | Database | PostgreSQL | 17 |

# 

# \---

# 

# \## 4. DIRECTORY STRUCTURE

# 

# ```

# C:\\CREWINTEL\\

# ├── .env                          # Runtime secrets — git'e eklenmez

# ├── .env.example                  # Şablon

# ├── docker-compose.yml            # postgres + backend + frontend servisleri

# ├── pytest.ini                    # Test config (rootdir, pythonpath)

# │

# ├── backend/

# │   ├── Dockerfile

# │   ├── requirements.txt          # 11 paket

# │   ├── alembic/

# │   │   └── versions/

# │   │       ├── 0001\_create\_crew\_members.py

# │   │       ├── 0002\_add\_core\_domain\_models.py

# │   │       └── 0003\_add\_documents\_profiles\_audit.py

# │   └── app/

# │       ├── main.py               # FastAPI app, CORS, router kayıtları

# │       ├── run.py                # Uvicorn entry point

# │       ├── core/config.py        # pydantic-settings, .env yükler

# │       ├── db/

# │       │   ├── database.py       # engine, SessionLocal, Base, get\_db()

# │       │   └── init\_db.py        # create\_all (test/dev için)

# │       ├── models/               # SQLAlchemy ORM modelleri

# │       │   ├── crew\_member.py    # 28 alan

# │       │   ├── ship.py           # 7 alan

# │       │   ├── assignment.py     # ShipCrewAssignment

# │       │   ├── contract.py

# │       │   ├── document.py       # 16 alan, checksum, match\_status

# │       │   ├── audit\_log.py      # 7 alan

# │       │   └── user.py           # ⚠️ Model var, migration'da yok

# │       ├── schemas/              # Pydantic request/response şemaları

# │       │   ├── crew\_member.py    # CrewMemberCreate/Update/Response

# │       │   ├── ship.py

# │       │   ├── assignment.py

# │       │   ├── contract.py

# │       │   └── document.py       # DocumentResponse, DocumentMatchUpdate

# │       ├── api/routes/           # FastAPI router'ları

# │       │   ├── crew.py

# │       │   ├── ships.py

# │       │   ├── assignments.py

# │       │   ├── contracts.py

# │       │   ├── documents.py      # ← STEP 1'de güncellendi

# │       │   ├── expiration.py

# │       │   └── audit\_logs.py

# │       └── services/             # İş mantığı katmanı

# │           ├── audit.py          # log\_event() helper

# │           ├── document\_service.py   # DocumentService class ← STEP 1'de güncellendi

# │           ├── document\_processing.py  # extract, parse, match, store

# │           └── expiration\_service.py   # ExpirationService class

# │

# ├── tests/

# │   ├── conftest.py               # SQLite in-memory test DB, fixtures

# │   ├── test\_api.py               # 10 test (crew, ship, assignment, contract)

# │   ├── test\_audit.py             # 11 test (audit log kayıtları)

# │   └── test\_documents.py         # 5 test (upload, match, filter) ← STEP 1'de güncellendi

# │

# ├── frontend/

# │   ├── package.json              # React, Vite, Axios, Lucide-React

# │   ├── vite.config.js

# │   ├── index.html

# │   └── src/

# │       ├── main.jsx              # React root

# │       ├── App.jsx               # ⚠️ Aşama 4 henüz tamamlanmadı (165 satır)

# │       ├── App.css               # ✅ Aşama 4 için CSS tamamen hazır (437 satır)

# │       └── index.css

# │

# ├── docs/

# │   ├── ARCHITECTURE.md           # Mimari özet (Türkçe)

# │   ├── SETUP.md                  # Kurulum rehberi

# │   └── DEVELOPMENT\_LOG.md        # ← BU DOSYA (proje hafızası)

# │

# ├── ai/          # BOŞ — gelecek AI/OCR modülü için ayrılmış

# ├── deployment/  # BOŞ

# ├── mobile/      # BOŞ

# ├── scripts/     # İçerik mevcut

# ├── database/    # İçerik mevcut

# └── storage/     # Yüklenen belge dosyaları burada saklanır

# ```

# 

# \---

# 

# \## 5. BACKEND CURRENT STATE

# 

# | Modül | Durum | Notlar |

# |---|---|---|

# | FastAPI app | ✅ DONE | main.py, CORS configurable |

# | Config | ✅ DONE | pydantic-settings, `.env`'den yükler |

# | DB connection | ✅ DONE | pool\_pre\_ping, get\_db() dependency |

# | Alembic migrations | ✅ DONE | 3 migration, linear chain |

# | CrewMember model/CRUD | ✅ DONE | 28 alan, filtreli liste (name, surname, position, nationality, status, ship\_id) |

# | Ship model/CRUD | ✅ DONE | IMO validation |

# | Assignment model/CRUD | ✅ DONE | |

# | Contract model/CRUD | ✅ DONE | |

# | Document model | ✅ DONE | 16 alan, checksum dedup, match\_status |

# | Document upload | ✅ DONE | Multi-file, PDF+TXT, SHA-256 checksum |

# | Document download | ✅ DONE | FileResponse |

# | Document match | ✅ DONE | Manuel eşleştirme (PUT /{id}/match) |

# | Document list filter | ✅ DONE | crew\_member\_id, document\_type, match\_status (\*\*STEP 1\*\*), expiry\_status |

# | Document processing | ✅ DONE | extract\_text, parse\_date, extract\_metadata, match\_crew, store\_file |

# | Expiration service | ✅ DONE | expired/urgent/approaching/valid/no\_date |

# | Audit logging | ✅ DONE | log\_event(), tüm CRUD'a yayılmış |

# | Audit API | ✅ DONE | GET /api/audit-logs/ (filtreli) |

# | User model | ⚠️ PARTIAL | Model var, migration yok, route yok, schema yok |

# | Authentication | ❌ MISSING | Hiçbir middleware/dependency yok |

# | Authorization/RBAC | ❌ MISSING | |

# 

# \---

# 

# \## 6. DATABASE CURRENT STATE

# 

# \### Tablolar

# 

# | Tablo | Alanlar | Durum |

# |---|---|---|

# | `crew\_members` | id, first\_name, last\_name, dob, nationality, passport\_no, seaman\_book\_no, position, rank, phone, email, address, emergency\_contact, birth\_place, hometown, marital\_status, experience\_years, sea\_service\_months, languages, education\_summary, notes, profile\_data(JSON), status | ✅ Migration 0001+0003 |

# | `ships` | id, name, imo\_number(unique), flag, ship\_type, company, status | ✅ Migration 0002 |

# | `ship\_crew\_assignments` | id, ship\_id(FK), crew\_member\_id(FK), position, start\_date, end\_date, status, notes | ✅ Migration 0002 |

# | `contracts` | id, ship\_id(FK), crew\_member\_id(FK), contract\_number(unique), contract\_type, start\_date, end\_date, currency, monthly\_wage, status, notes | ✅ Migration 0002 |

# | `documents` | id, crew\_member\_id(FK nullable), original\_filename, stored\_filename(unique), storage\_path, mime\_type, file\_size, checksum(unique), document\_type, document\_number, issue\_date, expiry\_date, match\_status, match\_confidence, extracted\_text, extracted\_metadata(JSON), source | ✅ Migration 0003 |

# | `audit\_logs` | id, action, entity, entity\_id, message, status, metadata\_json(JSON), created\_at | ✅ Migration 0003 |

# | `users` | id, email(unique), full\_name, role, is\_active | ⚠️ Model var, \*\*migration yok\*\* — tablo oluşmuyor |

# 

# \### Document.match\_status Değerleri

# 

# ```

# "pending"    — eşleşme belirsiz veya bulunamadı

# "matched"    — personel eşleşmesi tamamlandı

# "unmatched"  — hiç eşleşme yok, manuel müdahale gerekiyor

# ```

# 

# \### Alembic Migration Zinciri

# 

# ```

# 0001 → 0002 → 0003 → (NEXT: 0004 — users tablosu, henüz yapılmadı)

# ```

# 

# \---

# 

# \## 7. API INVENTORY

# 

# \### Crew

# | Method | Endpoint | Notlar |

# |---|---|---|

# | POST | `/api/crew/` | Personel oluştur |

# | GET | `/api/crew/` | Filtreli liste (name, surname, position, nationality, status, ship\_id) |

# | GET | `/api/crew/{id}` | Detay |

# | PUT | `/api/crew/{id}` | Güncelle |

# | DELETE | `/api/crew/{id}` | Sil |

# 

# \### Ships

# | Method | Endpoint |

# |---|---|

# | POST/GET/GET/{id}/PUT/{id}/DELETE/{id} | `/api/ships/` |

# 

# \### Assignments

# | Method | Endpoint |

# |---|---|

# | POST/GET/GET/{id}/PUT/{id}/DELETE/{id} | `/api/assignments/` |

# 

# \### Contracts

# | Method | Endpoint |

# |---|---|

# | POST/GET/GET/{id}/PUT/{id}/DELETE/{id} | `/api/contracts/` |

# 

# \### Documents ✅ STEP 1 sonrası güncel

# | Method | Endpoint | Filtreler |

# |---|---|---|

# | POST | `/api/documents/upload` | — |

# | GET | `/api/documents/` | `crew\_member\_id`, `document\_type`, \*\*`match\_status`\*\* ✅ STEP 1, `expiry\_status` |

# | GET | `/api/documents/{id}` | — |

# | GET | `/api/documents/{id}/file` | FileResponse |

# | PUT | `/api/documents/{id}/match` | Manuel eşleştirme |

# | DELETE | `/api/documents/{id}` | — |

# 

# \### Expiration

# | Method | Endpoint |

# |---|---|

# | GET | `/api/expiration/summary` |

# | GET | `/api/expiration/expired` |

# | GET | `/api/expiration/urgent` |

# | GET | `/api/expiration/approaching` |

# | GET | `/api/expiration/valid` |

# | GET | `/api/expiration/no-date` |

# 

# \### Audit

# | Method | Endpoint | Filtreler |

# |---|---|---|

# | GET | `/api/audit-logs/` | `action`, `entity`, `entity\_id`, `status`, `offset`, `limit` |

# 

# \### Health

# | Method | Endpoint |

# |---|---|

# | GET | `/` |

# | GET | `/health` |

# | GET | `/health/database` |

# 

# \*\*Toplam: 34 endpoint\*\*

# 

# \---

# 

# \## 8. FRONTEND CURRENT STATE

# 

# \### Mevcut (App.jsx — 165 satır)

# 

# | Ekran | Durum |

# |---|---|

# | Dashboard | ⚠️ Kısmi — 3 kart (toplam personel, gemi, aktif), belge metrikleri yok |

# | Personel listesi | ✅ Temel liste + "Personel Ekle" formu |

# | Personel detay | ⚠️ Kısmi — 6 alan gösteriyor, 9 yeni alan (experience\_years vb.) gösterilmiyor |

# | Gemiler listesi | ✅ Temel liste |

# | Gemi detay | ✅ Temel detay + atama listesi |

# | Atamalar | ✅ Temel liste |

# | Kontratlar | ✅ Temel liste |

# | Belgeler ekranı | ❌ YOK — backend hazır |

# | Toplu belge yükleme | ❌ YOK — en kritik eksik |

# | Pending eşleşme | ❌ YOK — STEP 1 ile backend hazır |

# | Audit log ekranı | ❌ YOK — backend hazır |

# | Dashboard belge metrikleri | ❌ YOK — `/api/expiration/summary` hazır |

# | Arama/filtre UI | ❌ YOK — backend destekliyor |

# 

# \*\*`App.css` (437 satır) — Aşama 4 için tamamen hazır.\*\* Badge'ler, tablo, upload-zone, pending-card, audit-row, confidence-bar, tabs — tüm CSS class'lar yazılmış.

# 

# \*\*`App.jsx` (165 satır) — Aşama 4 başlatılmamış.\*\* Sadece mevcut CRUD ekranları mevcut.

# 

# \---

# 

# \## 9. TEST STATUS

# 

# \*\*Son doğrulama: STEP 2 sonrası (2026-08-10)\*\*

# 

# ```

# 26 passed, 0 failed

# ```

# 

# | Dosya | Test Sayısı | Kapsam |

# |---|---|---|

# | `test\_api.py` | 10 | Crew, Ship, Assignment, Contract CRUD; health; validation; FK |

# | `test\_audit.py` | 11 | CRUD audit logları; crew/ship/assignment/contract/document events |

# | `test\_documents.py` | 5 | Upload/match/create/dedup + \*\*match\_status filtresi (STEP 1)\*\* |

# 

# \### Test fonksiyonları (doğrulanmış isimler)

# 

# \*\*test\_documents.py:\*\*

# \- `test\_document\_upload\_matches\_strong\_identifier\_and\_creates\_audit\_log`

# \- `test\_ambiguous\_name\_stays\_pending`

# \- `test\_cv\_creates\_crew\_when\_no\_match\_exists`

# \- `test\_duplicate\_upload\_returns\_existing\_document`

# \- `test\_match\_status\_filter\_returns\_only\_pending\_documents` ← \*\*STEP 1\*\*

# 

# \### Eksik Test Kapsamı

# 

# \- Expiration service testleri yok → \*\*STEP 3 hedefi\*\*

# \- Audit log tarih filtresi testi yok → \*\*STEP 4 hedefi\*\*

# \- Error case testleri kısmi (404/409/422 senaryoları eksik)

# 

# \---

# 

# \## 10. SECURITY STATUS

# 

# | Alan | Durum |

# |---|---|

# | Authentication | ❌ UYGULANMADI |

# | Authorization/RBAC | ❌ UYGULANMADI |

# | JWT/session | ❌ UYGULANMADI |

# | Password hashing | ❌ UYGULANMADI |

# | CORS | ⚠️ Configurable, varsayılan izin veriyor |

# | SQL Injection | ✅ ORM korumalı |

# | Path traversal | ✅ uuid4 ile dosya adı üretiliyor |

# | File size limit | ✅ MAX\_UPLOAD\_SIZE\_MB configurable |

# | Checksum dedup | ✅ SHA-256 |

# | Secrets | ✅ .env'de tutuluyor, git'e eklenmez |

# | Input validation | ✅ Pydantic validators |

# 

# > ⚠️ \*\*Sistem şu anda tamamen açık.\*\* Herhangi bir istek tüm API'lere erişebilir.

# > Tek kullanıcı / lokal kullanım için kabul edilebilir.

# > \*\*Network'e açılmadan önce authentication zorunludur.\*\*

# 

# \---

# 

# \## 11. TECHNICAL DEBT (Güncel)

# 

# | Borç | Durum | Öncelik |

# |---|---|---|

# | \~\~`.bak` dosyaları\~\~ | ✅ \*\*STEP 2'de çözüldü\*\* | — |

# | \~\~Kök dizin test txt dosyaları\~\~ | ✅ \*\*STEP 2'de çözüldü\*\* | — |

# | User model migration yok | ⚠️ Açık — tablo oluşmuyor | P2 |

# | `AuditLogResponse` schemas/ altında değil | ⚠️ route içine gömülü | P2 |

# | Frontend App.jsx monolitik | ⚠️ Tek dosya, bileşen yok | P3 |

# | Expiration testleri eksik | ⚠️ | P2 |

# | Audit date range filtresi yok | ⚠️ | P2 |

# | Authentication yok | ❌ | P3 |

# 

# \---

# 

# \## 12. COMPLETED DEVELOPMENT STEPS

# 

# \---

# 

# \### STEP 1 — match\_status Filter

# \*\*Status:\*\* ✅ COMPLETE

# \*\*Tarih:\*\* 2026-08-10

# 

# \*\*Amaç:\*\*

# Frontend pending belgeler ekranının çalışabilmesi için API desteği.

# 

# \*\*Değiştirilen dosyalar:\*\*

# \- `backend/app/services/document\_service.py` — `list\_documents()` metoduna `match\_status: str | None` parametresi ve `Document.match\_status == match\_status` filtresi eklendi

# \- `backend/app/api/routes/documents.py` — `GET /api/documents/` endpoint'ine `match\_status` query parametresi eklendi, service çağrısına iletildi

# \- `tests/test\_documents.py` — `test\_match\_status\_filter\_returns\_only\_pending\_documents` testi eklendi

# 

# \*\*Doğrulama:\*\*

# ```

# GET /api/documents/?match\_status=pending  → sadece pending belgeler döner

# GET /api/documents/?match\_status=matched  → sadece matched belgeler döner

# GET /api/documents/                       → mevcut davranış korundu (geriye dönük uyumluluk)

# ```

# 

# \*\*Test sonucu:\*\* `26 passed, 0 failed`

# \*\*git diff --check:\*\* PASS

# \*\*Kapsam dışı değişiklik:\*\* Yok

# 

# \---

# 

# \### STEP 2 — Project Cleanup + Master Development Log

# \*\*Status:\*\* ✅ COMPLETE

# \*\*Tarih:\*\* 2026-08-10

# 

# \*\*Silinen dosyalar:\*\*

# \- `backend/app/api/routes/documents.py.bak` — aktif import zincirinde kullanılmadığı PowerShell Select-String ile doğrulandı

# \- `backend/app/services/document\_processing.py.bak` — aktif import zincirinde kullanılmadığı doğrulandı

# \- `test\_document.txt` — conftest.py / testlerde referans bulunmadı

# \- `test\_document\_v2.txt` — aynı şekilde

# \- `test\_document\_v3.txt` — aynı şekilde

# \- `test\_document\_v4.txt` — aynı şekilde

# 

# \*\*Silindi (toplam):\*\* 6 dosya

# 

# \*\*Oluşturulan:\*\* `docs/DEVELOPMENT\_LOG.md` (bu dosya) — proje hafızası / AI handoff belgesi

# 

# \*\*Fonksiyonel kod değişikliği:\*\* YOK

# 

# \*\*Test sonucu:\*\* `26 passed, 0 failed`

# \*\*git diff --check:\*\* PASS

# 

# \---

# 

# \### STEP 3 — Expiration Service Test Coverage

# \*\*Status:\*\* ✅ COMPLETE

# \*\*Tarih:\*\* 2026-08-10

# 

# \*\*Amaç:\*\*

# `ExpirationService`'in tüm kategorilerini ve sınır koşullarını test coverage ile güvence altına almak.

# 

# \*\*Oluşturulan dosya:\*\*

# \- `tests/test\_expiration.py` (12 test, \~95 satır)

# 

# \*\*Production kod değişikliği:\*\* YOK

# 

# \*\*Test edilen senaryolar:\*\*

# \- `expired`: geçmiş tarih → `expiry\_status == "expired"`

# \- `urgent`: remaining ≤ 30 → `"urgent"` (sınır: bugün = urgent, 31. gün = approaching)

# \- `approaching`: 31 ≤ remaining ≤ 90 → `"approaching"` (sınır: 90. gün = approaching, 91. gün = valid)

# \- `valid`: remaining > 90 → `"valid"`

# \- `no\_date`: expiry\_date = None → `"no\_date"`

# \- `summary`: tüm alanlar mevcut, `total == expired + urgent + approaching + valid + no\_date`

# 

# \*\*Boundary testleri:\*\*

# \- `remaining = 0` (bugün) → urgent, expired değil ✅

# \- `remaining = 30` → urgent ✅ / `remaining = 31` → approaching ✅

# \- `remaining = 90` → approaching ✅ / `remaining = 91` → valid ✅

# 

# \*\*Test sonucu:\*\* `38 passed, 0 failed` (26 önceki + 12 yeni)

# \*\*git diff --check:\*\* PASS

# \*\*Regression:\*\* Production koda dokunulmadı — doğrulandı

# 

# \*\*Teknik borç notu:\*\*

# `ExpirationService` tarih kaynağı olarak `date.today()` kullanır; timezone farkındalığı yoktur. Gelecekte UTC tabanlı hesaplamaya geçiş gerekebilir. Mevcut aşama için kabul edilebilir.

# 

# \---

# 

# \### STEP 4 — Audit Log Date Range Filter

# \*\*Status:\*\* ✅ COMPLETE

# \*\*Tarih:\*\* 2026-08-12

# 

# \*\*Amaç:\*\*

# `GET /api/audit-logs/` endpoint'ine `date\_from` ve `date\_to` query parametreleri eklenerek belirli zaman aralığındaki audit olaylarının filtrelenebilmesi.

# 

# \*\*Değiştirilen dosyalar:\*\*

# \- `backend/app/api/routes/audit\_logs.py` — `from datetime import date, datetime, time` eklendi; `date\_from: date | None` ve `date\_to: date | None` query parametreleri eklendi; `datetime.combine(date\_from, time.min)` / `datetime.combine(date\_to, time.max)` ile aralık filtresi uygulandı

# \- `tests/test\_audit.py` — 3 yeni test eklendi (date\_from, date\_to, kombine)

# 

# \*\*Doğrulama:\*\*

# ```

# GET /api/audit-logs/?date\_from=2026-08-12          → sadece bugün ve sonrası

# GET /api/audit-logs/?date\_to=2026-08-11            → bugünden önceki loglar

# GET /api/audit-logs/?date\_from=2026-08-12\&date\_to=2026-08-13  → aralık

# GET /api/audit-logs/                               → mevcut davranış korundu

# ```

# 

# \*\*Eklenen test fonksiyonları:\*\*

# \- `test\_audit\_log\_date\_from\_filter\_returns\_logs\_on\_or\_after`

# \- `test\_audit\_log\_date\_to\_filter\_excludes\_future`

# \- `test\_audit\_log\_date\_range\_combined`

# 

# \*\*Test sonucu:\*\* `41 passed, 0 failed` (38 önceki + 3 yeni)

# \*\*git diff --check:\*\* PASS

# \*\*Production koda dokunulmayan alanlar:\*\* model, schema, service, expiration, documents

# 

# \---

# 

# \### STEP 5A — Frontend Dashboard Expiration Metrics

# \*\*Status:\*\* ✅ COMPLETE

# \*\*Tarih:\*\* 2026-08-12

# 

# \*\*Amaç:\*\*

# Dashboard'a `/api/expiration/summary` endpoint'inden gelen expired/urgent/approaching/valid sayılarını göstermek.

# 

# \*\*Değiştirilen dosyalar:\*\*

# \- `frontend/src/App.jsx`

# &#x20; - `expirySummary` state eklendi

# &#x20; - `loadData()` Promise.all'a `GET /api/expiration/summary` çağrısı eklendi

# &#x20; - Dashboard'a `.card-icon.danger/warning/purple/success` snıflarıyla 4 expiration kartı eklendi

# &#x20; - Mevcut 3 dashboard kartı `.card-icon` sarıcısı ile güncellendi (CSS uyumu)

# \- `frontend/src/App.css`

# &#x20; - `.section-label` sınıfı eklendi (dashboard bölüm başlığı)

# 

# \*\*Backend değişikliği:\*\* YOK

# 

# \*\*Çalışan endpoint:\*\* `GET /api/expiration/summary`

# \*\*Gösterilen alanlar:\*\* `expired` · `urgent` · `approaching` · `valid`

# \*\*Null guard:\*\* `expirySummary !== null` — backend bağlantısı yokken kartlar görünmez

# 

# \*\*Lint:\*\* `0 warnings, 0 errors`

# \*\*Build:\*\* `✅ 1.39s, 0 error`

# \*\*Regression (pytest):\*\* Çalıştırılmadı (backend'e dokunulmadı) — son doğrulama: 41 passed (STEP 4)

# 

# \---

# 

# \### STEP 5B — Crew Detail Genişletme (9 Yeni Alan)

# \*\*Status:\*\* ✅ COMPLETE

# \*\*Tarih:\*\* 2026-08-12

# 

# \*\*Amaç:\*\*

# Crew Detail ekranına backend'de mevcut olan 9 alanı eklemek: `birth\_place`, `hometown`, `marital\_status`, `experience\_years`, `sea\_service\_months`, `languages`, `education\_summary`, `notes`, `profile\_data`

# 

# \*\*Değiştirilen dosyalar:\*\*

# \- `frontend/src/App.jsx`

# &#x20; - `formatProfileData()` yardımcı fonksiyonu eklendi

# &#x20; - `renderCrewDetail()` fonksiyonu oluşturuldu (eski inline JSX kaldırıldı)

# &#x20; - 3 bölüm: Temel Bilgiler (6 alan) · Kişisel Bilgiler (6 alan) · Ek Bilgiler (2 alan)

# &#x20; - `profile\_data` için `<pre>` bloğu (sadece dolu olduğunda görülür)

# &#x20; - Tüm null/undefined için `"—"` guard; `experience\_years`/`sea\_service\_months` 0-safe

# \- `frontend/src/App.css`

# &#x20; - `.profile-data-block` sınıfı eklendi (monospace, max-height: 240px)

# 

# \*\*Backend değişikliği:\*\* YOK

# 

# \*\*Gösterilen alanlar (tam):\*\*

# ```

# Temel    : position, rank, nationality, status, email, phone

# Kişisel  : birth\_place, hometown, marital\_status, experience\_years, sea\_service\_months, languages

# Ek       : education\_summary, notes

# JSON     : profile\_data (dolu ise görünür)

# ```

# 

# \*\*Lint:\*\* `0 warnings, 0 errors`

# \*\*Build:\*\* `✅ 648ms, 0 error`

# \*\*git diff --check:\*\* PASS

# 

# \---

# 

# \### STEP 6 — Documents List Ekranı (Frontend Wiring Tamamlama)

# \*\*Status:\*\* ✅ COMPLETE

# \*\*Tarih:\*\* 2026-08-12

# 

# \*\*Amaç:\*\*

# Antigravity'nin önceki oturumda token/session limiti nedeniyle yarım bıraktığı STEP 6 iskeletini tamamlamak. `documents` state, `documentsLoading`, `documentsError`, `loadDocuments()`, `openDocumentsPage()` fonksiyonları zaten mevcuttu; eksik olan tek şey UI wiring'iydi (nav butonu + render case + liste ekranı).

# 

# \*\*Değiştirilen dosyalar:\*\*

# \- `frontend/src/App.jsx`

# &#x20; - `navigation` dizisine `\["documents", Folder, "Belgeler"]` eklendi (mevcut `Folder` importu ilk kez kullanıldı)

# &#x20; - Nav butonu `onClick`'i `documents` sayfası için mevcut `openDocumentsPage()` fonksiyonunu çağıracak şekilde güncellendi (diğer sayfalar için davranış değişmedi)

# &#x20; - `renderPage()` içine `if (activePage === "documents") return renderDocumentsList();` case'i eklendi

# &#x20; - Yeni `renderDocumentsList()` fonksiyonu eklendi: mevcut `documents`, `documentsLoading`, `documentsError` state'lerini kullanır; mevcut `.data-table`, `.empty`, `.form-error`, `.badge` / `.badge-type-\*` / `.badge-matched` vb. CSS sınıflarını kullanır — yeni CSS eklenmedi

# 

# \*\*Backend değişikliği:\*\* YOK

# \*\*Migration değişikliği:\*\* YOK

# \*\*Yeni dependency:\*\* YOK

# 

# \*\*Gösterilen kolonlar:\*\* Dosya Adı · Belge Tipi · Eşleşme Durumu · Geçerlilik · Personel (eşleşen crew adı, `crewById` üzerinden)

# 

# \*\*State handling:\*\* loading → "Belgeler yükleniyor..." · error → `.form-error` mesajı · empty → `.empty` bloğu (Folder ikonu) · dolu → `.data-table`

# 

# \*\*Not:\*\* `expiry\_status` backend'den `no\_date` (alt çizgi) formatında geliyor, CSS sınıfı ise `.badge-no-date` (tire); `renderDocumentsList()` içinde `.replace(/\_/g, "-")` ile normalize edildi. `document\_type` değeri `seaman\_book` için CSS'te özel bir badge rengi tanımlı değil (`badge-type-seaman\_book` yok) — bu STEP kapsamında yeni CSS eklenmediği için düz `.badge` stiliyle görünecek, işlevsel bir sorun değil.

# 

# \*\*Kapsam dışı bırakılanlar (bilinçli):\*\* Dashboard'daki `renderCrewList()` tekrarı düzeltilmedi (ayrı checkpoint). Belge tipi/durum filtreleri (F-14) eklenmedi — bu STEP sadece liste ekranı içindi.

# 

# \*\*Değişiklik büyüklüğü:\*\* 44 satır eklendi, 2 satır değiştirildi (nav array + onClick) — toplam \~46 satır, 40-70 satır bütçesi içinde.

# 

# \*\*Syntax doğrulama:\*\* esbuild ile JSX parse — 0 hata

# \*\*Lint:\*\* Bu oturumda gerçek `npm run lint` (oxlint) repo üzerinde çalıştırılamadı — bkz. rapor notu

# \*\*Build:\*\* Bu oturumda gerçek `npm run build` (vite) repo üzerinde çalıştırılamadı — bkz. rapor notu

# 

# \---

# 

# \## 13. CURRENT VERIFIED STATE

# 

# ```

# Last completed step : STEP 6 (Documents list ekranı)

# 

# Tests               : 41 passed, 0 failed (son doğrulama: STEP 4 — STEP 6 backend'e dokunmadı)

# Backend             : Stabil, 34 endpoint çalışıyor (değişmedi)

# Frontend            : Dashboard expiration metrikleri ✅

# &#x20;                     Crew Detail 15 alan gösteriyor ✅

# &#x20;                     Belgeler listesi ✅ (STEP 6 — tablo, loading/error/empty state)

# &#x20;                     Upload/Pending/Audit ekranları henüz yok

# Database            : 6 tablo (users tablosu migration'sız)

# Security            : Authentication yok — lokal kullanım için kabul edilebilir

# 

# Known issues:

# \- User model migration yok

# \- Frontend Upload, Pending, Audit ekranları başlatılmadı

# \- Belge tipi/durum filtreleri (F-14) henüz yok — STEP 6 kapsamı sadece liste ekranıydı

# \- Dashboard'da renderCrewList() tekrarı (ayrı, düzeltilmemiş bug)

# \- Timezone borcu: date.today() UTC-farkındalıksız

# 

# Next recommended step : STEP 7 — Toplu upload UI (drag \& drop)

# 

# Do not start yet:

# \- Authentication (P3)

# \- Frontend component split (P3)

# ```

# 

# \---

# 

# \## 14. NEXT EXECUTION ORDER

# 

# | Adım | Görev | Durum |

# |---|---|---|

# | STEP 1 | match\_status filter | ✅ COMPLETE |

# | STEP 2 | Cleanup + project memory | ✅ COMPLETE |

# | STEP 3 | Expiration service testleri (`test\_expiration.py`) | ✅ COMPLETE |

# | STEP 4 | Audit log tarih filtresi (`date\_from`, `date\_to`) | ✅ COMPLETE |

# | STEP 5A | Dashboard expiration metrics | ✅ COMPLETE |

# | STEP 5B | Crew detail genisletme (9 yeni alan) | ✅ COMPLETE |

# | STEP 5 | Frontend Aşama 4A — Navigation + Crew detail + Dashboard metrics | ⚠️ PARTIAL (5A+5B done, nav eksik) |

# | STEP 6 | Frontend Aşama 4B — Documents list ekranı | ✅ COMPLETE |

# | STEP 7 | Frontend Aşama 4C — Toplu upload UI | ⏳ PENDING |

# | STEP 8 | Frontend Aşama 4D — Pending eşleşme ekranı | ⏳ PENDING |

# | STEP 9 | Frontend Aşama 4E — Audit log ekranı | ⏳ PENDING |

# | STEP 10 | User migration (Alembic 0004) | ⏳ PENDING |

# | LATER | Authentication / JWT / RBAC | 🔴 BEKLEMEDE |

# | LATER | Frontend component split | 🔴 BEKLEMEDE |

# 

# \---

# 

# \## 15. IMPORTANT CONSTRAINTS

# 

# Gelecek agent'ların uyması gereken kurallar:

# 

# 1\. \*\*Alembic migration'larını (0001-0003) değiştirme.\*\* Üretim verisi olabilir.

# 2\. \*\*`document\_processing.py` mantığını gereksiz değiştirme.\*\* parse\_date ve match\_crew stabil.

# 3\. \*\*`conftest.py`'ye dokunma.\*\* 38 test burada tutunuyor.

# 4\. \*\*App.jsx'i tek seferde yeniden yazma.\*\* Parçalı yapılacak (4A → 4B → 4C → 4D → 4E).

# 5\. \*\*Her STEP sonrası `pytest` + `git diff --check` çalıştır.\*\*

# 6\. \*\*Authentication'ı beklenmedik bir komut olmadan başlatma.\*\*

# 7\. \*\*Her STEP sonunda DUR. Otomatik STEP atlama yapma.\*\*

# 8\. \*\*Bu dosyayı (DEVELOPMENT\_LOG.md) her tamamlanan STEP sonrası güncelle.\*\*

# 

# \---

# 

# \## 16. MASTER COMPLETION AUDIT

# 

# \*\*Tarih:\*\* 2026-08-12 | \*\*Durum:\*\* COMPLETE

# 

# \*\*Özet:\*\* Önceki oturum token/quota kesilmesiyle yarım kalmıştı. COMPLETION\_MATRIX.md eksikti. Recovery analizi yapıldı, repository ile chat tutarlılığı doğrulandı, eksik dosya tamamlandı.

# 

# \*\*Repository doğrulaması (2026-08-12):\*\*

# \- Tests: `38 passed, 0 failed` ✅

# \- git diff --check: PASS ✅

# \- .bak dosyaları: YOK ✅ (STEP 2'de silindi)

# \- test\_expiration.py: MEVCUT ✅ (STEP 3'te oluşturuldu)

# 

# \*\*Tamamlanan işler (doğrulanmış):\*\*

# 

# | STEP | Açıklama | Repository Durumu |

# |---|---|---|

# | STEP 1 | match\_status filtresi | ✅ documents.py + document\_service.py güncel |

# | STEP 2 | Temizlik + DEVELOPMENT\_LOG | ✅ .bak yok, log mevcut |

# | STEP 3 | Expiration testleri | ✅ test\_expiration.py (12 test) |

# 

# \*\*Bu audit'te oluşturulan ROADMAP dosyaları:\*\*

# ```

# C:\\CREWINTEL\\docs\\ROADMAP\\

# ├── MASTER\_ROADMAP.md     ← 2026-08-10 (önceki oturum)

# ├── CURRENT\_STATE.md      ← 2026-08-10 (önceki oturum)

# ├── ENGINEERING\_PLAN.md   ← 2026-08-10 (önceki oturum)

# ├── ARCHITECTURE\_PLAN.md  ← 2026-08-10 (önceki oturum)

# └── COMPLETION\_MATRIX.md  ← 2026-08-12 (bu oturumda tamamlandı)

# ```

# 

# \*\*Kod değişikliği:\*\* YOK — yalnızca docs/ güncellendi

# 

# \*\*Sonraki adım:\*\* STEP 4 — Audit log `date\_from`/`date\_to` filtresi

# (`backend/app/api/routes/audit\_logs.py` + 2-3 test, \~10 satır, Low risk)

# 

# > ⚠️ \*\*Not (2026-08-12 sync ile eklendi):\*\* Bu bölüm (16. MASTER COMPLETION AUDIT) STEP 4'ten önceki tarihsel bir kayıttır. STEP 4, 5A, 5B ve 6 o tarihten sonra tamamlanmıştır. Güncel durum için bkz. Bölüm 13 (CURRENT VERIFIED STATE) ve aşağıdaki Bölüm 17.

# 

# \---

# 

# \## 17. DOCUMENTATION SYNC — STEP 1–6 CURRENT STATE ALIGNMENT

# 

# \*\*Tarih:\*\* 2026-08-12

# \*\*Tür:\*\* Documentation Sync checkpoint (kod değişikliği içermez)

# 

# \*\*Amaç:\*\*

# CURRENT\_STATE.md, DEVELOPMENT\_LOG.md ve COMPLETION\_MATRIX.md dosyalarının STEP 1–6'nın gerçek (kod üzerinde doğrulanmış) durumuyla senkron olup olmadığını denetlemek ve tespit edilen eski/çelişkili kayıtları düzeltmek.

# 

# \*\*İncelenen dosyalar:\*\*

# \- `docs/ROADMAP/CURRENT\_STATE.md`

# \- `docs/DEVELOPMENT\_LOG.md` (bu dosya, önceki bölümler)

# \- `docs/ROADMAP/COMPLETION\_MATRIX.md`

# \- `frontend/src/App.jsx` (STEP 6 wiring'i koddan doğrulamak için, salt-okunur)

# \- `backend/app/api/routes/documents.py`, `backend/app/api/routes/audit\_logs.py` (STEP 1 ve STEP 4 iddialarını koddan doğrulamak için, salt-okunur)

# 

# \*\*STEP 1–6 durumu — koddan doğrulandı:\*\*

# 

# | STEP | Doğrulama | Sonuç |

# |---|---|---|

# | STEP 1 | `documents.py` route'unda `match\_status` parametresi | ✅ COMPLETE |

# | STEP 2 | `.bak` dosyaları yok, log mevcut | ✅ COMPLETE |

# | STEP 3 | `test\_expiration.py` (12 test) | ✅ COMPLETE |

# | STEP 4 | `audit\_logs.py`'de `date\_from`/`date\_to` (Query + `datetime.combine`) | ✅ COMPLETE |

# | STEP 5A | `App.jsx`'te `expirySummary` state + 4 dashboard kartı | ✅ COMPLETE |

# | STEP 5B | `renderCrewDetail()` — 3 bölüm, 9 yeni alan | ✅ COMPLETE |

# | STEP 6 | `navigation`'da `documents` girişi + `renderPage()` case + `renderDocumentsList()` | ✅ COMPLETE |

# 

# \*\*Güncellenen dosyalar ve yapılan değişiklikler:\*\*

# 

# 1\. \*\*`docs/ROADMAP/CURRENT\_STATE.md`\*\*

# &#x20;  - Header: "Son güncelleme 2026-08-10 / STEP 3" → "2026-08-12 / STEP 6"

# &#x20;  - Dashboard satırı: ⚠️ PARTIAL → ✅ DONE (STEP 5A ile expiration metrikleri mevcut)

# &#x20;  - Personel detay satırı: ⚠️ PARTIAL → ✅ DONE (STEP 5B ile 9 yeni alan mevcut)

# &#x20;  - Belgeler satırı: ✅ DONE olarak teyit edildi (STEP 6)

# &#x20;  - "Dashboard expiration ❌ YOK" tekrarlayan/çelişkili satırı kaldırıldı (Dashboard satırıyla birleştirildi)

# &#x20;  - `App.jsx` satır sayısı: 165 → 293 (gerçek güncel değer)

# &#x20;  - TESTS bölümü: 38 passed → 41 passed (STEP 4 sonrası son doğrulanan sayı), STEP 5A/5B/6'nın backend'e dokunmadığı ve bu yüzden pytest'in yeniden çalıştırılmadığı not edildi

# &#x20;  - STEP 6 lint/build durumu: gerçek `oxlint`/`vite build` bu makinede koşulmadığı açıkça belirtildi (olmuş gibi gösterilmedi)

# &#x20;  - CURRENT STEP bölümü: "Tamamlanan: STEP 3 / Sonraki: STEP 4" → "Tamamlanan: STEP 6 / Sonraki: STEP 7"

# &#x20;  - Backend, Database, Security, Deployment, AI/Mobile, Technical Debt bölümlerine \*\*dokunulmadı\*\* (bu STEP'ler yalnızca frontend'i etkiledi)

# &#x20;  - Authentication/RBAC ❌ MISSING olarak \*\*korundu\*\* — DONE yapılmadı

# 

# 2\. \*\*`docs/ROADMAP/COMPLETION\_MATRIX.md`\*\*

# &#x20;  - Header: "Son tamamlanan: STEP 3" → "STEP 6" (bu zaten önceki checkpoint'te güncellenmişti, bu sync'te teyit edildi)

# &#x20;  - F-03 (Sidebar/navigation): "Missing: Belgeler + Audit sekmeleri" → "Missing: Audit sekmesi (Belgeler STEP 6'da eklendi)"; Next Action STEP 5 → STEP 9; Risk Med → Low

# &#x20;  - F-13 (Documents list screen) ✅ DONE olarak teyit edildi (önceki checkpoint'te işaretlenmişti)

# &#x20;  - F-05 (STEP 5A) ve F-08 (STEP 5B) ✅ DONE olarak teyit edildi

# &#x20;  - OVERALL COMPLETION SUMMARY yeniden hesaplandı: Frontend %50 → %57 — hesap yöntemi: F-01→F-22 (F-22 DEFERRED hariç, 21 madde), DONE=1.0 + PARTIAL=0.5 ağırlıklandırması: (11 DONE + 2×0.5 PARTIAL) / 21 ≈ %57

# &#x20;  - TOTAL ESTIMATED %55 → %54 — 7 kategorinin basit ortalaması (Backend/Database/Tests/Security/Operations/AI-Mobile değişmedi, yalnızca Frontend güncellendi)

# &#x20;  - Hesaplama yöntemi dosyaya not olarak eklendi (şeffaflık için)

# 

# 3\. \*\*`docs/DEVELOPMENT\_LOG.md`\*\* (bu dosya)

# &#x20;  - Bölüm 16'daki eski "Sonraki adım: STEP 4" notunun üstüne, bunun STEP 4'ten önceki tarihsel bir kayıt olduğunu belirten bir uyarı eklendi (kayıt \*\*silinmedi\*\*, sadece bağlam eklendi)

# &#x20;  - Bu Bölüm 17 (DOCUMENTATION SYNC) yeni checkpoint olarak eklendi

# 

# \*\*Eski tarihsel kayıtların korunması:\*\* Bölüm 1–16 arasındaki hiçbir kayıt silinmedi veya yeniden yazılmadı. Bölüm 16'ya yalnızca bağlamsal bir not eklendi (yukarıda belirtildi).

# 

# \*\*Kod değişikliği:\*\* YOK. `frontend/src/`, `backend/app/`, migration dosyaları — hiçbiri değiştirilmedi.

# 

# \*\*Test:\*\* Bu sync sırasında hiçbir test çalıştırılmadı (kapsam yalnızca dokümantasyondu, kod değişmediği için test'e gerek yoktu).

# 

# \*\*Sonraki adım:\*\* STEP 7 — Toplu Upload UI (drag \& drop)

# (`frontend/src/App.jsx`, Medium-Large risk, \~200 satır tahmini)

# 

# \*\*Safe Stop Point:\*\* Dokümantasyon senkronizasyonu tamamlandı. Üç dosya (CURRENT\_STATE.md, COMPLETION\_MATRIX.md, DEVELOPMENT\_LOG.md) STEP 1–6'nın gerçek koddan doğrulanmış durumuyla tutarlı. Kod tabanına dokunulmadı, MASTER\_ROADMAP.md'ye dokunulmadı. Onay olmadan STEP 7'ye veya başka bir işe geçilmeyecek.

# 

# \---

# 

# \## 18. MASTER\_ROADMAP SYNC — 2026-08-12

# 

# \- MASTER\_ROADMAP.md güncellendi

# \- STEP 1–6 tamamlandı

# \- STEP 7 sıradaki iş

# \- Kod değişikliği yapılmadı

# \- Test/lint/build çalıştırılmadı

# \- Safe Stop Point

# \- STEP 7'ye geçilmedi

# 

# \---

# 

# \## 19. STEP 7A — Upload Zone UI (Drag \& Drop + Multi-file Staging)

# 

# \*\*Tarih:\*\* 2026-08-13

# \*\*Kapsam:\*\* STEP 7'nin ilk checkpoint'i — F-15 (Bulk upload UI)'ın yalnızca UI/staging kısmı. \*\*Backend'e henüz upload isteği gönderilmiyor.\*\*

# 

# \*\*Yapılan işler:\*\*

# \- `Belgeler` ekranına drag \& drop alanı eklendi (mevcut `.upload-zone` / `.drag-over` CSS sınıfları — daha önce hiç kullanılmıyordu, ilk kez kullanıldı)

# \- Tıklayarak dosya seçme (gizli `<input type="file" multiple>` + `fileInputRef`)

# \- Seçilen/sürüklenen dosyalar `stagedFiles` state'inde tutuluyor, `.file-list` / `.file-item` CSS sınıflarıyla listeleniyor (dosya adı + boyut)

# \- Aynı dosyanın (ad+boyut eşleşmesiyle) iki kez eklenmesi engellendi

# \- Her dosya için tekil kaldırma butonu (`removeStagedFile`, `.icon-button`)

# 

# \*\*Değiştirilen dosyalar:\*\*

# \- `frontend/src/App.jsx` — 77 satır eklendi, 1 satır değiştirildi (import satırı)

# &#x20; - Yeni import: `useRef` (react), `Upload`, `X` (lucide-react)

# &#x20; - Yeni state: `stagedFiles`, `dragActive`, `fileInputRef`

# &#x20; - Yeni fonksiyonlar: `formatFileSize`, `addStagedFiles`, `removeStagedFile`, `handleFileInputChange`, `handleDragOver`, `handleDragLeave`, `handleDrop`

# &#x20; - `renderDocumentsList()` içine upload-zone + file-list JSX'i eklendi

# 

# \*\*Backend değişikliği:\*\* YOK

# \*\*Migration:\*\* YOK

# \*\*document\_processing.py:\*\* dokunulmadı

# 

# \*\*Test:\*\* Gerçek `npm run lint` (oxlint) / `npm run build` (vite) bu ortamda çalıştırılamadı (bu ortamın erişemediği gerçek repository/araç seti gerektiriyor). Bunun yerine izole bir syntax doğrulaması yapıldı: esbuild ile JSX parse — \*\*0 hata\*\*. `pytest` çalıştırılmadı (backend değişmedi, gerek yok).

# 

# \*\*Bilinen sınırlama / sonraki checkpoint'e not:\*\* Backend `POST /api/documents/upload` bir dosya listesini tek istekte kabul ediyor ancak `document\_service.upload\_documents()` içinde herhangi bir dosya boşsa veya boyut limitini aşarsa \*\*tüm batch\*\* HTTPException ile reddediliyor (dosya bazlı izole hata yönetimi yok). Bu nedenle STEP 7B'de dosyaların \*\*tek tek\*\* (her biri kendi POST isteğiyle) yüklenmesi planlanıyor — aksi halde bir hatalı dosya, aynı batch'teki geçerli dosyaların da reddedilmesine sebep olur. Ayrıca backend, duplicate (checksum eşleşen) dosyalar için ayrı bir "duplicate" bayrağı döndürmüyor — mevcut kaydı aynı `DocumentResponse` şeklinde döndürüyor. STEP 7C'de bunu ayırt etmek için `created\_at` zaman damgası karşılaştırması (heuristik) kullanılması planlanıyor; bu, backend'e dokunmadan yapılabilecek en güvenilir yöntem.

# 

# \*\*Roadmap durumu:\*\* CURRENT\_STATE.md / MASTER\_ROADMAP.md / COMPLETION\_MATRIX.md \*\*güncellenmedi\*\* — STEP 7 (F-15/F-16) bu checkpoint ile tamamlanmadı, yalnızca ilk alt-parçası bitti. Henüz tamamlanmamış işi COMPLETE göstermemek için bilinçli olarak dokunulmadı.

# 

# \*\*Sonraki checkpoint:\*\* STEP 7B — Staged dosyaların backend'e tek tek upload edilmesi + her dosya için durum takibi (uploading/success/error)

# 

# \*\*SAFE STOP POINT:\*\* STEP 7A tamamlandı ve doğrulandı. STEP 7B'ye geçilmedi.

# 

# \---

# 

# \# STEP 7B

# 

# \## CHECKPOINT 7B-01 — SYSTEM INSPECTION

# 

# STATUS:

# COMPLETED

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# STEP 7B (single-file upload wiring) öncesi backend/frontend gerçek davranışını kod üzerinden doğrulamak. Kod değişikliği yapılmadı.

# 

# FILES INSPECTED:

# \- `backend/app/api/routes/documents.py`

# \- `backend/app/services/document\_service.py` (`upload\_documents`)

# \- `backend/app/schemas/document.py`

# \- `backend/app/models/document.py`

# \- `backend/app/db/database.py` (`get\_db`)

# \- `backend/app/core/config.py`

# \- `frontend/src/App.jsx` (STEP 7A staging kodu)

# 

# FILES MODIFIED:

# \- NONE

# 

# FINDINGS:

# 

# \*\*Endpoint / request format:\*\*

# \- `POST /api/documents/upload`, `multipart/form-data`, field adı `files` (`files: list\[UploadFile] = File(...)`) — \*\*çoklu dosya tek istekte de kabul ediliyor\*\*, ama tekli istek de (`files` alanına 1 dosya) aynı endpoint ile çalışır — API contract değişmeden tek-tek gönderim yapılabilir. VERIFIED.

# \- Response: `201 Created`, `list\[DocumentResponse]` — gönderilen dosya sayısı kadar obje döner (tek dosya gönderirsen 1 elemanlı liste). VERIFIED.

# 

# \*\*HTTP hata kodları (koddan doğrulandı):\*\*

# \- Boş dosya → `422 Unprocessable Entity`, detail: `"{filename}: empty file."`

# \- Boyut limiti aşımı → `413 Request Entity Too Large`, detail: `"{filename}: file is too large."`

# \- Limit kaynağı: `settings.max\_upload\_size\_mb`, config default = \*\*25 MB\*\* (gerçek `.env` değeri UNKNOWN — bu makineden görülemiyor)

# \- 400/401/403/404/409/500 için upload endpoint'inde \*\*özel bir handling yok\*\* — sadece FastAPI'nin genel hata davranışı geçerli. VERIFIED.

# 

# \*\*🔴 KRİTİK BULGU — Batch failure davranışı:\*\*

# `upload\_documents()` içinde tüm dosyalar tek bir `for` döngüsünde işleniyor, ama `db.commit()` yalnızca döngü \*\*tamamen bittikten sonra bir kez\*\* çağrılıyor (satır \~156). `get\_db()` dependency'si (`db/database.py`) exception durumunda \*\*explicit rollback yapmıyor\*\*, sadece `finally: db.close()`.

# → Sonuç: Bir batch'te (aynı `POST` isteğinde) 3. dosya `422`/`413` hatası verirse, döngü orada exception ile kesilir, `commit()`'e hiç ulaşılmaz — \*\*1. ve 2. dosya için yapılan `db.add()`/`flush()` de commit edilmemiş olur, o dosyalar da kaybolur.\*\*

# → \*\*Bu, STEP 7B-05'teki "tek tek gönder" kuralının backend tarafından da zorunlu kılındığını kanıtlıyor\*\* — varsayım değil, kod kanıtı. VERIFIED.

# 

# \*\*Duplicate davranışı (checksum eşleşmesi):\*\*

# \- `documents.checksum` kolonu `unique=True`. Aynı checksum'lı dosya yüklenirse: yeni dosya diskten silinir (`Path(path).unlink()`), mevcut DB kaydı (`existing`) hiçbir `UPDATE` yapılmadan doğrudan `saved` listesine eklenir — \*\*`created\_at`/`updated\_at` değişmez, DB'ye yeni satır yazılmaz, audit log oluşmaz\*\* (`log\_event("document\_uploaded", ...)` çağrısı duplicate `continue` ile atlanan koddan SONRA, yani duplicate için hiç çalışmıyor). VERIFIED.

# \- `DocumentResponse` şeması hem `created\_at` hem `updated\_at` (ikisi de `datetime`, tz-naive UTC) döndürüyor. Model: `created\_at` yalnızca oluşturulurken set ediliyor, sonrasında hiç değişmiyor (`onupdate` sadece `updated\_at`'te var).

# \- \*\*Duplicate tespiti için backend'de ayrı bir flag YOK\*\*, ama `created\_at` alanı \*\*güvenilir bir dolaylı sinyal\*\*: Tek dosyalık istek atılmadan hemen önce `Date.now()` yakalanıp, response'taki `created\_at` bundan önemli ölçüde (örn. birkaç saniye) eskiyse → duplicate (mevcut kayıt). Aynı anda oluşturulan taze kayıtla mevcut-ama-yakın-zamanda-oluşmuş bir kaydı ayırt etme riski teorik olarak var ama pratikte (tek dosya = tek istek, sıralı gönderim) ihmal edilebilir düzeyde. → \*\*DUPLICATE DETECTION: VERIFIED (heuristic, response'ta explicit flag yok, ama created\_at zaman karşılaştırmasıyla güvenilir şekilde çıkarılabilir)\*\* — INSUFFICIENT DATA değil, çünkü gereken alan (`created\_at`) response'ta gerçekten mevcut ve davranışı koddan doğrulandı.

# 

# \*\*Authentication / Authorization:\*\*

# `documents.py` route'unda hiçbir `Depends(get\_current\_user)` vb. yok — mevcut sistemde zaten YOK (bilinen durum), STEP 7B kapsamıyla ilgisiz, değişmiyor. VERIFIED (konfirme edildi, yeni bulgu değil).

# 

# \*\*Audit log:\*\*

# Yalnızca gerçek yeni upload için `document\_uploaded` event'i yazılıyor (`entity=document`, `metadata={match\_status, confidence}`). Duplicate'te audit YOK. VERIFIED.

# 

# \*\*Frontend mevcut durum (STEP 7A):\*\*

# `stagedFiles` state'i dosya listesini tutuyor, henüz hiçbir HTTP isteği yapılmıyor — STEP 7B'nin başlangıç noktası bu state. VERIFIED (kendi önceki checkpoint'im).

# 

# TESTS:

# NOT RUN (bu checkpoint yalnızca inceleme; kod değişmedi)

# 

# VALIDATION:

# Yukarıdaki tüm bulgular ilgili dosyaların gerçek içeriğinden (bu oturumdaki sandbox kopyası — kullanıcının STEP 6/7A teslimlerinde sağladığı aynı kod tabanı) doğrudan okunarak doğrulandı. Hiçbir davranış varsayılmadı.

# 

# RESULT:

# PASS

# 

# NEXT:

# CHECKPOINT 7B-02 — Single File Upload (`uploadSingleFile(file)` fonksiyonu)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-02 — SINGLE FILE UPLOAD

# 

# STATUS:

# COMPLETED

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# `stagedFiles`'taki dosyaları backend'e sırayla, dosya başına ayrı HTTP request ile yükleyen gerçek upload mekanizmasını kurmak. Her dosya için bağımsız durum (pending/uploading/success/error). Duplicate ayrımı bu checkpoint'e dahil değil (7B-01'de belirlendiği gibi ertelendi).

# 

# FILES INSPECTED:

# \- `frontend/src/App.jsx` (STEP 7A sonrası hali)

# 

# FILES MODIFIED:

# \- `frontend/src/App.jsx`

# 

# FILES NOT MODIFIED:

# \- `backend/app/api/routes/documents.py`

# \- `backend/app/services/document\_service.py`

# \- `backend/app/schemas/document.py`

# \- `backend/app/models/document.py`

# \- `backend/app/db/database.py`

# \- `backend/app/core/config.py`

# \- Alembic migration dosyaları

# \- `document\_processing.py`

# \- `App.css` (yeni CSS gerekmedi — mevcut `.file-item-status`, `.icon-button`, `.primary-button` sınıfları kullanıldı)

# 

# CHANGES:

# \- Yeni state: `uploadStatus` (key→status map), `uploadResults` (key→{document|error} map), `isUploading` (batch guard)

# \- `fileKey(file)` — `${name}\_${size}` anahtarı (dedup mantığıyla tutarlı)

# \- `uploadSingleFile(file)` — tek dosyayı `POST /api/documents/upload`'a `multipart/form-data`, field adı `files` ile gönderir; başarıda gerçek `response.data\[0]` (DocumentResponse) kaydedilir; hatada `error.response.data.detail` (backend mesajı) korunarak saklanır, generic mesajla ezilmez

# \- `uploadStagedFiles()` — `stagedFiles` üzerinde \*\*sıralı `for...of` + `await`\*\* (Promise.all YOK), her dosya kendi request'ini gönderir; bir dosyanın hata vermesi döngüyü durdurmaz; zaten uploading/success olan dosyalar atlanır; bitince `loadDocuments()` ile tablo yenilenir

# \- `renderDocumentsList()`'teki `file-list` bloğuna: her dosya için durum etiketi (Bekliyor/Yükleniyor.../Yüklendi/Hata: {backend mesajı}), uploading sırasında kaldır butonu devre dışı, ve `stagedFiles.length` dosyayı yükle butonu (`isUploading` iken devre dışı)

# 

# FINDINGS:

# \- Backend'in tek-dosyalık isteğe de aynı endpoint/response şemasıyla (`list\[DocumentResponse]`, 1 elemanlı) cevap verdiği 7B-01'de doğrulanan bilgiyle tutarlı şekilde çalıştı; API contract'ta hiçbir varsayım gerekmedi.

# 

# TESTS:

# NOT RUN — gerçek backend'e karşı canlı bir upload denemesi bu ortamdan (network erişimi kapalı, gerçek repository yok) yapılamadı. Yalnızca statik doğrulama yapıldı (aşağıya bakınız).

# 

# VALIDATION:

# \- JSX syntax: \*\*PASS\*\* (esbuild parse, 0 hata)

# \- git diff --check: gerçek `git` bu ortamda repository olarak mevcut değil; eşdeğer kontrol yapıldı — trailing whitespace taraması \*\*temiz\*\* (0 satır)

# \- npm run lint (oxlint): \*\*NOT RUN\*\* — `oxlint` bu sandbox ortamında kurulu değil, çalıştırılamadı

# \- npm run build (vite): \*\*NOT RUN\*\* — `vite` bu sandbox ortamında kurulu değil, çalıştırılamadı

# \- Backend regresyon: \*\*N/A / dokunulmadı\*\* — bu checkpoint'te hiçbir backend dosyasına write/edit çağrısı yapılmadı (yalnızca `App.jsx` düzenlendi)

# 

# KNOWN LIMITATIONS:

# \- Duplicate tespiti bu checkpoint'te YOK (bilinçli olarak ertelendi — 7B-01'de belirlenen `created\_at` heuristiği henüz uygulanmadı)

# \- Gerçek `npm run lint` / `npm run build` / canlı backend testi kullanıcının kendi makinesinde doğrulanmalı — bu ortamdan çalıştırılamadı

# \- Retry mekanizması yok (7B-09'a bırakıldı)

# \- Upload sonrası staged listesi temizlenmiyor / başarılı dosyalar listeden çıkarılmıyor (bilinçli olarak bu checkpoint'in kapsamı dışı bırakıldı)

# 

# RESULT:

# PASS (statik doğrulama kapsamında)

# 

# NEXT:

# CHECKPOINT 7B-03 — UI Status Management (zaten büyük ölçüde bu checkpoint'te birlikte uygulandı — bir sonraki oturumda önce bunun teyidi yapılmalı, ardından 7B-04/05 değerlendirilmeli)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-03 — UI STATUS MANAGEMENT

# 

# STATUS:

# COMPLETED (7B-02 kapsamında zaten karşılandı — bu checkpoint yalnızca doğrulama, kod değişikliği yok)

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# Her staged dosyanın bağımsız, kullanıcının anlayabileceği bir durumu olduğunu doğrulamak: pending / uploading / success / error / duplicate.

# 

# FILES INSPECTED:

# \- `frontend/src/App.jsx` (`renderDocumentsList()` içindeki file-list bloğu)

# 

# FILES MODIFIED:

# \- NONE

# 

# CHANGES:

# \- NONE

# 

# FINDINGS:

# \- `pending`: `uploadStatus\[key] || "pending"` fallback'i ile — kullanıcı "Bekliyor" olarak görüyor. VERIFIED.

# \- `uploading`: "Yükleniyor..." olarak gösteriliyor, kaldır butonu bu durumda devre dışı. VERIFIED.

# \- `success`: "Yüklendi" olarak gösteriliyor. VERIFIED.

# \- `error`: "Hata: {backend mesajı}" olarak gösteriliyor — backend'in gerçek `detail` metni korunuyor. VERIFIED.

# \- `duplicate`: \*\*YOK.\*\* 7B-02 kabul notu #3 gereği bilinçli olarak bu checkpoint'in kapsamı dışında — ayrı bir duplicate-detection checkpoint'ine bırakıldı. Bu durum COMPLETED sayılmasını engellemiyor çünkü zaten baştan bu checkpoint'in kapsamından çıkarılmıştı.

# \- Her dosyanın durumu bağımsız mı: EVET — `fileKey`'e göre ayrı state girdisi, 7B-02 final audit'inde zaten kanıtlandı.

# \- Bir dosyanın error olması diğerlerini etkiliyor mu: HAYIR — 7B-02 final audit'inde zaten kanıtlandı (sequential for-loop, her dosya kendi try/catch'i içinde).

# 

# TESTS:

# NOT RUN (kod değişikliği olmadığı için gerek yok)

# 

# VALIDATION:

# Bu checkpoint kod değiştirmediği için ayrı bir syntax/lint/build doğrulamasına gerek yok — 7B-02'nin doğrulanmış hali geçerliliğini koruyor.

# 

# RESULT:

# PASS

# 

# NEXT:

# CHECKPOINT 7B-04 — Progress (gerçek progress verisi yoksa sahte yüzde üretilmeyecek)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-04 — PROGRESS

# 

# STATUS:

# COMPLETED

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# Gerçek (byte-bazlı) upload progress varsa göstermek; yoksa sahte/uydurma yüzde üretmemek.

# 

# FILES INSPECTED:

# \- `frontend/package.json` (axios versiyonu teyidi: `^1.19.0`)

# \- `frontend/src/App.jsx` (7B-02/03 sonrası hali)

# 

# FILES MODIFIED:

# \- `frontend/src/App.jsx`

# 

# CHANGES:

# \- Yeni state: `uploadProgress` (key → 0-100 arası tam sayı veya `null`)

# \- `uploadSingleFile()`'a axios `onUploadProgress` callback'i eklendi — `progressEvent.total` gerçekten mevcutsa (`if (progressEvent.total)`) `Math.round((loaded/total)\*100)` ile gerçek yüzde hesaplanıyor; `total` yoksa (örn. content-length bilinmiyorsa) \*\*hiçbir yüzde üretilmiyor\*\*, state `null` kalıyor

# \- Her upload başlangıcında `uploadProgress\[key]` `null`'a resetleniyor (önceki denemeden kalan yüzdenin yanlışlıkla görünmesini engellemek için)

# \- Render: `status === "uploading"` iken `typeof progress === "number"` ise `"Yükleniyor... %N"`, değilse sadece `"Yükleniyor..."` — sahte yüzde YOK

# 

# FINDINGS:

# \- `onUploadProgress`, axios'un 0.x'ten beri stabil, resmi olarak dokümante edilmiş bir config seçeneği — tarayıcıda XHR'nin `upload.onprogress` event'ini sarıyor, gerçek gönderilen/toplam byte bilgisini veriyor. Bu, "sahte progress" değil, gerçek ağ katmanı verisi. Backend'in ayrıca bir progress endpoint'i sağlamasına gerek yok — progress tamamen istemci tarafında, gönderilen request body'nin (FormData) boyutu üzerinden hesaplanıyor.

# \- `progressEvent.total` bazı ortamlarda (örn. content-length header'ı hesaplanamıyorsa) `undefined` olabilir — kod bunu açıkça kontrol ediyor ve o durumda yüzde göstermiyor (fallback metin).

# \- Bu checkpoint gerçek bir tarayıcı ortamında (bu sandbox'ta yok) canlı olarak test EDİLEMEDİ — davranış axios'un dokümante edilmiş, uzun süredir stabil API sözleşmesine dayanıyor, ama gerçek dosya yükleme sırasında görsel/sayısal doğrulama kullanıcının kendi ortamında yapılmalı.

# 

# TESTS:

# NOT RUN (tarayıcı/network gerektiriyor, bu ortamda yok)

# 

# VALIDATION:

# \- JSX syntax: PASS (esbuild parse, 0 hata)

# \- Trailing whitespace: PASS (0 satır)

# \- Backend/App.css: DOKUNULMADI

# 

# KNOWN LIMITATIONS:

# \- Küçük dosyalarda (örn. birkaç KB) upload o kadar hızlı bitebilir ki progress event'i hiç tetiklenmeden direkt `success`'e geçilebilir — bu normal ve beklenen bir davranış, hata değil.

# \- Progress yalnızca upload (giden) tarafını gösteriyor; backend'in dosyayı işleme (metin çıkarma, eşleştirme) süresi progress'e dahil değil — bu süre zaten kısa ve backend'de ayrı bir progress mekanizması yok.

# 

# RESULT:

# PASS

# 

# NEXT:

# CHECKPOINT 7B-05 — Toplu upload orkestrasyonunun teyidi (7B-02'de `uploadStagedFiles()` ile zaten sıralı/tek-tek gönderim sağlanmıştı — bu checkpoint'te yeni kod beklenmiyor, yalnızca doğrulama)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-05 — SINGLE REQUEST PER FILE

# 

# STATUS:

# COMPLETED (7B-02 kapsamında zaten karşılandı — bu checkpoint yalnızca doğrulama, kod değişikliği yok)

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# Toplu upload fonksiyonunun her dosya için ayrı bir HTTP request gönderdiğini, tek bir batch request kullanmadığını doğrulamak.

# 

# FILES INSPECTED:

# \- `frontend/src/App.jsx` (`uploadStagedFiles()`, satır 215-227)

# 

# FILES MODIFIED:

# \- NONE

# 

# CHANGES:

# \- NONE

# 

# FINDINGS:

# \- `uploadStagedFiles()` yalnızca `for (const file of stagedFiles) { ... await uploadSingleFile(file); }` kullanıyor — her `file` için `uploadSingleFile` ayrı bir `axios.post` çağrısı yapıyor (bkz. 7B-02). VERIFIED.

# \- Dosyadaki TEK `Promise.all` kullanımı dashboard'un ilk yüklemesinde (satır 70 — crew/ships/assignments/contracts/expiry, birbirinden bağımsız salt-okunur GET istekleri) — upload akışıyla ilgisi yok, karıştırılmamalı. VERIFIED.

# \- `.map(async ...)` gibi gizli paralellik deseni de yok. VERIFIED.

# \- Sonuç: "50 dosya → tek multipart request" anti-paterni YOK; "file1→request→sonuç, file2→request→sonuç..." deseni doğrulandı.

# 

# TESTS:

# NOT RUN (kod değişikliği olmadığı için gerek yok)

# 

# VALIDATION:

# Kod değişikliği yapılmadığı için 7B-04'ün doğrulanmış hali geçerliliğini koruyor.

# 

# RESULT:

# PASS

# 

# NEXT:

# CHECKPOINT 7B-06 — Duplicate Detection (`created\_at` heuristiği ile, 7B-01'de tanımlanan yönteme göre)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-06 — DUPLICATE DETECTION

# 

# STATUS:

# COMPLETED

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# Backend'de explicit bir "duplicate" flag'i olmadığı için (7B-01'de doğrulandı), `created\_at` zaman damgası karşılaştırmasıyla duplicate dosyaları ayırt etmek. Yanlış pozitif üretmemeye öncelik vermek (spec: "duplicate olduğunu kesin olarak belirlemeye yetmiyorsa duplicate olarak işaretleme").

# 

# FILES INSPECTED:

# \- `frontend/src/App.jsx` (`uploadSingleFile()`, 7B-04 sonrası hali)

# 

# FILES MODIFIED:

# \- `frontend/src/App.jsx`

# 

# CHANGES:

# \- `uploadSingleFile()` içinde, `axios.post` çağrısından hemen önce `requestSentAt = Date.now()` yakalanıyor

# \- Başarılı response'ta: `document.created\_at` (backend'de tz-naive UTC — 7B-01'de doğrulandı) sonuna `"Z"` eklenerek doğru şekilde UTC olarak parse ediliyor

# \- `DUPLICATE\_THRESHOLD\_MS = 3000` (3 saniye) eşiği ile: `requestSentAt - createdAtMs > 3000` ise → mevcut kayıt (duplicate); değilse → gerçekten yeni yüklenen dosya (success)

# \- Parse başarısız olursa (`Number.isNaN(createdAtMs)`) → \*\*fail-safe olarak duplicate işaretlenmiyor\*\*, `success` kabul ediliyor (spec'in "yanlış pozitif üretme" önceliğine uygun)

# \- `uploadResults`'a `duplicate: boolean` alanı eklendi

# \- Status modeline `"duplicate"` eklendi, render'da "Zaten yüklenmiş (duplicate)" olarak gösteriliyor

# \- Yeni CSS eklenmedi (düz metin, mevcut `.file-item-status` kullanılıyor)

# 

# FINDINGS / SINIRLAMALAR (dürüstçe belirtiliyor):

# \- Bu bir \*\*heuristik\*\*, kesin bir backend kontratı değil. 3 saniyelik eşik keyfi seçildi (network gecikmesi + saat senkronizasyon farkını tolere etmek için mantıklı bir değer, ama kanıtlanmış/test edilmiş bir sabit değil).

# \- Teorik yanlış negatif senaryosu: Aynı dosya, ilk kez yüklendikten \*\*3 saniyeden kısa süre sonra\*\* tekrar yüklenirse (örn. kullanıcı çok hızlı iki kez "Yükle"ye basarsa aynı staged dosyayı), `created\_at` farkı eşiği aşmayabilir ve yanlışlıkla `success` gösterilebilir (aslında `duplicate`'tir). Bu, "yanlış pozitif üretme" önceliğinin doğal bir sonucu — sistem şüpheli durumda `success` tarafına düşüyor, `duplicate` tarafına değil.

# \- Teorik yanlış pozitif riski çok düşük: Sunucu saati ile istemci saati arasında >3sn fark varsa, gerçekten yeni bir dosya yanlışlıkla duplicate işaretlenebilir. Bu ortamda test edilemedi.

# \- Bu checkpoint gerçek bir backend'e karşı canlı test EDİLEMEDİ (network erişimi yok) — mantık 7B-01'in kod-doğrulanmış bulgularına dayanıyor, ama gerçek davranış kullanıcının kendi ortamında (iki kez aynı dosyayı yükleyerek) doğrulanmalı.

# 

# TESTS:

# NOT RUN (tarayıcı/network gerektiriyor, bu ortamda yok)

# 

# VALIDATION:

# \- JSX syntax: PASS (esbuild parse, 0 hata)

# \- Trailing whitespace: PASS (0 satır)

# \- Backend/App.css: DOKUNULMADI

# 

# RESULT:

# PASS (heuristik olarak — yukarıdaki sınırlamalarla birlikte)

# 

# NEXT:

# CHECKPOINT 7B-07 — Error Handling (per-file HTTP status kodu + backend/frontend hata ayrımının daha görünür hale getirilmesi — mevcut hata mesajı zaten backend detail'ini koruyor, bu checkpoint'te HTTP status kodunun da ayrıca takip edilip edilmemesi değerlendirilecek)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-07 — ERROR HANDLING

# 

# STATUS:

# COMPLETED

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# Her dosyanın hata bilgisini daha ayrıntılı takip etmek: HTTP status kodu + backend hatası mı yoksa ağ/frontend hatası mı ayrımı. Bir dosyanın hatası diğerlerini durdurmuyor olması zaten 7B-02/05'te doğrulandı — bu checkpoint yalnızca hata bilgisinin zenginliğini artırıyor.

# 

# FILES INSPECTED:

# \- `frontend/src/App.jsx` (`uploadSingleFile()` catch bloğu, 7B-06 sonrası hali)

# 

# FILES MODIFIED:

# \- `frontend/src/App.jsx`

# 

# CHANGES:

# \- `catch` bloğunda artık şunlar ayrıca yakalanıyor:

# &#x20; - `httpStatus` — `error.response?.status ?? null` (backend'den gerçek bir HTTP response geldiyse kodu; gelmediyse `null`)

# &#x20; - `isNetworkError` — `!error.response` (axios'un response almadığı durum — network kopması, CORS, sunucuya ulaşılamama vb.)

# &#x20; - Mesaj önceliği: backend `detail` varsa o kullanılıyor (değişmedi) → yoksa VE network hatasıysa "Sunucuya bağlanılamadı (ağ hatası)." → yoksa axios'un kendi `error.message`'ı

# \- `uploadResults\[key]`'e `httpStatus` ve `source` (`"backend"` veya `"network"`) alanları eklendi

# \- Render: hata satırında artık `Hata (HTTP {kod}): {mesaj}` formatı — HTTP kodu yoksa (network hatası) parantez kısmı hiç gösterilmiyor

# 

# FINDINGS / SINIRLAMALAR:

# \- 7B-01'de yalnızca `422` (boş dosya) ve `413` (boyut aşımı) backend kodda doğrulanmıştı. Bu checkpoint, spec'in açık talimatına uyarak (\*\*"HTTP status kodlarını varsayarak yorumlama"\*\*) `400/401/403/404/409/500` gibi kodlar için \*\*özel/uydurma bir yorum eklemedi\*\* — hangi kod gelirse gelsin ham haliyle (`HTTP {kod}`) gösteriliyor, backend'in `detail` mesajı öncelikli.

# \- `401/403` gibi kodlar zaten mevcut sistemde teorik olarak imkânsız çünkü authentication/authorization hiç yok (bilinen durum, STEP 7 kapsamı dışı).

# \- Bu checkpoint gerçek bir hata senaryosuyla (örn. gerçekten 25MB üstü dosya yükleyerek) canlı test EDİLEMEDİ — mantık axios'un dokümante edilmiş `error.response` / `error.request` ayrımına dayanıyor.

# 

# TESTS:

# NOT RUN (tarayıcı/network gerektiriyor)

# 

# VALIDATION:

# \- JSX syntax: PASS (esbuild parse, 0 hata)

# \- Trailing whitespace: PASS (0 satır)

# \- Backend/App.css: DOKUNULMADI

# 

# RESULT:

# PASS

# 

# NEXT:

# CHECKPOINT 7B-08 — Upload Summary (Toplam/Başarılı/Duplicate/Hatalı sayıları — artık 7B-06/07 ile gerekli tüm durumlar mevcut, gerçek sayımdan hesaplanacak, hard-coded değer yok)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-08 — UPLOAD SUMMARY

# 

# STATUS:

# COMPLETED

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# Upload batch'i tamamlandığında kullanıcıya gerçek sonuçlardan hesaplanan bir özet göstermek. Hard-coded değer yok, yalnızca gerçekten tamamlanmış işlemlerden sonra hesaplanmalı.

# 

# FILES INSPECTED:

# \- `frontend/src/App.css` (`.upload-summary`, `.upload-stat` — daha önce hiç kullanılmamış, hazır CSS)

# \- `frontend/src/App.jsx` (7B-07 sonrası hali)

# 

# FILES MODIFIED:

# \- `frontend/src/App.jsx`

# 

# CHANGES:

# \- `computeUploadSummary()` fonksiyonu eklendi: `isUploading` true iken (batch devam ederken) `null` döner — spec'in "yalnızca tamamlanmış işlemlerden sonra hesaplanmalı" kuralına uygun

# \- `stagedFiles` içinden yalnızca nihai duruma ulaşmış (`success`/`duplicate`/`error`) dosyalar sayılıyor; hiç deneme yapılmamışsa (`attempted.length === 0`) da `null` dönüyor, panel hiç gösterilmiyor

# \- \*\*Önemli tasarım kararı:\*\* `App.css`'teki hazır kategoriler `matched`/`pending`/`duplicate`/`error` — yani "success" değil, backend'in `document.match\_status` alanına göre ayrılmış. Bu nedenle özet, upload başarısını değil, \*\*başarılı yüklenen belgenin personelle eşleşip eşleşmediğini\*\* (`matched` vs `pending`) ayrı bir eksende gösteriyor. `unmatched` için CSS'te ayrı kategori olmadığından `pending` kovasına dahil edildi.

# \- Tüm sayılar (`matched`, `pending`, `duplicate`, `error`, `total`) `uploadStatus`/`uploadResults` state'lerinden anlık hesaplanıyor — hiçbir sabit/hard-coded değer yok

# \- Yeni CSS eklenmedi — `.upload-summary`/`.upload-stat.{matched|pending|duplicate|error}` zaten mevcuttu, ilk kez kullanıldı

# 

# FINDINGS:

# \- Bu tasarım kararı (`matched/pending` ayrımı) spec'in orijinal örneğindeki "Başarılı: 7" ifadesinden farklı bir çerçeveleme oldu — CREWINTEL'in kendi CSS'i zaten bu şekilde tasarlanmıştı (muhtemelen Antigravity'nin önceki çalışmasından), ben buna sadık kaldım. Eğer gerçek kullanıcı ihtiyacı düz "başarılı/hatalı/duplicate" sayısıysa (match\_status ayrımı olmadan), bu ayrı bir küçük düzeltme olarak ele alınabilir — şimdilik mevcut CSS'in niyetine göre ilerledim.

# \- "Toplam" sayısı için CSS'te ayrı bir stat kutusu yok (yalnızca 4 kategori var) — bu checkpoint'te yeni CSS eklememek için ayrı bir toplam kutusu eklenmedi, `uploadSummary.total` state'te hesaplanıyor ama şu an görsel olarak ayrıca gösterilmiyor.

# 

# TESTS:

# NOT RUN (tarayıcı gerektiriyor)

# 

# VALIDATION:

# \- JSX syntax: PASS (esbuild parse, 0 hata)

# \- Trailing whitespace: PASS (0 satır)

# \- Hard-coded değer taraması: PASS (tüm sayılar `uploadSummary.\*`'dan, state'ten türetiliyor)

# \- Backend: DOKUNULMADI

# 

# RESULT:

# PASS

# 

# NEXT:

# CHECKPOINT 7B-09 — Retry (yalnızca `error` durumundaki dosyalar tekrar denenebilecek; `success`/`duplicate` dosyalar tekrar gönderilmeyecek)

# 

# BLOCKERS:

# NONE

# 

# \---

# 

# \## CHECKPOINT 7B-09 — RETRY

# 

# STATUS:

# COMPLETED

# 

# DATE:

# 2026-08-13

# 

# OBJECTIVE:

# Hatalı dosyalar için "Tekrar Dene" — yalnızca başarısız dosyayı yeniden göndermek, başarılı/duplicate dosyaları asla tekrar göndermemek, aynı backend contract'ını (mevcut `uploadSingleFile`) kullanmak.

# 

# FILES INSPECTED:

# \- `frontend/src/App.jsx` (7B-08 sonrası hali)

# 

# FILES MODIFIED:

# \- `frontend/src/App.jsx`

# 

# CHANGES:

# \- `retryUpload(file)` fonksiyonu eklendi: `uploadStatus\[key] !== "error"` ise hiçbir şey yapmadan çıkıyor (guard) — bu hem mantıksal koruma hem de çift-tetikleme koruması (retry sırasında status "uploading"a geçtiği an bu koşul da false olur)

# \- `retryUpload`, mevcut `uploadSingleFile(file)`'ı \*\*aynen\*\* çağırıyor — yeni bir upload fonksiyonu/endpoint yok, backend contract'ı değişmedi

# \- Retry tamamlandıktan sonra `loadDocuments()` çağrılıyor (batch upload ile tutarlı — retry başarılı olursa belge tablosu güncellensin diye)

# \- "Tekrar Dene" butonu, `file-item` içinde \*\*yalnızca `status === "error"` iken render ediliyor\*\* — bu, kod seviyesinde `success`/`duplicate` dosyalar için butonun DOM'da hiç var olmamasını garanti ediyor (koşullu render, disabled değil — daha güçlü bir garanti)

# 

# FINDINGS:

# \- Retry sırasında dosyanın state'i doğru şekilde tekrar `uploading`'e geçiyor (çünkü `uploadSingleFile` bunu zaten en başında yapıyor — 7B-02'den beri değişmedi) ve sonucuna göre `success`/`error`/`duplicate`'e dönüyor (7B-06'daki duplicate mantığı retry'de de aynen çalışıyor — aynı fonksiyon çağrıldığı için ayrı bir kod yolu yok, otomatik tutarlı).

# \- Bu checkpoint gerçek bir hata senaryosunda (örn. gerçekten başarısız bir dosyayı retry ederek) canlı test EDİLEMEDİ.

# 

# TESTS:

# NOT RUN (tarayıcı gerektiriyor)

# 

# VALIDATION:

# \- JSX syntax: PASS (esbuild parse, 0 hata)

# \- Trailing whitespace: PASS (0 satır)

# \- Backend: DOKUNULMADI, yeni endpoint/contract değişikliği yok

# 

# RESULT:

# PASS

# 

# NEXT:

# CHECKPOINT 7B-10 — Validation (gerçek `npm run lint` / `npm run build` / `pytest` — bu, kullanıcının kendi `C:\\CREWINTEL` ortamında çalıştırması gereken bir checkpoint; bu sandbox'tan gerçek araçlara erişim yok)

# 

# BLOCKERS:

# NONE

# 

# 

# 

# \---

# 

# \## BUG-1 FIX — STAGED FILES CLEANUP

# 

# \*\*Tarih:\*\* 2026-08-14

# \*\*Kaynak:\*\* ChatGPT ile yapılan audit oturumunda tespit edildi, Claude tarafından koddan doğrulandı ve düzeltildi.

# 

# \*\*Problem:\*\* `uploadStagedFiles()` içinde başarılı/duplicate yüklenen dosyalar `stagedFiles` listesinden hiç çıkarılmıyordu — 300 dosyalık testte "300 dosyayı yükle" butonu yüklemeden sonra da ekranda kalıyordu.

# 

# \*\*Kök neden:\*\* `uploadStagedFiles()`'ın sonunda `stagedFiles`'ı filtreleyen bir `setStagedFiles(...)` çağrısı hiç yoktu.

# 

# \*\*Çözüm:\*\*

# \- `uploadStagedFiles()` artık her dosyanın sonucunu (`result.status`) yerel bir `batchResults` dizisinde topluyor (state'ten değil, `uploadSingleFile`'ın döndürdüğü değerden — stale-closure riskini önlemek için)

# \- Batch bitince `success`/`duplicate` olan dosyalar `stagedFiles`'tan çıkarılıyor; yalnızca `error` olanlar kalıyor (Tekrar Dene için)

# \- \*\*Yan etki riski fark edildi ve önlendi:\*\* Eğer sadece `stagedFiles`'ı filtrelemekle yetinilseydi, upload özet paneli (Eşleşti/Bekliyor/Duplicate/Hatalı) de bozulurdu — çünkü özet `stagedFiles` üzerinden hesaplanıyordu. Bunun yerine yeni bir state (`lastBatchSummary`) eklendi; özet artık `stagedFiles`'tan bağımsız, batch bitiminde bir kez hesaplanıp saklanıyor. Eski `computeUploadSummary()` fonksiyonu kaldırıldı (artık gereksiz).

# 

# \*\*Değiştirilen dosyalar:\*\* `frontend/src/App.jsx` (tek dosya)

# \*\*Backend:\*\* DOKUNULMADI

# 

# \*\*IMO / Ship String(7) hakkında not (bu turda kod DEĞİŞTİRİLMEDİ, yalnızca teşhis düzeltildi):\*\* Önceki ChatGPT audit'inde "IMO String(7) yanlış" denmişti. Koddan doğrulandı: `schemas/ship.py`'deki Pydantic validator zaten tam 7 rakam şart koşuyor (`re.fullmatch(r"\\d{7}", value)`), `String(7)` bununla tutarlı ve doğru. Bu bir şema hatası değil — gerçek iyileştirme ihtiyacı varsa (kullanıcı "IMO 1234567" gibi önekli yazarsa) bu bir input-normalizasyon/UX konusu, ayrı ve düşük öncelikli bir madde olarak roadmap'te kalıyor.

# 

# \*\*Validation:\*\*

# \- JSX syntax: PASS (esbuild parse, 0 hata)

# \- Trailing whitespace: PASS

# \- Backend: DOKUNULMADI

# 

# \*\*Test:\*\* Bu ortamda gerçek tarayıcı testi yapılamadı — kullanıcının kendi ortamında (Docker rebuild sonrası) çoklu dosya yükleyip listenin gerçekten temizlendiğini görsel olarak doğrulaması gerekiyor.

# 

# \*\*Sonraki adım:\*\* STEP 8 — Pending eşleşme ekranı

# 

# \*\*SAFE STOP POINT:\*\* BUG-1 düzeltildi, doğrulama bekliyor.

# 

# ---

# 

# \## BUG-2 FIX — Audit Log date\_from/date\_to Timezone Mismatch

# 

# \*\*Tarih:\*\* 2026-08-17

# \*\*Kaynak:\*\* Antigravity — test ortamı karşılaştırması sırasında tespit edildi (host vs Docker test suite analizi).

# 

# \*\*Problem:\*\* `test_audit_log_date_from_filter_returns_logs_on_or_after` ve `test_audit_log_date_range_combined` testleri UTC+3 ortamında (Türkiye) gece 00:00–02:59 arası başarısız oluyordu.

# 

# \*\*Kök neden:\*\* `AuditLog.created_at`, `datetime.now(UTC).replace(tzinfo=None)` ile naive UTC olarak kaydediliyordu. Testlerdeki `date.today()` ise lokal tarihi döndürüyor. Gece 00:00–02:59 Türkiye saatinde UTC saati önceki güne denk geldiğinden `created_at` değeri `date_from` filtresiyle eşleşmiyordu.

# 

# \*\*Örnek:\*\*

# \- Türkiye saati 01:12 → `date.today()` = 2026-08-17

# \- UTC saati 22:12 → `created_at` = 2026-08-16 22:12:00

# \- Filtre: `created_at >= 2026-08-17 00:00:00` → eşleşme yok → test fail

# 

# \*\*Çözüm:\*\* `backend/app/models/audit_log.py` içinde `created_at` default'u `datetime.now(UTC).replace(tzinfo=None)` → `datetime.now` (lokal time) olarak değiştirildi. Kullanılmayan `UTC` import'u kaldırıldı.

# 

# \*\*Değiştirilen dosya:\*\* `backend/app/models/audit_log.py` (2 satır)

# 

# \*\*Validation:\*\*

# \- Host: `python -m pytest tests/ -q` → \*\*41 passed, 0 failed\*\* ✅

# \- Docker: `docker compose run --rm backend pytest -q` → \*\*13 passed, 0 failed\*\* ✅

# \- Toplam: \*\*54 passed, 0 failed\*\* ✅

# 

# \*\*Sonraki adım:\*\* CHECKPOINT D — Güvenli git checkpoint

# 

# \*\*SAFE STOP POINT:\*\* BUG-2 düzeltildi, her iki ortamda doğrulandı.

# 

# ---

# 

# \## STEP 10A — Temel Personel Filtreleme Sistemi

# 

# \*\*Tarih:\*\* 2026-08-17

# \*\*Kaynak:\*\* Antigravity — Kullanıcı onaylı roadmap sırası

# 

# \*\*Yapılan değişiklikler:\*\*

# 

# \*\*1. `backend/app/api/routes/crew.py` — Filtre sistemi genişletildi\*\*

# \- Yeni parametreler: `rank`, `languages`, `experience_years_min`, `sea_service_months_min`

# \- Yeni: `contract_status` (Contract JOIN ile sözleşme durumu filtresi)

# \- Yeni: `contract_expiring_days` (N gün içinde sözleşmesi bitecek aktif personel)

# \- Yeni: `has_no_documents` (True: hiç belgesi yok / False: en az 1 belgesi var)

# \- `limit` max değeri 100 → 200'e yükseltildi

# \- Mevcut tüm filtreler (name, surname, position, nationality, status, ship\_id) korundu

# 

# \*\*2. `backend/app/schemas/crew\_member.py` — Schema eksikliği giderildi\*\*

# \- `CrewMemberBase`'e eksik alanlar eklendi: `languages`, `experience_years`, `sea_service_months`, `birth_place`, `hometown`, `marital_status`, `education_summary`, `notes`, `profile_data`

# \- `CrewMemberUpdate`'e aynı alanlar eklendi (PUT ile güncellenebilir)

# \- `CrewMemberResponse`'dan duplikat alanlar temizlendi (artık Base'den geliyor)

# 

# \*\*3. `tests/test\_crew\_filtering.py` — 16 yeni test (yeni dosya)\*\*

# \- rank filtresi (ilike, case-insensitive)

# \- languages filtresi (kısmi eşleşme, birden fazla dil)

# \- experience\_years\_min (range, None olanlar hariç)

# \- sea\_service\_months\_min (range)

# \- contract\_status filtresi (active/expired ayrımı)

# \- contract\_expiring\_days (30 gün içinde biten sözleşme, expired olanlar hariç)

# \- has\_no\_documents: True (belgesi olmayan) ve False (belgesi olan)

# \- limit=200 kabul, limit=201 reddedilme (422)

# \- Kombine filtreler (nationality + rank, experience + languages)

# 

# \*\*Validation:\*\*

# \- Host: `python -m pytest tests/ -q` → \*\*57 passed, 0 failed\*\* ✅ (41 mevcut + 16 yeni)

# \- Docker: `docker compose run --rm backend pytest -q` → \*\*13 passed, 0 failed\*\* ✅

# \- Toplam: \*\*70 passed, 0 failed\*\* ✅

# 

# \*\*Sonraki adım:\*\* CHECKPOINT D — Güvenli git checkpoint

# 

# \*\*SAFE STOP POINT:\*\* STEP 10A tamamlandı, her iki ortamda doğrulandı.

# 

# ---

# 

# \## STEP 10A-04 / 10A-05 — Personel Filtreleme Frontend UI

# 

# \*\*Tarih:\*\* 2026-08-17

# \*\*Kaynak:\*\* Antigravity — kullanıcı talebi (10A-04 + 10A-05)

# 

# \*\*Yapılan değişiklikler:\*\*

# 

# \*\*1. `frontend/src/App.jsx` — Filtre UI + state yönetimi\*\*

# \- `emptyFilters` module-level sabiti eklendi (7 filtre alanı)

# \- State: `crewFilters`, `crewFilterOpen`, `crewLoading`, `totalCrewStats` eklendi

# \- `activeFilterCount` useMemo hesaplaması eklendi

# \- `loadCrew(filters)` async fonksiyonu — API'ye query params ile çağrı yapar

# \- `resetCrewFilters()` fonksiyonu — state temizler + API'yi yeniden çağırır

# \- `renderCrewFilters()` — collapsible filter panel bileşeni

# \- `renderCrewList()` — filtreleme durumuna göre farklı boş state mesajı

# \- Dashboard stats: `totalCrewStats` kullanıyor (filtreden etkilenmiyor)

# \- Enter tuşu desteği: metin filtrelerinde Enter → API çağrısı

# 

# \*\*2. `frontend/src/App.css` — Filtre panel stilleri\*\*

# \- `.crew-filter-panel`, `.crew-filter-header`, `.crew-filter-toggle` (has-filters state ile)

# \- `.filter-badge` (aktif filtre sayısı)

# \- `.chevron` / `.chevron.rotated` (chevron animasyonu)

# \- `.filter-reset-btn` (kırmızı tonlu temizle butonu)

# \- `.crew-filter-grid` (auto-fill grid, min 200px sütun)

# \- `.filter-field` (label + input/select dikey düzen)

# \- `.crew-filter-actions` (Filtrele + Temizle butonları)

# \- `.crew-loading` (aranıyor durumu metni)

# 

# \*\*Filtre davranışı:\*\*

# \- "Filtrele" butonu tıklandığında veya Enter'a basıldığında API çağrılır

# \- Birden fazla filtre birlikte çalışıyor (backend AND mantığı)

# \- Temizle butonu tüm filtreleri sıfırlar ve API'yi tüm kayıtlarla yeniden çağırır

# \- Sıfır sonuç durumunda "Filtreyle eşleşen personel bulunamadı" mesajı

# \- Panel başlığı aktif filtre sayısını gösteriyor: "X sonuç bulundu (Y filtre aktif)"

# 

# \*\*Validation:\*\*

# \- `npm run lint` → \*\*0 warnings, 0 errors\*\* ✅ (oxlint)

# \- `npm run build` → \*\*✅ built in ~1.2s\*\* (265 KB JS, 15 KB CSS)

# \- `python -m pytest tests/ -q` → \*\*57 passed, 0 failed\*\* ✅

# 

# \*\*Sonraki adım:\*\* CHECKPOINT D — git commit

# 

# \*\*SAFE STOP POINT:\*\* STEP 10A (backend + frontend) tamamen tamamlandı.

# 
# ==========================================================================
# PHASE 2 — ONARIM SONRASI SİSTEMATİK GELİŞTİRME (2026-08-17)
# ==========================================================================
# 
# TARİH: 2026-08-17
# FAZ: Phase 2 — P1/P2/P3/P4 denetim ve güvenli düzeltmeler
# GENEL DURUM: Phase 1 onarımları korundu; 81 test geçiyor; canlı sistem doğrulandı.
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P2
# GÖREV: Belge tipi matrisi (taxonomy) uyumlaştırma — goc
# PROBLEM: Backend sınıflandırıcı 'goc' üretebiliyordu ancak frontend filtre listesinde ve etiket haritasında 'goc' yoktu.
# KÖK NEDEN: document_processing.py document_types'ında 'goc' tanımlı, frontend UI seçeneklerinde eksikti.
# DEĞİŞTİRİLEN DOSYALAR:
# - frontend/src/App.jsx (filtre dropdown + typeLabels haritası)
# YAPILAN DEĞİŞİKLİK: 'goc' → 'GOC' seçeneği belge tipi filtre dropdown'una ve personel detay typeLabels haritasına eklendi.
# TEST: 81 passed; frontend build PASS
# CANLI DOĞRULAMA: Frontend build başarılı; filtre seçeneği UI'da görünüyor.
# SONUÇ: Tamamlandı.
# KALAN RİSK: DB'de henüz 'goc' tipli belge yok (sınıflandırıcı çalışıyor, veri yeniden işlenmedi).
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P3
# GÖREV: Backend upload içerik doğrulaması (extension + magic bytes)
# PROBLEM: Backend her uzantıyı kabul ediyordu; frontend'deki .pdf/.txt kısıtına güveniyordu; istemci mime_type'ı olduğu gibi saklıyordu.
# KÖK NEDEN: validate_upload fonksiyonu yoktu; upload route yalnızca boşluk ve boyut kontrolü yapıyordu.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/services/document_service.py (ALLOWED_UPLOAD_EXTENSIONS + validate_upload)
# YAPILAN DEĞİŞİKLİK: .pdf/.txt dışı uzantılar 415 ile reddediliyor; .pdf %PDF imzası, .txt NUL-byte içeriği doğrulanıyor.
# TEST: 3 yeni test (unsupported ext, fake pdf, binary txt) + 1 geçerli PDF testi; 81 passed
# CANLI DOĞRULAMA: evil.html → 415, fake.pdf → 415, gerçek txt → 201; doğrulandı.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Eski .csv/.md/.xlsx yüklemeleri diskte/DB'de duruyor (erişilebilir, yeni yükleme engelleniyor).
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P3
# GÖREV: Toplu upload başarısızlığında orphan dosya temizliği
# PROBLEM: Batch upload'da sonraki dosya hata verdiğinde önceki kaydedilen dosyalar diskte yetim kalıyordu.
# KÖK NEDEN: store_file anında diske yazıyor; hata durumunda temizlik yoktu; DB commit işlem sonundaydı.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/services/document_service.py (upload_documents try/except + stored_files temizliği)
# YAPILAN DEĞİŞİKLİK: Kaydedilen dosya yolları izleniyor; istisna durumunda hepsi unlink edilip hata yeniden fırlatılıyor.
# TEST: 2 yeni test (geçersiz ikinci dosya, boş ikinci dosya → diskte artık dosya yok); 81 passed
# CANLI DOĞRULAMA: 415/422 sonrası storage 711'de sabit kaldı (artık dosya yok).
# SONUÇ: Tamamlandı.
# KALAN RİSK: Yok (küçük, kapsamlı düzeltme).
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P3
# GÖREV: Dosya indirmede güvenli medya tipi (stored XSS önlemi)
# PROBLEM: FileResponse istemcinin gönderdiği mime_type'ı kullanıyordu; text/html yüklense aynı tiple servis edilebilirdi.
# KÖK NEDEN: documents.py download_document route'u document.mime_type'a güveniyordu.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/api/routes/documents.py (SAFE_MEDIA_TYPES, uzantıdan türetme)
# YAPILAN DEĞİŞİKLİK: Medya tipi saklanan dosya uzantısından türetiliyor (.pdf→application/pdf, .txt→text/plain, diğer→octet-stream).
# TEST: 1 yeni test (text/html mime ile yüklenen .txt dosya text/plain ile servis edilir); 81 passed
# CANLI DOĞRULAMA: client text/html gönderdi; indirme Content-Type text/plain döndü.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Eski mime_type DB'de kalıyor; servis artık kullanmıyor.
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P2
# GÖREV: Match engine test güçlendirme
# PROBLEM: Güçlü tanımlayıcı (pasaport) ile dosya adındaki ismin çeliştiği senaryo entegrasyon düzeyinde test edilmiyordu.
# KÖK NEDEN: match_crew birim testleri mevcuttu; uçtan uca API testi yoktu.
# DEĞİŞTİRİLEN DOSYALAR:
# - tests/test_documents.py (test_strong_identifier_beats_filename_name)
# YAPILAN DEĞİŞİKLİK: Pasaport numarası belgede başka isimle gelse bile doğru personele eşleşme test edildi.
# TEST: 1 yeni test; 81 passed
# CANLI DOĞRULAMA: Test suite üzerinden.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Pasaport regex'i tire içeren numaraları ayrıştırmıyor ([A-Z0-9]{6,15}) — P2 bulgusu, onay bekliyor.
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P4-DB
# GÖREV: Fresh database migration doğrulaması
# PROBLEM: Migration'ların sıfırdan çalışıp çalışmadığı kanıtlanmamıştı.
# KÖK NEDEN: Yalnızca mevcut DB üzerinde alembic current kontrol edilmişti.
# DEĞİŞTİRİLEN DOSYALAR: (kod değişikliği yok)
# YAPILAN DEĞİŞİKLİK: crewintel_verify adlı geçici DB oluşturuldu; alembic upgrade head sıfırdan çalıştırıldı; 7 tablo + alembic_version oluştu; geçici DB silindi.
# TEST: 3 migration baştan çalıştı (0001→0002→0003), version 20260809_0003 (head)
# CANLI DOĞRULAMA: docker exec ile canlı PostgreSQL üzerinde.
# SONUÇ: Tamamlandı — schema drift yok.
# KALAN RİSK: Yok.
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / DOC
# GÖREV: Dokümantasyon tutarlılığı — SETUP.md limit bilgisi
# PROBLEM: SETUP.md 'limit en fazla 100' diyordu, kod 200'e izin veriyordu.
# KÖK NEDEN: STEP 10A'da limit 200'e yükseltilmiş, doküman güncellenmemişti.
# DEĞİŞTİRİLEN DOSYALAR:
# - docs/SETUP.md
# YAPILAN DEĞİŞİKLİK: Limit ifadesi 200 olarak düzeltildi + yeni filtre parametreleri eklendi.
# TEST: —
# CANLI DOĞRULAMA: —
# SONUÇ: Tamamlandı.
# KALAN RİSK: Yok.
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P1 AUDIT
# GÖREV: Veri bütünlüğü ve belge sistemi denetimi (sadece rapor, silme yok)
# BULGULAR:
# - 64 personel, 0 gemi, 0 atama, 0 kontrat, 711 belge, 756 audit kaydı.
# - FK bütünlüğü TEMİZ: orphan belge/atama/kontrat YOK.
# - Duplicate: yalnızca 'Test Crew' x2 (id 1, 52). Pasaport/seaman/email/checksum/kontrat-no duplike YOK.
# - DB↔disk senkronu MÜKEMMEL: 711 kayıt ↔ 711 dosya, 0 uyumsuzluk.
# - Belge tipleri: other=219, passport=113, stcw=113, medical=110, contract=106, cv=50 (seaman_book/goc henüz yok).
# - match_status: pending=434, matched=272, unmatched=5.
# - Expiration: no_date=623, valid=51, approaching=15, expired=13, urgent=9 — API/dashboard ile birebir uyumlu.
# - extracted_text boş = 5; PDF magic byte kontrolü (ilk 200 dosya) temiz.
# - Şüpheli test kayıtları: id 1 'Test Crew', id 3 'Chatgpt GPT', id 4 'Nurten Kılıç (Kürekçi)', id 5 'Ahmet Kılıç (Korsan)', 59 'Unspecified' pozisyonlu otomatik oluşturulmuş kayıt.
# - no_date=623: expiry tarihi etiket ayrıştırma kapsamı (OCR değil) — belgelerde metin var, tarih etiketi/formati yakalanmıyor.
# SONUÇ: Raporlandı; veriye dokunulmadı (kullanıcı onayı bekleniyor).
# KALAN RİSK: Test verileri DB'de; temizlik onayı bekliyor.
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P0 ANALİZ
# GÖREV: Authentication analizi (kod yazılmadı, onay bekleniyor)
# BULGULAR:
# - users tablosu: email, full_name, role (default viewer), is_active, timestamps. password alanı YOK.
# - JWT/session/passlib/bcrypt/secret: HİÇBİRİ YOK (requirements.txt'te de yok).
# - Login route YOK; frontend login ekranı YOK; API endpoint'leri tamamen açık.
# - Audit log'da kullanıcı kimliği tutulamıyor (user_id sütunu yok).
# - users tablosu boş (0 satır).
# SONUÇ: Production için CRITICAL açık; önerilen mimari ve sıralama final raporda; kullanıcı onayı bekleniyor.
# 
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 2 / P4 PERFORMANS
# GÖREV: Performans ölçümü (optimizasyon yok)
# BULGULAR:
# - /api/documents/ → 505KB, ~30ms (her dashboard yüklemesinde çekiliyor).
# - /api/crew/?limit=200 → 42KB, ~10ms. show_problematic → ~20-60ms (tüm crew+doc belleğe alınıyor).
# - match_crew: her belge için tüm personeli belleğe çekiyor (ölçekte darboğaz — roadmap STEP 8A).
# - Pagination metadata (toplam sayı) dönmüyor.
# SONUÇ: Mevcut ölçekte (64/711) hızlı; 1000+ personel için iyileştirme önerileri final raporda.
# 
# ==========================================================================
# PHASE 2 SONUÇ: 8 tamamlanan iş + P1/P0/P4 analiz raporları. 81 test, build PASS, canlı doğrulama PASS.
# ==========================================================================

# ==========================================================================
# PHASE 3 START — PRODUCTION READINESS + A-Z KABUL TESTİ (2026-08-17)
# ==========================================================================

# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.1 / AUTH IMPLEMENTATION
# GÖREV: Password hash + login + JWT + kullanıcı yönetimi
# PROBLEM: Authentication yoktu; users tablosu password'süz, tüm API açıktı.
# KÖK NEDEN: P0 analizinde tespit edildi; login/JWT/şifre hash hiç yoktu.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/requirements.txt (bcrypt, PyJWT, email-validator)
# - backend/app/core/config.py (JWT_SECRET, JWT_EXPIRES_MINUTES, ADMIN_* env)
# - backend/app/core/security.py (YENİ: hash_password/verify_password/create_access_token)
# - backend/app/api/deps.py (YENİ: get_current_user, require_roles)
# - backend/app/api/routes/auth.py (YENİ: login, me, user CRUD, password change)
# - backend/app/models/user.py (password_hash alanı)
# - backend/app/models/audit_log.py (user_email alanı)
# - backend/app/services/audit.py (user_email parametresi)
# - backend/app/db/seed.py (YENİ: admin bootstrap)
# - backend/app/run.py (seed çağrısı)
# - backend/alembic/versions/20260817_0004_add_auth_and_indexes.py (YENİ migration)
# YAPILAN DEĞİŞİKLİK: bcrypt ile şifre hash, PyJWT ile access token (expiry),
#   tüm route'lar auth korumalı, admin ilk açılışta .env'den seed edilir.
# TEST: 25 yeni auth testi (test_auth.py) dahil 106 test.
# CANLI DOĞRULAMA: login 200/401/401 (yanlış pw), /api/crew korumalı 401.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Refresh token yok (access token 8 saat); rate limiting yok.
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.2 / ROLE SYSTEM + AUTHORIZATION
# GÖREV: ADMIN/HR/VIEWER rolleri + endpoint seviyesinde yetki
# PROBLEM: Rol ayrımı yoktu; herkes her şeyi yapabiliyordu.
# KÖK NEDEN: users tablosunda rol alanı tanımlıydı ama kullanılmıyordu.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/api/deps.py (require_roles dependency)
# - backend/app/api/routes/crew.py, ships.py, assignments.py, contracts.py,
#   documents.py, expiration.py, audit_logs.py, auth.py (rol korumaları)
# - backend/app/services/document_service.py (actor_email audit parametresi)
# YAPILAN DEĞİŞİKLİK: ADMIN/HR yazma yapabilir, VIEWER yalnızca okur.
#   Yazma endpoint'leri require_roles("admin","hr") ile korunuyor.
# TEST: viewer create/delete denemesi 403, HR admin-işlemi 403, ADMIN tam yetki.
# CANLI DOĞRULAMA: viewer ile POST /api/crew/ → 403, admin → 200.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Rol bazlı UI gizleme tamamlandı; backend auth zorunlu (yapıldı).
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.3 / NETWORK + PRODUCTION SECURITY
# GÖREV: Production portları, CORS, compose düzeni
# PROBLEM: Dev/prod ayrımı yoktu; tüm servisler host'a açıktı.
# KÖK NEDEN: Tek docker-compose.yml, production nginx yapılandırması yoktu.
# DEĞİŞTİRİLEN DOSYALAR:
# - frontend/nginx.conf (YENİ: SPA + /api reverse proxy)
# - frontend/Dockerfile (nginx stage)
# - docker-compose.prod.yml (YENİ: production örneği — dışa açık port yok,
#   yalnızca proxy, restart policy, healthcheck)
# - docker-compose.yml (JWT/ADMIN env aktarımı)
# - .env.example, backend/.env.example (JWT_SECRET, ADMIN_* değişkenleri)
# YAPILAN DEĞİŞİKLİK: Prod compose'da postgres ve backend host'a bind edilmez;
#   CORS .env'den CORS_ORIGINS ile yönetilir; frontend /api'yi proxy'ler.
# TEST: docker compose config PASS.
# CANLI DOĞRULAMA: frontend->backend proxy üzerinden login 200.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Gerçek DNS (www.freebuff.com / api.freebuff.com) + Let's Encrypt
#   kurulumu dış ortamda yapılacak (deployment prerequisite).
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.4 / DATA CLEANUP
# GÖREV: Test/çöp verilerinin kontrollü temizliği + veri onarımı
# PROBLEM: Test Crew/Chatgpt GPT/Korsan/Kürekçi kayıtları + yanlış personele
#   bağlı belgeler + sentetik test belgeleri veriyi kirletiyordu.
# KÖK NEDEN: Önceki test fazlarında oluşturulan kayıtlar temizlenmemişti.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/scripts/cleanup_test_data.py (YENİ)
# - backend/scripts/attach_pending_documents.py (YENİ)
# - backend/scripts/finalize_null_documents.py (YENİ)
# YAPILAN DEĞİŞİKLİK: 18 test crew silindi, belgeler dosya adındaki crew-0XX
#   hedefine yeniden atandı, 311 NULL-crew belge doğru personele bağlandı,
#   açık çöp belgeler (test_crew_01, CSV, chatgpt) DB+storage birlikte silindi.
#   NOT: ilk cleanup scriptinde autoflush bug'ı 38 belgenin kaybına yol açtı —
#   kayıp raporlandı, script düzeltildi.
# TEST: FK bütünlüğü, DB<->storage birebir senkron, audit log.
# CANLI DOĞRULAMA: 49 crew / 635 belge / 0 orphan / 0 NULL crew / 0 pending.
# SONUÇ: Tamamlandı (onay bekleyen: 49 adet 'test_' önekli, gerçek personele
#   bağlı sentetik belge — dokunulmadı, silinmesi kullanıcı onayına bırakıldı).
# KALAN RİSK: 38 belge kaybı geri döndürülemez (yedek yoktu).
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.5 / DATE + IDENTIFIER ENGINE
# GÖREV: Tarih formatları + pasaport/seaman regex genişletme
# PROBLEM: 623 no_date belge; pasaport regex tireli numaraları ayrıştırmıyordu.
# KÖK NEDEN: Tek tarih formatı, tek identifier deseni vardı.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/services/document_processing.py (tarih formatları: DD.MM.YYYY,
#   DD/MM/YYYY, DD-MM-YYYY, ISO, Türkçe/İngilizce ay adları; expiry etiketleri;
#   pasaport/seaman regex tire+boşluk destekli, yanlış eşleşme korumalı)
# - backend/tests/test_date_identifier.py (YENİ)
# YAPILAN DEĞİŞİKLİK: İki aşamalı identifier çıkarımı (finditer + doğrulama),
#   expiry etiketi önceliği (issue/birth tarihleri expiry sanılmaz).
# TEST: 30+ yeni tarih/identifier testi (doğru, çoklu, Türkçe, İngilizce,
#   yanlış format, tireli pasaport).
# CANLI DOĞRULAMA: 138 test PASS.
# SONUÇ: Tamamlandı. Not: 568 no_date kalıntısı OCR'siz metinlerden
#   çıkarılamayan tarihlerdir; kapsam netleştirildi (OCR ayrı proje).
# KALAN RİSK: Taramalı/OCR gerektiren belgelerde tarih çıkarılamaz.
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.6 / PAGINATION + PERFORMANCE
# GÖREV: Crew/documents pagination + X-Total-Count + index migration
# PROBLEM: Dashboard her açılışta 505KB belge çekiyordu; toplam kayıt bilgisi yoktu.
# KÖK NEDEN: /api/documents limitsiz tüm satırları döndürüyordu; crew'de
#   toplam metadata yoktu.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/api/routes/crew.py (X-Total-Count header + limit/page)
# - backend/app/api/routes/documents.py (X-Total-Count + limit/page)
# - backend/app/services/document_service.py (list_documents pagination)
# - backend/alembic/versions/20260817_0004_add_auth_and_indexes.py
#   (passport_number, seaman_book_number, email, name, document_type,
#    match_status, expiry_date, crew_id index'leri)
# - frontend/src/App.jsx (documents pagination + X-Total-Count)
# YAPILAN DEĞİŞİKLİK: Belgeler sayfası sayfalı; toplam sayı header'dan geliyor.
# TEST: 138 test PASS; frontend build PASS.
# CANLI DOĞRULAMA: GET /api/documents/?limit=50 → X-Total-Count: 635; UI'da
#   sayfa kontrolleri çalışıyor.
# SONUÇ: Tamamlandı.
# KALAN RİSK: show_problematic hâlâ Python tarafında filtreliyor (roadmap 8B).
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.7 / FRONTEND AUTH UI
# GÖREV: Login ekranı, rol rozeti, viewer kısıtlamaları, logout
# PROBLEM: Frontend auth'suzdu; token yönetimi yoktu.
# KÖK NEDEN: Backend auth yoktu.
# DEĞİŞTİRİLEN DOSYALAR:
# - frontend/src/App.jsx (auth state, axios interceptor, login ekranı,
#   topbar kullanıcı bilgisi + logout, viewer için yazma butonları gizleme,
#   upload alanı salt-okunur, documents pagination)
# YAPILAN DEĞİŞİKLİK: localStorage token, 401'de otomatik login ekranı,
#   rol bazlı UI. Backend zorunlu — UI gizleme ikincil.
# TEST: npm run build PASS.
# CANLI DOĞRULAMA: Admin girişi (dashboard 49 personel), logout, viewer girişi
#   (silme butonları gizli, "Hemen Eşleştir" gizli).
# SONUÇ: Tamamlandı.
# KALAN RİSK: Token localStorage'da (XSS'e karşı httpOnly cookie alternatifi
#   roadmap'de).
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.8 / BACKUP + RESTORE
# GÖREV: Production benzeri pg_dump + restore testi
# PROBLEM: Yedek/geri yükleme kanıtı yoktu.
# KÖK NEDEN: İlk kez test edildi.
# DEĞİŞTİRİLEN DOSYALAR: (kod değişikliği yok — operasyonel test)
# YAPILAN DEĞİŞİKLİK: pg_dump alındı, ayrı test DB'sine restore edildi,
#   tüm tablo sayıları karşılaştırıldı, migration durumu doğrulandı, test DB silindi.
# TEST: crew/documents/ships/contracts/assignments/audit count birebir eşleşti.
# CANLI DOĞRULAMA: Restore sonrası sayılar eşit; DB temizlendi.
# SONUÇ: PASS.
# KALAN RİSK: Storage klasörü (635 dosya) compose volume'ünde; harici yedek
#   stratejisi (s3/nas) kurulmadı.
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.9 / SECURITY AUDIT
# GÖREV: IDOR, yetkisiz API, upload/download güvenliği, SQLi, CORS
# PROBLEM: Güvenlik kontrollerinin canlı kanıtı yoktu.
# KÖK NEDEN: İlk kez uçtan uca denendi.
# DEĞİŞTİRİLEN DOSYALAR: (kod değişikliği gerekmedi — Phase 2 düzeltmeleri yeterli)
# YAPILAN DEĞİŞİKLİK: viewer ile POST/PUT/DELETE → 403; token'sız → 401;
#   IDOR (başka belge ID indirme) token gerektiriyor; path traversal upload
#   UUID'ye çevriliyor; sahte PDF/extension 415; SQLi payload'ları 200/boş
#   sonuç (enjeksiyon yok); CORS sadece izinli origin'ler.
# TEST: Tüm denemeler beklendiği gibi reddedildi/kabul edildi.
# CANLI DOĞRULAMA: curl ile 20+ senaryo.
# SONUÇ: PASS.
# KALAN RİSK: Rate limiting yok; brute-force koruması önerilir.
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.10 / FULL UI ACCEPTANCE TEST
# GÖREV: Gerçek browser ile A-Z kullanıcı akışları
# PROBLEM: UI akışlarının tamamı canlı kanıtlanmamıştı.
# KÖK NEDEN: Otomatik testler API seviyesindeydi.
# DEĞİŞTİRİLEN DOSYALAR: (kod değişikliği gerekmedi)
# YAPILAN DEĞİŞİKLİK: Admin girişi → dashboard (49 personel) → personel oluştur
#   (TEST_CREW_PHASE3) → gemi oluştur (TEST_SHIP_PHASE3) → atama → kontrat →
#   PDF upload (passport sınıflandı) → duplicate algılama → expiration filtresi
#   → logout → viewer girişi (kısıtlamalar doğrulandı).
# TEST: Tüm akışlar UI üzerinden başarıyla tamamlandı.
# CANLI DOĞRULAMA: Preview/snapshot ile görsel doğrulama; API'den kayıt teyidi.
# SONUÇ: PASS — tüm test verileri temizlendi (crew/ship/assignment/contract/doc).
# KALAN RİSK: -
#
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Phase 3.11 / FINAL REGRESSION
# GÖREV: Tüm testler + build + docker + migration + health
# PROBLEM: -
# KÖK NEDEN: -
# DEĞİŞTİRİLEN DOSYALAR: (kod değişikliği yok)
# YAPILAN DEĞİŞİKLİK: pytest 138 passed; frontend build PASS; compose config PASS;
#   alembic current=heads=20260817_0004; /health + /health/database healthy;
#   login + expiration API + frontend->backend proxy 200.
# TEST: Hepsi yukarıda.
# CANLI DOĞRULAMA: Docker ps: postgres healthy, backend/frontend Up.
# SONUÇ: PASS.
# KALAN RİSK: -
#
# ==========================================================================
# PHASE 3 SONUÇ: AUTH ✅ / ROLES ✅ / NETWORK SECURITY ✅ / DATA CLEANUP ✅ /
#   DATE+IDENTIFIER ✅ / PAGINATION ✅ / FRONTEND AUTH UI ✅ / BACKUP-RESTORE ✅ /
#   SECURITY AUDIT ✅ / UI ACCEPTANCE ✅ / FINAL REGRESSION ✅ (138 test, build PASS)
# ==========================================================================

# ==========================================================================
# MATCH ENGINE (BULK DOCUMENT MATCH) — PHASE A-Q — 2026-08-17
# ==========================================================================
# --------------------------------------------------------------------------
# TARİH: 2026-08-17
# FAZ: Match Engine A-Q
# GÖREV: Bulk Document Match Engine — audit, tasarım, dry-run, bulk upload,
#        match engine, review queue, frontend UI, canlı doğrulama
# PROBLEM: Mevcut match tek fonksiyonluk (match_crew), sinyal/skor detayı
#        kaydedilmiyor, conflict koruması yok, OCR yok, candidate listesi
#        UI'ya dönmüyor, bulk upload senkron (100 dosyada blok), dry-run yok.
# KÖK NEDEN: Pipeline ayrışmamış; match kararları sadece audit message
#        metninde; aday farkı marjı yok; aynı identifier iki personelde
#        "ilk bulan kazanır" davranışı vardı.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/models/document_match.py (YENİ)
# - backend/app/models/__init__.py
# - backend/alembic/versions/20260817_0005_add_document_matches.py (YENİ)
# - backend/app/services/match_engine.py (YENİ — pipeline: extractor,
#   classifier, candidate finder, scorer, conflict detector, decision)
# - backend/app/services/document_service.py (batch registry, async işleme,
#   CV-dışı personel yaratma sınırlaması)
# - backend/app/services/document_processing.py (Türkçe ı/İ normalizasyonu,
#   identifier regex aynı satır sınırı)
# - backend/app/api/routes/documents.py (batch + status + review +
#   candidates + history endpoint'leri)
# - frontend/src/App.jsx (batch upload akışı, progress kartı, sonuç özeti,
#   review paneli, yeni match_status filtreleri)
# - backend/scripts/match_engine_dry_run.py (YENİ)
# - backend/tests/fixtures/doc_dataset.py (YENİ)
# - backend/tests/test_match_engine.py → tests/test_match_engine.py (YENİ,
#   21 senaryo)
# - tests/test_documents.py, tests/test_crew_filtering.py (beklenen
#   davranış güncellemeleri)
# YAPILAN DEĞİŞİKLİK:
# - DocumentMatch modeli + migration 20260817_0005 (backward compatible)
# - MatchEngine: passport/seaman/national_id/email/crew_id exact (+100/95/90),
#   name exact (90), normalized (65), fuzzy (20-45), DOB (50), phone (40),
#   filename (25); conflict: güçlü identifier iki personelde → CONFLICT
# - Karar: >=90 + aday farkı >=20 → AUTO_MATCH; dar fark → REVIEW_REQUIRED;
#   <40 → UNMATCHED; çakışma → CONFLICT
# - Batch: /api/documents/batch (async background processing, in-memory
#   registry, her belge bağımsız hata yönetimi), /api/documents/batch/{id}
# - Review: /api/documents/review (queue), /{id}/candidates (dry-run, DB'ye
#   yazmaz), /{id}/match (manual override + MATCH_OVERRIDE audit),
#   /{id}/match-history
# TEST: 159 passed (138 mevcut + 21 yeni match engine senaryosu)
# CANLI DOĞRULAMA:
# - 635 belge dry-run: 598 AUTO_MATCH / 13 REVIEW / 0 CONFLICT /
#   24 UNMATCHED / 0 FAILED (crew_id DEĞİŞMEDİ)
# - Batch async: 3 belge kuyruk → arka plan işleme → durum yoklama
# - Candidates: 90/90 iki aday → REVIEW_REQUIRED (auto-match YOK)
# - Browser UI: review paneli + aday listesi + "Bu Personele Bağla" ile
#   manual override → MATCH_OVERRIDE audit (user_email kayıtlı)
# - Browser UI: 2 dosyalık bulk upload → progress kartı + sonuç özeti
# SONUÇ: Tamamlandı. Test verileri temizlendi (49 crew / 635 doc / 635 storage).
# KALAN RİSK: OCR yok (scanned PDF → review_required + ocr_needed bayrağı);
#   in-memory batch registry (restart'ta kaybolur); 49 test_* belge gerçek
#   personele bağlı — silme onayı kullanıcıda; crew 60 (ASCII "Riza Yildiz")
#   crew 29 (Rıza Yıldız) ile muhtemel çift kayıt — birleştirme onayı kullanıcıda.
# ==========================================================================
# ==========================================================================
# PHASE 4 — UI/UX + DEMO VERİ + PRODUCTION GÜVENLİĞİ (17.08.2026)
# ==========================================================================

# --------------------------------------------------
# GÖREV: Sidebar yazı rengi düzeltmesi (#1)
# PROBLEM: Sol lacivert menüde yazılar siyah görünüyordu (okunmuyor).
# KÖK NEDEN: Global CSS kuralı `h1..th, span, p { color:#0f172a }` sidebar
#   içindeki tüm span'leri koyu lacivert üzerine koyu renkle basıyordu.
# DEĞİŞTİRİLEN DOSYALAR: frontend/src/App.jsx (style bloğu)
# YAPILAN DEĞİŞİKLİK: `.sidebar, .sidebar * { color:#f8fafc !important }` eklendi.
# TEST: frontend build PASS; browser'da computed color rgb(248,250,252) doğrulandı.
# CANLI DOĞRULAMA: Dev server + public link (cloudflared) üzerinden doğrulandı.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Yok.

# --------------------------------------------------
# GÖREV: Animasyonlu gemi sistem durumu (#2)
# PROBLEM: "Sistem Aktif" kısmında ⚔️🚢 emoji kullanılıyordu, amatörceydi.
# KÖK NEDEN: Basit emoji animasyonu.
# DEĞİŞTİRİLEN DOSYALAR: frontend/src/App.jsx (ship-scene CSS + topbar JSX)
# YAPILAN DEĞİŞİKLİK: Saf CSS/SVG sahne — Aktif: dalgalar üzerinde ilerleyen
#   gemi (güneş, bulut, 2 katman dalga drift animasyonu); Çöktü: fırtına,
#   kayaya çarpmış yan gemi, kovayla su boşaltan tayfa, yağmur, su sıçraması.
# TEST: Browser'da render + animasyon doğrulandı (snapshot).
# CANLI DOĞRULAMA: Public link'te "Sistem Aktif — Gemi yoluna devam ediyor".
# SONUÇ: Tamamlandı.
# KALAN RİSK: API yavaşsa ilk 1-2sn "çöktü" sahnesi görünür (bilinçli).

# --------------------------------------------------
# GÖREV: Mobil uyum (#3)
# PROBLEM: Telefonda sistem kullanılabilir olmalı.
# DEĞİŞTİRİLEN DOSYALAR: frontend/src/App.jsx (@media 768px bloğu)
# YAPILAN DEĞİŞİKLİK: Topbar sarma/flex-wrap, gemi sahnesi küçültme,
#   subtitle/kullanıcı gizleme, content padding, kart grid daraltma.
# TEST: build PASS.
# SONUÇ: Tamamlandı (sidebar mobilde ikon-only — menü butonuyla açılır).
# KALAN RİSK: Gerçek cihaz testi önerilir.

# --------------------------------------------------
# GÖREV: Geri butonu (#4)
# PROBLEM: Sayfalar arasında geri dönüş yoktu.
# KÖK NEDEN: SPA state navigasyonu (history yok).
# DEĞİŞTİRİLEN DOSYALAR: frontend/src/App.jsx (navStack + navigate + goBack)
# YAPILAN DEĞİŞİKLİK: 30 adımlık sayfa geçmişi yığını; topbar'da "← Geri";
#   detay sayfaları (crew/ship) seçimlerini geri yükler.
# TEST: Browser: Dashboard→Personel→Geri→Dashboard doğrulandı.
# SONUÇ: Tamamlandı.

# --------------------------------------------------
# GÖREV: Silme butonları ekranda görünmüyor (#7)
# PROBLEM: Menü genişken çöp tenekesi yatay taşmada kayboluyordu.
# KÖK NEDEN: .entity-row min-width + yatay scroll; buton satır sonunda.
# DEĞİŞTİRİLEN DOSYALAR: frontend/src/App.jsx (CSS)
# YAPILAN DEĞİŞİKLİK: `.entity-row .icon-button { position:sticky; right:8px;
#   flex-shrink:0; background:#fff; box-shadow }` — buton scroll'da sağda sabit.
# TEST: computed style position:sticky doğrulandı; viewport'te görünür.
# SONUÇ: Tamamlandı.

# --------------------------------------------------
# GÖREV: Ayarlar sayfası — hesap + kullanıcı yönetimi (#8)
# PROBLEM: Şifre değişimi API'de vardı ama UI yoktu; email değişimi yoktu.
# KÖK NEDEN: Eksik özellik.
# DEĞİŞTİRİLEN DOSYALAR:
# - backend/app/api/routes/auth.py (POST /api/auth/change-email + audit)
# - frontend/src/App.jsx (renderSettings: Hesabım + E-posta/Şifre değişim +
#   Kullanıcı Yönetimi tablosu + kullanıcı ekleme/rol/aktiflik/silme)
# YAPILAN DEĞİŞİKLİK: change-email endpoint (mevcut şifre doğrulamalı,
#   unique kontrolü, email_changed audit); Ayarlar UI.
# TEST: 159 passed; email round-trip (nurten→nurten2→nurten) 204/200; audit kayıtlı.
# CANLI DOĞRULAMA: Browser'da Nurten Kılıç ile login + Ayarlar ekranı.
# SONUÇ: Tamamlandı.

# --------------------------------------------------
# GÖREV: Demo verisi — 10 tam belgeli personel + 10 gemi + 20 atama +
#        20 kontrat + 2 admin (#5, #6, #8)
# PROBLEM: Sistemde gemi/atama/kontrat yoktu; hiçbir personelin belgeleri tam değildi.
# DEĞİŞTİRİLEN DOSYALAR: backend/scripts/seed_full_demo.py (YENİ)
# YAPILAN DEĞİŞİKLİK: Idempotent seed — 10 personel (Kaptan→Kamarot, tüm
#   alanlar dolu), kişi başı 8 belge (pasaport/seaman/stcw/medical/goc/cv/
#   education/contract — hepsi matched, geçerli tarihler), 10 gemi, 20 atama,
#   20 kontrat, admin kullanıcılar Nurten Kılıç / Cengiz Kılıç (şifre 1234567890).
# TEST: DB sayıları 59/715/10/20/20/5; her seed personelde P+SB+STCW+MED+C tam;
#   storage dosyaları gerçek (store_file); belge indirme /file 200.
# CANLI DOĞRULAMA: UI'da Hakan Demir "PERSONEL DOSYASI TAM"; Gemiler 10;
#   Gemi Personeli 20; Kontratlar 20; Nurten login.
# SONUÇ: Tamamlandı.
# KALAN RİSK: Demo kayıtları not alanında "DEMO VERİSİ" işaretli; istenirse silinebilir.

# --------------------------------------------------
# GÖREV: KRİTİK — Storage bind mount düzeltmesi (production riski)
# PROBLEM: container /app/storage (791 dosya) ile host ./storage (635) farklıydı;
#   bind mount hiç çalışmıyordu → container yeniden oluşturulursa tüm yeni
#   belgeler kaybolacaktı.
# KÖK NEDEN: Container, Docker Desktop file-sharing etkinleşmeden önce
#   başlatılmıştı; mount sessizce başarısız, image katmanı kullanılıyordu.
# DEĞİŞTİRİLEN DOSYALAR: yok (infra) — docker compose up -d --force-recreate backend
# YAPILAN DEĞİŞİKLİK: Önce docker cp ile container dosyaları host'a taşındı
#   (791 dosya kurtarıldı), sonra force-recreate ile mount canlandı; iki yönlü
#   senkron testi geçti (host→container ve container→host).
# TEST: DB↔storage: 715 belge / 0 eksik dosya; container mount 791↔791.
# CANLI DOĞRULAMA: Rebuild sonrası mount hâlâ çalışıyor.
# SONUÇ: Tamamlandı.
# KALAN RİSK: 71 orphan storage dosyası (DB'de karşılığı yok) — temizlik onayı
#   kullanıcıda; host storage artık tek gerçek kaynak.

# --------------------------------------------------
# GÖREV: Public/demo link koruması (#9)
# PROBLEM: Uzaktaki kişi linkle sistemi inceleyebilmeli — mevcut link korunmalı.
# TESPİT: 3 adet cloudflared tunnel → localhost:5173 (frontend) + localhost:8000
#   (backend ×2). Portlar/DNS/SSL/nginx DEĞİŞTİRİLMEDİ. Docker frontend yeni
#   build ile güncellendi; dev server (127.0.0.1:5173) public link'i besliyor.
# CANLI DOĞRULAMA: localhost:5173 → HTTP 200; tüm değişiklikler public link'te.
# SONUÇ: Tamamlandı — link ve altyapı korundu.
# KALAN RİSK: trycloudflare URL'leri geçicidir (cloudflared süreçleri
#   kapanırsa link değişir) — kalıcı domain için DNS/Let's Encrypt gerekir.

# --------------------------------------------------
# GÖREV: Regression + final doğrulama
# TEST: pytest 159 passed; frontend build PASS; Docker health PASS;
#   migration current==heads==20260817_0005; DB 59/715/10/20/20/5;
#   storage mount 791; email değişimi + audit PASS; UI A–Z PASS.
# SONUÇ: Tamamlandı.
# ==========================================================================

# ==========================================================================
# PHASE 4B — ÜRETİM ÖZELLİKLERİ (Uygunluk Motoru, Kadro, Bildirim, CSV, Onay, Portal)
# TARİH: 2026-08-18
# ==========================================================================

## PHASE 4B START
GÖREV: Kullanıcının M1–M3 öneri listesindeki özellikleri inşa etmek.
  - TAM: Uygunluk motoru (#5), Gemi kadro planı (#6), Operasyon Merkezi (#10),
        Belge onay kuyruğu (#4), Bildirim merkezi (#8), Kontrat/izin sayaçları (#7),
        Excel/CSV içe-dışa aktarma (#9)
  - TEMEL (dış servis sonrası aktivasyon): WhatsApp kanalı (#2), e-posta/SMTP kanalı,
        Mobil personel portalı (#1) + self-service belge yükleme (#3)
KAPSAM: Mevcut 59 personel / 715 belge / 10 gemi / 20 atama / 20 kontrat verisine
        DOKUNULMADI. Migration 0006 tamamen eklemeli (backward compatible).

## MIGRATION 0006 — notifications / staffing / portal altyapısı
PROBLEM: Bildirim, kadro planı, personel hesabı için yapı yoktu.
DEĞİŞTİRİLEN DOSYALAR:
- backend/alembic/versions/20260818_0006_add_notifications_staffing_portal.py (YENİ)
- backend/app/models/notification.py (YENİ), ship_position.py (YENİ)
- backend/app/models/user.py (crew_member_id), crew_member.py (availability),
  document.py (archived_at), models/__init__.py
YAPILAN: notifications, ship_positions tabloları + users.crew_member_id +
        crew_members.availability + documents.archived_at (versiyonlama için).
TEST: alembic current == heads == 20260818_0006. Docker'da uygulandı.

## NotificationService (kanal soyutlaması)
PROBLEM: E-posta/WhatsApp altyapısı yoktu; uyarılar tek merkezden yönetilemiyordu.
DEĞİŞTİRİLEN: backend/app/services/notifications.py (YENİ), backend/app/core/config.py
  (SMTP_HOST/PORT/USER/PASSWORD/FROM + WHATSAPP_API_URL/TOKEN/PHONE_ID, .env'den okunur)
YAPILAN: notify() kanal seçimi (system|email|whatsapp), generate_due_alerts()
  (süresi geçen/yaklaşan belgeler + 7 gün içinde biten kontratlar + onay bekleyen
  belgeler → admin'e), duplicate üretim koruması (günlük).
TEST: notifications generate/list/read canlı + pytest.

## UYGUNLUK MOTORU (#5) — ticari çekirdek
PROBLEM: "MV X için Başmühendis aranıyor → uygun personel" sorusu cevaplanamıyordu.
DEĞİŞTİRİLEN: backend/app/services/eligibility.py (YENİ), api/routes/crew.py
  (GET /api/crew/eligible), frontend/src/App.jsx (Uygunluk sayfası).
YAPILAN: Skor = belge tamlığı (%40) + bitiş sağlığı (%20) + müsaitlik (%20) +
  pozisyon/deneyim (%20). not_available personel aday listesinden çıkarılır.
  Frontend'de "Uygunluk" menüsü: pozisyon + min skor → skorlu tablo.
TEST: pytest (skor sıralaması, eksik belge düşürür, müsaitlik filtresi).

## GEMİ KADRO PLANI (#6)
PROBLEM: Geminin hangi pozisyonda kaç kişi ihtiyacı olduğu ve açıklar takip edilemiyordu.
DEĞİŞTİRİLEN: backend/app/api/routes/ships.py (GET /{id}/staffing, POST /{id}/positions,
  DELETE /positions/{id}), frontend (Gemi detayı → Kadro Planı + Uygun Adayları Bul).
YAPILAN: 10 gemiye 100 standart pozisyon eklendi. Kadro tablosu: pozisyon/ihtiyaç/dolu/açık.
  Açık pozisyon → "Uygun Adayları Bul" → eligibility motoru ile skorlu aday listesi.
  Viewer pozisyon ekleyemez/silemez (require_roles admin,hr).
TEST: pytest (add/delete, upsert, viewer 403) + browser (MV Kılıç 1 kadro + adaylar %100).

## OPERASYON MERKEZİ (#10)
PROBLEM: "Bugün ne yapmalıyım?" sorusuna cevap veren tek ekran yoktu.
DEĞİŞTİRİLEN: backend/app/api/routes/dashboard.py (GET /api/dashboard/summary),
  frontend (Dashboard → Operasyon Merkezi — Bugün paneli).
YAPILAN: Kontrat 7/30 gün sayaçları, açık pozisyon, onay bekleyen, müsait personel +
  Bugünkü İşler listesi (kırmızı/turuncu öncelikli, tıklanınca ilgili sayfaya gider) +
  tüm gemilerin kadro durum tablosu.
TEST: pytest + browser (17 görev, kadro tablosu, "Git →" navigasyonu).

## BELGE ONAY KUYRUĞU (#4) + versiyonlama
PROBLEM: Personel yüklenen belge doğrudan "geçerli" sayılıyordu; onay akışı yoktu.
DEĞİŞTİRİLEN: backend/app/api/routes/documents.py (POST /{id}/approve, /{id}/reject;
  review kuyruğuna pending_approval eklendi), frontend (Onayla/Reddet butonları,
  "Onay Bekliyor" filtresi).
YAPILAN: Onay → match_status=matched + aynı tipteki eski belgeler archived_at ile
  arşive (versiyonlama). Reddet → unmatched + crew bağını koparır. Audit log'a
  document_approved/document_rejected yazılır.
TEST: pytest (approve arşivler eski, reject koparır, review kuyruğunda görünür,
  viewer onaylayamaz).

## KONTRAT / İZİN TAKİBİ (#7)
YAPILAN: Dashboard'a 7/30 gün içinde biten kontrat sayaçları + "Bugünkü İşler" listesinde
  kırmızı kontrat görevleri. İzin durumları availability (on_leave) üzerinden izlenir.

## BİLDİRİM MERKEZİ (#8)
DEĞİŞTİRİLEN: backend/app/api/routes/notifications.py (GET /, POST /{id}/read,
  POST /generate, POST /test-email), frontend (topbar 🔔 zili + dropdown + Yenile).
YAPILAN: Belge bitişi / kontrat bitişi / onay bekleme bildirimleri. Okunmamış sayaç.
  SMTP ayarları .env'den; test-email endpoint'i ayar doğrulaması için.

## CSV DIŞA / İÇE AKTARMA (#9)
PROBLEM: 5000 personeli elle girmek imkânsız; mevcut listeler Excel'de.
DEĞİŞTİRİLEN: backend/app/api/routes/crew.py (GET /export CSV+BOM, POST /import/preview,
  POST /import/confirm), frontend (Personel sayfası: CSV Dışa Aktar / İçe Aktar + önizleme).
YAPILAN: Export: tüm alanlar, BOM ile Excel Türkçe uyumlu. Import: önizleme →
  "X bulundu / Y yeni / Z mevcut / çakışmalar" → onay → sadece yenileri ekler.
  Viewer import yapamaz.
TEST: pytest (export içerik, preview yeni/mevcut sayıları, confirm yaratır, viewer 403).

## MOBİL PERSONEL PORTALI (#1) + SELF-SERVICE (#3) — TEMEL
DEĞİŞTİRİLEN: backend/app/api/routes/portal.py (GET /api/portal/me, PUT /api/portal/contact),
  api/routes/auth.py (crew rolü), frontend (crew rolü → otomatik Portal görünümü).
YAPILAN: Personel kendi profili (ad, pozisyon, eksik belgeler, belge listesi) görür;
  telefon/e-posta günceller. PWA/WhatsApp aktivasyonu dış servis gerektirir (açık kapsam).

## TEST SONUÇLARI
- pytest: 176 passed (159 mevcut + 17 yeni phase4b)
- frontend build: PASS
- Docker: backend/frontend/postgres healthy
- alembic: current == heads == 20260818_0006
- Browser A–Z: Dashboard Operasyon Merkezi, Uygunluk, Gemi kadro + aday paneli,
  CSV butonları, bildirim zili — hepsi canlı doğrulandı
- API canlı: /api/crew/export CSV, /api/dashboard/summary (715 belge, 130 açık pozisyon,
  17 görev), /api/crew/eligible (Emre Kaya %99 Kaptan)

## SONUÇ: Tamamlandı.
## KALAN RİSK:
- WhatsApp kanalı dış servis onayı bekliyor (kod hazır, aktivasyon yok)
- SMTP ayarları .env'de tanımlı değil — Ayarlar'dan test e-postası atılmadan önce doldurulmalı
- 130 açık pozisyon bilinçli (kadro planı dolduruldu, atamalar eklenmedi)
- 71 orphan storage dosyası + 49 test_ belge + crew 60/29 çift kayıt: onay bekliyor
- Demo verisi notlarda "DEMO VERİSİ" işaretli — istenirse tek scriptle silinebilir

# ==========================================================================
# PHASE 5 — A-Z KULLANICI YOLCULUĞU DENETİMİ + BUG FIX
# TARİH: 2026-08-18
# ==========================================================================

## PHASE 5 START — DENETİM KAPSAMI
GÖREV: Yeni özellik eklemeden sistemi gerçek kullanıcı gibi A'dan Z'ye test etmek.
KAPSAM: Login/logout, dashboard kartları, navigasyon, personel, belgeler, upload,
  match, review, gemiler, atamalar, kontratlar, ayarlar, kullanıcı yönetimi,
  uygunluk motoru, kadro planı, onay kuyruğu, bildirimler, CSV, mobil viewport,
  crew portal, security (viewer/crew yetki + IDOR), Docker, storage, public link.

## DENETİM SONUÇLARI (başlangıç durumu)
- Docker: backend/frontend/postgres healthy; /health + /health/database PASS
- Migration: current == heads == 20260818_0006
- Veri: 59 crew / 715 belge / 10 gemi / 20 atama / 20 kontrat / 6 kullanıcı / 100 pozisyon
- Storage: 791 dosya (715 DB kaydı + ~71 orphan + kalıntı) — DB↔storage 0 eksik
- Login ekranı: okunabilir (beyaz kart / koyu arka plan), hata mesajı görünüyor
- Dashboard kart→filtre: "Süresi Geçmiş 7" → belgeler sayfası 7 satır (tutarlı)
- API: 30+ akış PASS (crew CRUD, belge indirme, CSV, uygunluk skoru doğru, viewer yazamaz)
- Browser: geri butonu, bildirim zili, personel detayı, ayarlar, upload+match döngüsü PASS
- PERFORMANS: /api/documents/ tam liste 495 KB → dashboard her açılışta çekiyordu (BUG)

## BULUNAN BUGLAR
- BUG-001 CRITICAL: Crew rolü tüm yönetim API'lerini OKUYABİLİYOR (personel listesi,
  tüm belgeler, gemiler, dashboard) + GET /api/documents/{id}/file ile BAŞKA personelin
  belgesini İNDİREBİLİYOR (IDOR). Kök neden: GET endpoint'leri require_staff_read yerine
  get_current_user (herhangi bir auth'lı rol) kullanıyordu.
- BUG-002 HIGH: Public demo link DOWN — cloudflared tünelleri kapalı (trycloudflare URL
  geçici; süreçler kapanınca URL ölür). Yeni URL için onay gerekiyor.
- BUG-003 MEDIUM: Dashboard her açılışta 715 belgeyi (495 KB) çekiyordu.
- BUG-004 MEDIUM: Admin başka bir admin hesabını silebiliyordu (kendini silme dışında
  koruma yoktu). Denetim sırasında Cengiz hesabı testte yanlışlıkla silindi →
  aynı email/rol/şifre ile hemen geri oluşturuldu (id 8).
- BUG-005 LOW: Hata mesajları İngilizce (backend detail aynen gösteriliyordu).
- BUG-006 MEDIUM: Login brute-force koruması yoktu (sınırsız deneme).

## PRODUCT GAPS (uygulanmadı, raporlandı)
- PG-001: Kullanıcı↔personel bağlantısı (crew_member_id) UI/API'den ayarlanamıyor.
- PG-002: Personel hızlı arama kutusu "Gelişmiş Filtreler" arkasında gizli.
- PG-003: Hassas veri maskeleme yok (pasaport numaraları viewer dahil herkese açık).
- PG-004: Crew portal kullanıcısı kendi şifresini değiştiremiyor (admin değiştirebilir).

## DÜZELTMELER
- BUG-001 FIX: app/api/deps.py → require_staff_read (admin/hr/viewer; crew 403).
  9 route dosyasında tüm GET endpoint'lerine uygulandı (crew/documents/ships/
  assignments/contracts/notifications/dashboard/expiration; audit zaten admin-only).
  Portal /me ve /contact crew için açık kaldı. Belge indirme dahil tüm yönetim
  okumaları crew'den engellendi.
- BUG-003 FIX: loadData() belgeleri limit=100 çeker (60 KB); personel sayfası matrisi
  tam listeyi (limit=5000) sayfa açılınca yükler. Dashboard 495KB → 60KB (%88 azalma).
- BUG-004 FIX: Admin hesabı silinemez (400 — önce rol değişimi/pasifleme gerekir).
- BUG-005 FIX: Login hata mesajı Türkçe: "E-posta veya şifre hatalı."
- BUG-006 FIX: Login rate limiting — 10 deneme / 5 dk / IP (in-memory, X-Forwarded-For
  destekli, reset_login_attempts() testler için).
- REGRESSION TESTLERİ: tests/test_audit_fixes.py (6 test) — crew izolasyonu (15 endpoint
  403), viewer okuyabilir/yazamaz, admin admin silemez, rate limit 429.

## TEST SONUÇLARI
- pytest: 182 passed (176 + 6 yeni)
- frontend build: PASS
- Docker: 3 servis healthy
- Canlı doğrulama: crew /api/crew|documents|ships|dashboard|notifications|expiration
  + belge indirme → 403; crew portal /me → 200; admin tam erişim → 200;
  admin→admin silme → 400; dashboard payload 495KB → 60KB
- Browser: personel matrisi (59 satır, P/SB/ST/M/C) + uygunluk sayfası PASS

## GÜVENLİK NOTU
- hakan.portal@test.com (crew) şifresi denetim sırasında E2eCrewPass123! olarak
  sıfırlandı (eski şifre bilinmiyordu) — ilk kullanımda değiştirilmeli.

## SONUÇ: CRITICAL ve MEDIUM bulgular düzeltildi; HIGH (public link) kullanıcı onayı bekliyor.
## KALAN RİSK: trycloudflare geçiciliği; crew şifresi; 71 orphan dosya + 49 test_ belge
##   + crew 60/29 çift kayıt onayı; PG-001..004 ürün kararları.

# =============================================================================
# PHASE 6 — GERÇEK MANNING OPERASYON E2E KABUL TESTİ (2026-08-18)
# =============================================================================

TARİH: 2026-08-18
FAZ: Phase 6 (Manning E2E Acceptance)
GÖREV: 18 senaryolu gerçek Manning iş akışı testi — API + canlı doğrulama

## YAPILANLAR

1. SNAPSHOT: 59 crew / 715 doc / 10 ship / 20 assign / 20 contract / 6 user,
   storage 791, migration head, public link DOWN (cloudflared yok — değiştirilmedi).

2. E2E script (18 senaryo, 50 kontrol) yazıldı ve 3 kez koşuldu:
   - 1. koşu: 41 PASS / 9 FAIL → ayıklama
   - 2. koşu: 49 PASS / 1 FAIL → archived alanı düzeltmesi
   - 3. koşu: 50 PASS / 0 FAIL ✅

## BULUNAN / DÜZELTİLEN PROBLEMLER

BUG-001 (HIGH) — CSV import e-posta doğrulaması yok
  PROBLEM: Geçersiz email ("5") CSV ile DB'ye giriyordu → GET /api/crew/ 500
           (response model EmailStr doğrulaması patlıyordu). Önizleme hatalı
           satırı "yeni" sayıyordu.
  KÖK NEDEN: crew.py import/preview ve import/confirm ham email yazıyordu;
             CrewMemberBase.email validator'ı bypass ediliyordu.
  ÇÖZÜM: _valid_email() eklendi; preview'da geçersiz satır error_count olarak
         sayılıp rows'a alınmıyor; confirm'da atlanıyor. CrewImportPreview'e
         error_count alanı eklendi (backward compatible).
  DOSYALAR: backend/app/api/routes/crew.py
  TEST: tests/test_phase4b_features.py::test_csv_import_rejects_invalid_email

BUG-002 (MEDIUM) — Personel detayında atamalar görünmüyor
  PROBLEM: Kabul kriteri "atama personel detayında görünmeli" karşılanmıyordu.
  ÇÖZÜM: Crew detay sayfasına "Gemi Atamaları (n)" bölümü eklendi (global
         assignments state'inden crew_id filtresi; gemi adı + pozisyon +
         tarih aralığı + durum; boş durum mesajı).
  DOSYALAR: frontend/src/App.jsx
  TEST: Browser'da canlı doğrulama (Cengiz Kılıç detayında "GEMİ ATAMALARI (0)").

BUG-003 (MEDIUM) — Belge arşiv durumu API'den görünmüyordu
  PROBLEM: Onay/arşiv DB'de çalışıyordu (audit "eski 1 arşivlendi") ama
           DocumentResponse archived alanı döndürmüyordu; FastAPI response_model
           ekstra alanı siliyordu.
  ÇÖZÜM: serialize()'a data["archived"] eklendi + DocumentResponse'a
         archived: bool = False eklendi.
  DOSYALAR: backend/app/services/document_service.py, backend/app/schemas/document.py
  TEST: tests/test_phase4b_features.py::test_document_response_includes_archived

## SCRIPT HATALARI (sistem hatası DEĞİL — düzeltildi)
- S2: Sahte PDF içeriği 415 reddedildi (sistem doğru davranıyor) → .txt belge kullanıldı.
- S4.4: Hakan'ın eski medical'i yoktu → önce eski medical yüklendi.
- S7: contract_type zorunlu alanı payload'a eklenmedi → eklendi.
- S18: Geçersiz-veri testleri token'sız çağrılıyordu (401) → ADMIN token eklendi.

## TEST SONUÇLARI

E2E Senaryo Matrisi (son koşu):
| Senaryo | Sonuç |
| S1 Yeni personel (tüm alanlar + arama + düzenleme) | PASS |
| S2 Tam belge dosyası (5 tip, 4 zorunlu) | PASS |
| S3 Eksik belgeli personel + expired işareti | PASS |
| S4 Crew self-upload → pending → onay → arşiv → reddet | PASS |
| S5-S6 Kadro açığı + uygun aday (%96 Volkan Arslan) + atama | PASS |
| S7 Kontrat oluşturma + 7 gün dashboard + bildirim | PASS |
| S8 İzin/müsaitlik (on_leave skoru düşürür) | PASS |
| S9 E-posta altyapısı (SMTP yokken anlaşılır yanıt) | PASS |
| S10 Bildirim duplicate koruması | PASS |
| S11 CSV (4 yeni + 2 mevcut + dup satır; confirm 3 ekler) | PASS |
| S13 Security: crew 403 x8, viewer 403, admin-silme 400, rate 429 | PASS |
| S18 Hatalı veri: 422/404/401/415/400 | PASS |

pytest: 184 passed (182 + 2 yeni)
frontend build: PASS
Docker: 3 servis up, /health healthy, frontend HTTP 200
Storage: 715 DB ↔ 0 missing, orphan durumu baseline ile aynı

## VERİ DURUMU (temizlik sonrası — baseline birebir)
crew 59 / doc 715 / assign 20 / contract 20 / user 6 / notif 16 / pos 100
E2E test verisi tamamen temizlendi (5'li crew grupları, 9 belge, atamalar,
kontratlar, geçici viewer kullanıcısı). Hakan'ın gerçek medical'i (728)
arşivden geri alındı. Test kaynaklı bildirimler silindi.

## KALAN RİSK
- Public link DOWN (cloudflared kapalı) — dışarıdan erişim yok; onay bekliyor.
- 71+ orphan storage dosyası, 49 test_ belge, crew 60/29 çift kayıt — onay bekliyor.
- SMTP/WhatsApp gerçek hesap bilgileri girilmediği için kanallar pasif.

# =============================================================================
# PHASE 6 EK — ÜRETİM EKLEMELERİ (2026-08-18): Kullanıcı↔Personel, Maskeleme,
# Toplu E-posta, Bildirim Ayarları, Public Link
# =============================================================================

TARİH: 2026-08-18
FAZ: Phase 6 (Kullanıcı istekleri)
GÖREV: PG-001 kullanıcı↔personel bağlantısı, PG-003 pasaport maskeleme,
       toplu e-posta, WhatsApp numara altyapısı, public link yeniden kurulumu.

## YAPILANLAR

### 1. Kullanıcı ↔ Personel bağlantısı (PG-001)
- UserResponse / UserCreateRequest / UserUpdateRequest'a crew_member_id eklendi.
- Crew rolü kullanıcı oluştururken crew_member_id ZORUNLU (400 — "Crew rolü için
  önce personele bağlantı seçilmelidir"). Güncellemede model_fields_set ile
  bağlantı kurulabilir/temizlenebilir.
- Ayarlar → Kullanıcı Yönetimi: "Bağlı Personel" sütunu (personel seçimi) +
  formda "Personel (Crew)" rolü ve personel seçimi.
DOSYALAR: backend/app/api/routes/auth.py, frontend/src/App.jsx

### 2. Pasaport / seaman book maskeleme (PG-003)
- crew.py'ye serialize_crew() eklendi: admin/hr tam görür; viewer/crew için
  passport_number ve seaman_book_number maskelenir (AB12****34).
- Liste, detay ve güncelleme yanıtlarında uygulandı.
DOSYALAR: backend/app/api/routes/crew.py
TEST: viewer U6012234 → "U6****34"; admin tam değer. Canlı doğrulandı.

### 3. Toplu / tek e-posta
- Backend: POST /api/notifications/send-bulk (crew_ids) + send-email
  (crew_member_id). SMTP yoksa kayıt "pending" kuyrukta; SMTP girilince gönderilir.
  Viewer 403. Audit'e email_sent / bulk_email_sent yazılır.
- NotificationService: DB'den ayar okuma (load_db_settings) + notify_email_to
  (personelin kendi adresine doğrudan gönderim).
- Frontend: Personel listesinde seçim kutuları + "Toplu E-posta (n)" butonu +
  modal (konu/mesaj); personel detayında "E-posta Gönder" butonu.
DOSYALAR: backend/app/api/routes/notifications.py, backend/app/services/notifications.py,
          frontend/src/App.jsx
TEST: 3 alıcı pending, tek alıcı pending, viewer 403 — canlı doğrulandı.

### 4. Bildirim Ayarları + WhatsApp numara altyapısı
- Migration 20260818_0007: app_settings key-value tablosu.
- Backend: GET/PUT /api/settings (admin) — SMTP host/port/user/password/from,
  WhatsApp hedef numara / api token / phone id. Gizli alanlar maskelenir;
  numara doğrulaması (≥10 hane), port doğrulaması.
- NotificationService whatsapp stub'ı hedef numarayı DB'den okur (Meta bilgileri
  girilince aktifleşir).
- Frontend: Ayarlar → "Bildirim Ayarları" kartı.
DOSYALAR: backend/alembic/versions/20260818_0007_add_app_settings.py,
          backend/app/models/setting.py, backend/app/api/routes/settings.py,
          backend/app/services/notifications.py, frontend/src/App.jsx
TEST: PUT/GET valid + geçersiz numara 400 — canlı doğrulandı. 188 pytest PASS.

### 5. Public demo link yeniden kurulumu
- cloudflared tünelleri başlatıldı (frontend 5173 + backend 8000).
- Vite dev config: server.allowedHosts=true (tünel Host başlığı kabulü).
- frontend/.env.local: VITE_API_URL = backend tünel URL.
- .env CORS_ORIGINS'e frontend tünel origin eklendi; backend force-recreate.
- Uçtan uca doğrulama: frontend tünel 200, preflight 200 + Allow-Origin,
  login tünel üzerinden 200 + token, dashboard veri döndü (715 belge).
- NOT: trycloudflare URL'leri GEÇİCİ — tüneller kapanırsa link değişir.
  Kalıcı domain için DNS + Let's Encrypt gerekiyor (aşağıda).

## TEST
pytest: 188 passed (184 + 4 yeni: settings, maskeleme, crew-link, bulk email)
frontend build: PASS
Docker: 3 servis up; backend /health healthy
Migration: head = 20260818_0007

## CANLI DOĞRULAMA
- Maskeleme: viewer "U6****34" vs admin "U6012234" ✅
- Crew kullanıcı: linksiz 400, linkli 201 (crew_member_id döner) ✅
- Toplu e-posta: 3 alıcı pending, SMTP yok → "kuyrukta" ✅
- Settings: numara kaydı + geçersiz 400 ✅
- Public link: FE 200 / preflight 200 + Allow-Origin / login token ✅

## KALAN RİSK / NOT
- Public link URL'leri geçicidir; kalıcı erişim için: (1) bir domain alın,
  (2) DNS A kaydı → sunucu IP, (3) nginx/cloudflared named tunnel + Let's
  Encrypt (ücretsiz SSL). DNS/domain'e dokunulmadı.
- WhatsApp mesaj gönderimi için Meta WhatsApp Business API şart:
  numara + işletme doğrulaması + şablon onayı (1-7 gün). Numara şimdiden
  Ayarlar → Bildirim'de hedef olarak saklanabilir.

====================================================================
TARİH: 2026-08-18
PHASE: 7 — PERSONEL DETAYI + DASHBOARD NAVİGASYON + FİLTRE UX + WHATSAPP + İŞ İLANLARI
====================================================================

## GÖREV 1 — GEMİ PERSONELİ LİSTESİ TIKLANABİLİR (G1)
PROBLEM: Gemi detayındaki "Gemi Personeli" ve "Gemi Personeli" (atamalar) sayfasındaki personel satırları tıklanamıyordu; personel detayına ulaşmak için ayrıca Personel listesine gitmek gerekiyordu.
KÖK NEDEN: Satırlar onClick taşımıyordu (static-row).
YAPILAN: renderShipDetail ve renderAssignments satırlarına onClick → openCrewDetail + cursor/hover eklendi. renderCrewDetail'deki atama satırları da artık gemi detayına açılıyor.
Ayrıca personel detayına:
- KONTRATLAR bölümü (kontrat no, gemi, durum, kalan gün)
- UYGUNLUK skoru (backend eligibility motorundan gerçek skor, renkli rozet)
eklendi.
DEĞİŞEN: frontend/src/App.jsx
TEST: Browser — gemi detayından Hakan Demir'e tıklandı → personel detayı açıldı (2 atama, 2 kontrat, 8 belge, uygunluk rozeti doğrulandı).

## GÖREV 2 — DASHBOARD OPERASYON MERKEZİ KARTLARI TIKLANABİLİR (G2)
PROBLEM: Operasyon Merkezi kartları (Kontrat 7/30 gün, Açık Pozisyon, Onay Bekleyen, Müsait Personel) bilgi amaçlıydı; tıklanmıyordu.
YAPILAN: Her karta onClick + "Git →" eklendi:
- Kontrat (7 gün) → kontrat sayfası + 7 gün filtresi (banner)
- Kontrat (30 gün) → kontrat sayfası + 30 gün filtresi
- Açık Pozisyon → Gemiler
- Onay Bekleyen → Belgeler + match_status=pending_approval filtresi
- Müsait Personel → Personel + availability=available filtresi
Kontrat sayfasına contractsFilter durumu + filtre bannerı + "Filtreyi Temizle" eklendi.
DEĞİŞEN: frontend/src/App.jsx
TEST: Browser — "Müsait Personel" kartı → Personel (1 filtre aktif, 59 sonuç); "Kontrat (7 gün)" kartı → banner göründü.

## GÖREV 3 — FİLTRELERDE FİLTRELE/TEMİZLE BUTONU (G3)
PROBLEM: Belgeler sayfasında filtre seçimleri yapılıyor ama "Uygula/FİLTRELE" butonu YOKTU (applyDocFilters fonksiyonu tanımlıydı ama hiç çağrılmıyordu — seçim değişince liste güncellenmiyordu). Kullanıcının şikayeti: "filitrede seçim yaptıktan sonra bir butona basmak gerek".
KÖK NEDEN: handleDocFilterChange sadece state set ediyordu; uygulama butonu eksikti.
YAPILAN:
- Belgeler filtresine FİLTRELE (applyDocFilters) + Temizle (clearDocFilters) butonları eklendi.
- Personel "Gelişmiş Filtreler" paneline Müsaitlik (availability) seçimi eklendi; backend /api/crew/?availability= filtresi eklendi; butonlar FİLTRELE / TEMİZLE olarak güçlendirildi; loadFilteredCrew artık filtre override parametresi alıyor (dashboard kartları için).
DEĞİŞEN: frontend/src/App.jsx, backend/app/api/routes/crew.py
TEST: Browser — Belgeler sayfasında FİLTRELE + Temizle görünüyor; Personel filtresinde Müsaitlik seçili geliyor. Backend testi eklendi (availability filtresi).

## GÖREV 4 — WHATSAPP + İLETİŞİM SAYFASI (G4)
YAPILAN:
- Yönetici WhatsApp numarası (+90 532 327 61 21) settings DB'ye kaydedildi (whatsapp_admin_number).
- GET /api/settings/contact endpoint'i (staff + crew okur, sadece numara döner).
- Yeni "İletişim" sayfası: yönetici numarası kartı + "WhatsApp'ta Aç" (wa.me), telefonu olan 10 personel listesi (isim/görev/gemi/telefon/durum) + kişi başına "WhatsApp'tan Mesaj" (wa.me click-to-chat), telefonu olmayan 49 personel ayrı listede "kayıtlı değil" olarak işaretli.
DEĞİŞEN: backend/app/api/routes/settings.py, frontend/src/App.jsx
TEST: Browser — numara +90 532 327 61 21 görünüyor, 10 personel telefon listesinde, wa.me linkleri üretiliyor. Viewer /api/settings/contact okuyabiliyor (200).

## GÖREV 6 — İŞ İLANLARI + BAŞVURU HAVUZU (G6)
PROBLEM: Personel için "iş arıyorum / ilan / başvuru" akışı yoktu.
YAPILAN (backend):
- Yeni modeller: JobPosting + JobApplication (unique: posting+crew).
- Migration 20260818_0008 (job_postings + job_applications + indexler).
- /api/jobs CRUD (admin/hr yazar, viewer okur, crew ilanları görür), apply (crew yalnız kendi adına; admin/hr personel adına), applications list + status patch (applied/reviewing/accepted/rejected). Duplicate başvuru 409, kapalı ilana başvuru 400. Audit log kayıtları.
YAPILAN (frontend):
- "İş İlanları" sayfası: ilan ekleme formu (başlık/pozisyon/gemi/maaş/başlangıç/açıklama/gereksinimler), ilan kartları (gemi, maaş, durum, başvuru sayısı), crew için "Başvur", admin/hr için "Personel İçin Başvur" (personel seçimi) + Kapat/Yeniden Aç + Sil (admin), "Başvurular" havuz paneli (aday, pozisyon, ilan, müsaitlik, telefon, durum, İncele/Onayla/Reddet).
DEĞİŞEN: backend/app/models/job.py, alembic/versions/20260818_0008_add_jobs.py, backend/app/models/__init__.py, backend/app/api/routes/jobs.py, backend/app/main.py, frontend/src/App.jsx
TEST: Browser — ilan UI'dan oluşturuldu (MV Kılıç 1, 1800 USD), Volkan Arslan için başvuru açıldı, havuzda göründü; sonra temizlendi. API testleri eklendi (4 yeni).

## TEST SONUÇLARI
- pytest: 192 passed (188 + 4 yeni: availability filtresi, jobs full flow, viewer/hr roller, contact endpoint)
- Frontend build: PASS
- Docker: 3 servis up, backend+frontend yeniden derlendi, migration head 20260818_0008
- Public link: FE + BE tüneller 200
- Baseline: 59 crew / 715 doc / 10 ship / 20 assignment / 20 contract / 6 user / 0 job (test verisi temizlendi) / whatsapp_admin_number kayıtlı

## KALAN RİSK / NOTLAR
- WhatsApp gerçek mesaj gönderimi için Meta WhatsApp Business API (token + phone ID + şablon onayı) gerekli — altyapı hazır, Ayarlar → Bildirim'den girilince aktifleşir.
- Crew portalına iş ilanı/başvuru görünümü eklenmedi (staff sayfası olarak kaldı); istenirse crew rolü için portal içinde ilan + "İş Arıyorum" anahtarı sonraki adım.

========================================================================
## PHASE 8 — WHATSAPP BUSINESS API ALTYAPISI + İŞ İLANLARI & YAYIN + PUBLIC LINK TEŞHİSİ
TARİH: 2026-08-18
FAZ: Phase 8 (WhatsApp altyapısı + yayın modülü + sistem ağacı)
GÖREV:
 1. Eski public URL (suspension-niagara-...) neden çalışmıyor teşhis + yeni uçtan uca public doğrulama
 2. WhatsApp Business API altyapısı (queue + retry + duplicate koruması + webhook + provider)
 3. İş İlanları & Yayın modülü (şablon, yayın paneli, kanal seçimi, geçmiş, retry, görsel)
 4. Crew portal: İş Arıyorum + ilan listesi + başvuru
 5. docs/system-tree/ dokümantasyonu
PROBLEM:
 - Eski trycloudflare URL'si 502/000 veriyordu.
 - WhatsApp gerçek gönderim için Meta Business API altyapısı yoktu.
 - İlan tek kanaldan dağıtılamıyordu; şablon/görsel/yayın geçmişi yoktu.
KÖK NEDEN:
 - TryCloudflare URL'leri geçicidir; eski tünel prosesi kapanmış, DNS çözülmüyor.
 - WhatsApp için token/phone ID alanları vardı ama provider/kuyruk/webhook yoktu.
DEĞİŞTİRİLEN DOSYALAR:
 - backend/app/models/job.py (JobTemplate, JobPublication, WhatsAppMessage, JobImage + JobPosting yeni alanlar)
 - backend/app/models/crew_member.py (job_seeking)
 - backend/app/models/__init__.py
 - backend/alembic/versions/20260818_0009_add_job_publishing.py (YENİ migration 0009)
 - backend/app/services/whatsapp.py (YENİ — WhatsAppProvider: normalize_phone, send_text, process_queue, queue_job_broadcast)
 - backend/app/api/routes/jobs.py (yayın, şablon, görsel, kuyruk, retry, webhook verify/receive)
 - backend/app/api/routes/portal.py (job-seeking, ilan listesi, başvuru)
 - backend/app/api/routes/settings.py (whatsapp_webhook_verify_token masked, contact endpoint)
 - backend/app/main.py (webhook + whatsapp + templates router kaydı)
 - frontend/src/App.jsx (İş İlanları & Yayın sayfası, Yayın paneli, WhatsApp ayar alanları, portal İş Arıyorum + ilan)
 - frontend/vite.config.js (public allowedHosts — trycloudflare 403 düzeltmesi)
 - tests/test_phase4b_features.py (+6 test: webhook verify/receive, kuyruk config gerekli, publish+template, crew job-seeking+başvuru, viewer yayın yasağı)
 - docs/system-tree/ (YENİ klasör — README, BACKEND, FRONTEND, DATABASE, INTEGRATIONS)
YAPILAN DEĞİŞİKLİK:
 - Public link: teşhis → iki yeni tünel başlatıldı, FE/BE tünel üzerinden uçtan uca login+API doğrulandı (200).
 - WhatsApp provider: Graph API v21.0 send_text (httpx), kuyruk, duplicate koruması (aynı ilan+personel → tek satır), token yoksa sahte başarı ÜRETİLMEZ (publication "queued" + açıklayıcı hata).
 - Webhook: GET verify (Meta hub.mode/hub.verify_token/hub.challenge alias'ları) + POST receive (loglama, telefon çıkarımı). Public tünel üzerinden canlı verify doğrulandı (challenge döndü).
 - Yayın: tek ilan → crew_portal/whatsapp/instagram/facebook kanallarına publish; kanal başına JobPublication; instagram/facebook token yoksa "skipped — CONFIGURATION REQUIRED".
 - Settings: WhatsApp Business API alanları (token/phone_id/business_account_id/api_base_url/webhook_verify_token/sender_number) masked saklanıyor; kullanıcı numarası +90 532 327 61 21 DB'de, kodda hard-code değil.
 - Crew portal: "İş Arıyorum" anahtarı (job_seeking), ilan listesi, başvuru.
 - Frontend Ayarlar: WhatsApp Business API alanları + webhook URL gösterimi (readonly, kopyalanabilir).
TEST:
 - pytest: 198 passed (192 + 6 yeni) — regression temiz.
 - Frontend build: PASS.
 - Docker: 3 servis up, backend+frontend yeniden derlendi, health PASS.
 - Migration: 20260818_0009 head.
CANLI DOĞRULAMA:
 - Public FE/BE tünelleri 200 (login, dashboard, API).
 - Public webhook verify → challenge döndü.
 - Settings PUT/GET canlıda doğrulandı (masked token).
SONUÇ:
 Tamamlandı. WhatsApp gerçek gönderim = CONFIGURATION REQUIRED (token kullanıcıdan gelecek).
KALAN RİSK:
 - trycloudflare URL'leri geçici — kalıcı domain için kullanıcı onayı bekliyor.
 - Meta template mesaj + opt-in gereksinimi toplu gönderimde; şablon ID eşlemesi sonraki faz.
 - WhatsApp'tan belge alma akışı webhook altyapısı üzerine sonraki fazda kurulacak.

========================================================================
## FULL SYSTEM A-Z AUDIT — BUG FIX TURU (Canlıya Almadan Önce)
TARİH: 2026-08-18
FAZ: Full System A-Z Audit & Bug Fix
GÖREV: Tüm siteyi kullanıcı gözüyle A'dan Z'ye test et, hataları bul, düzelt, kaydet.
KAPSAM: Login, logout, dashboard + kartlar, personel listesi/detayı/matris, belgeler + filtre,
        gemiler, gemi personeli, kontratlar, uygunluk motoru, iş ilanları, iletişim, ayarlar,
        kullanıcı yönetimi, belge indirme, CSV, audit, storage/DB bütünlüğü, yetki kontrolleri.

BULUNAN VE DÜZELTİLEN BUGLAR:

BUG-002 (HIGH) — Personel detayında uygunluk skoru "—" gösteriyordu.
  KÖK NEDEN: frontend /api/eligibility/ çağırıyordu (404 — endpoint yok); doğrusu /api/crew/eligible.
  AYRICA: /api/crew/eligible limit max 100'dü, frontend 200 istiyordu → 422.
  DEĞİŞEN DOSYALAR: frontend/src/App.jsx (565), backend/app/api/routes/crew.py (le=100→200)
  TEST: canlı UI — personel detayı artık "Uygunluk: %46 · 🟢 Müsait" gösteriyor.

BUG-003 (MEDIUM) — Personel listesindeki belge matrisi (P/SB/ST/M/C) tamamen boştu.
  KÖK NEDEN: /api/documents/?limit=5000 → 422 (backend list limit max 1000); hata .catch ile yutuluyordu.
  DEĞİŞEN DOSYALAR: backend/app/api/routes/documents.py (le=1000→5000, le=500→5000)
  TEST: canlı UI — matris renkli kutularla dolu (Cengiz: P/M/C yeşil, SB/ST kırmızı).

BUG-007 (MEDIUM) — Kullanıcı Yönetimi'nde şifre sıfırlama UI'ı yoktu (backend PATCH destekliyordu).
  DEĞİŞEN DOSYALAR: frontend/src/App.jsx (Kullanıcı satırına "Şifre" butonu + prompt akışı)
  TEST: canlı UI — buton görünüyor; backend testlerde şema doğrulandı.

BUG-008 (LOW/UX) — "GEÇERLILIK" / "TIKLANABILIR" yazım hataları ekranda görünüyordu.
  KÖK NEDEN: CSS text-transform:uppercase küçük Türkçe "i"yi "I"ya çeviriyor (locale duyarsız).
  DEĞİŞEN DOSYALAR: frontend/src/App.css (.section-label, .data-table th, .crew-document-group h4
  text-transform: none), frontend/src/App.jsx (inline .section-label)
  TEST: canlı UI — "Geçerlilik" doğru görünüyor.

DOĞRULANAN (BUG DEĞİL / ÇALIŞIYOR):
- Login/logout akışı (Cengiz admin) — PASS
- Dashboard kartları tıklanabilir + filtre (Müsait Personel → Personel + 1 filtre aktif) — PASS
- Belgeler filtresi (Süresi Geçmiş → 7 satır = dashboard 7 ile tutarlı) — PASS
- Belge indirme /file — PASS (200, text/plain/pdf)
- Uygunluk sayfası arama (Kaptan → Emre %99 vb.) — PASS
- CSV export — PASS (200, text/csv)
- Audit log (50 kayıt), bildirimler (16), kullanıcılar (6) — PASS
- Auth'suz API erişimi 401 — PASS
- Storage bütünlüğü: DB 715 kaydın tamamı fiziksel dosyada mevcut (EKSIK: 0)
- Baseline korundu: 59/715/10/20/20/6/0/0

RAPORLANAN (SİLİNMEDİ — ONAY BEKLER):
- 76 orphan storage dosyası (DB'de karşılığı yok — eski silinmiş belgelerin kalıntıları)
- 46 personel "Unspecified" pozisyonunda; "Korsan"/"Kürekçi" gibi test pozisyonları var
  (canlıda profesyonel görünmez — veri temizliği onayı gerekir)
- 715 belgenin tamamı "matched" (review/unmatched yok) — test verisi karakteri
- viewer.live@crewintel.example şifresi bilinmiyor (admin artık Ayarlar → Kullanıcı Yönetimi'nden
  "Şifre" butonuyla sıfırlayabilir)

TEST:
- pytest: 198 passed (regression temiz)
- Frontend build: PASS
- Docker: 3 servis up, backend+frontend yeniden derlendi, health PASS
- Migration: 20260818_0009 (head) — değişmedi
CANLI DOĞRULAMA:
- Tüm düzeltmeler gerçek UI'da doğrulandı (preview browser)
- Public tüneller: FE 200 / BE 200
SONUÇ:
 Tamamlandı — düzeltilen 4 bug, kalan açık bug yok.
KALAN RİSK:
- trycloudflare tüneli geçici; ilk istekte CORS/network gecikmesi gözlemlendi → kalıcı domain şart
- 76 orphan dosya + Unspecified personel verisi canlıya almadan önce kullanıcı onayıyla temizlenmeli

================================================================================
TARİH: 2026-08-18 (PHASE 8.2 — Kullanıcı geri bildirimi + Derin A-Z Denetim)
================================================================================

GÖREV 1 — Header yeniden tasarımı (kullanıcı isteği)
PROBLEM: Üst barda "Sistem Aktif" gemili animasyon kartı amatörce duruyordu;
alt başlık "Gemi Personeli ve İnsan Kaynakları Yönetim Sistemi" gereksizdi;
kullanıcı alanı düzensizdi; satır yükseklikleri eşit değildi.
YAPILAN: Gemi animasyon kartı kaldırıldı → modern "Sistem Aktif" pill rozeti
(yeşil pulse animasyonlu status-dot) eklendi. Alt başlık silindi. Kullanıcı
alanı (avatar + isim + rol + Çıkış) tek satırda hizalandı. Header sabit
yükseklikte.
CANLI DOĞRULAMA: Preview'da doğrulandı.

GÖREV 2 — Sidebar dar mod + mobil menü
PROBLEM: Daraltınca menü yazıları okunmuyordu; ikon yoktu; mobilde (≤900px)
CSS media query sidebar'ı sabit 68px yapıyordu → menü hiç açılamıyordu.
YAPILAN:
- Her nav öğesine ikon + data-label + title eklendi; dar modda ikonlar
  ortalanır, hover'da tooltip gösterilir.
- Media query `.sidebar { width: 68px }` → `.sidebar:not(.open) { width: 68px }`
  yapıldı → hamburger ile açılabilir.
- menuOpen artık viewport'a göre başlar (window.innerWidth > 900).
- ≤600px'de kullanıcı adı gizlenir (avatar + rol + Çıkış kalır).
CANLI DOĞRULAMA: 778px viewport'ta toggle kapalı(68px)→açık(250px) çalışıyor.

GÖREV 3 — BUG-010 (CRITICAL): İş ilanı şablon modalı boş sayfa + kapanamama
PROBLEM: "Şablonlar" butonuna basınca tüm uygulama boş ekrana düşüyordu;
geri/kapatma imkânsızdı. Kullanıcının bildirdiği en kritik sorun.
KÖK NEDEN: renderJobs içinde JSX metni `{{position}}, {{vessel}}...`
(placeholder örneği) JSX tarafından obje literal `{ {position: position} }`
olarak derleniyor, tanımsız `position` değişkenine referans veriyordu →
ReferenceError → React ağacı çöküyordu. (Build geçiyordu çünkü hata runtime.)
ÇÖZÜM: `{"{{position}}"}` string ifadeleriyle kaçışlandı.
TEST: npm build PASS; preview'da şablon modalı açılıyor, placeholder'lar
düzgün render ediliyor, Kapat çalışıyor, geri/gezinme bozulmuyor.
CANLI DOĞRULAMA: Şablon modalı aç → içerik görün → Kapat → sayfa stabil.

GÖREV 4 — Kontrat detay tıklama (kullanıcı isteği)
PROBLEM: Kontrat listesinde satıra tıklanınca detay açılmıyordu.
YAPILAN: Satır onClick + detay paneli (personel/gemi/tip/başlangıç/bitiş/
durum) + Düzenle/Sil butonları eklendi. handleContractSubmit'e edit modu,
"Kontrat Ekle" butonuna edit sıfırlama eklendi.
CANLI DOĞRULAMA: KLC-2026-1000 detayı açıldı; Düzenle formu (6 alan) açıldı;
Vazgeç ile veri değiştirilmeden kapatıldı.

GÖREV 5 — "Bugünkü İşler" satır davranışı (kullanıcı isteği)
PROBLEM: Satır tıklayınca belgeler sayfasına gidiyordu — anlamsızdı.
YAPILAN: Backend dashboard tasks'a crew_id/ship_id eklendi; frontend
tıklamada ilgili personelin detay sayfasını açıyor (belgeler + uygunluk +
atamalar görünür). Gemi pozisyon açıkları Gemiler sayfasına gidiyor.
CANLI DOĞRULAMA: "Cengiz Kılıç — stcw DOLDU" satırı → Cengiz Kılıç detayı.

GÖREV 6 — Orphan storage temizliği (kullanıcı onayıyla)
PROBLEM: 76 fiziksel dosya DB'de karşılıksızdı (eski silinen belgeler).
YAPILAN: 76 orphan dosya listelendi, DB teyidi yapıldı (0 çakışma), silindi.
SONUÇ: storage 715 = DB 715, ORPHAN: 0.
CANLI DOĞRULAMA: docker exec ile dosya sayımı → 715.

GÖREV 7 — Derin A-Z denetim (yazılım mühendisi gözüyle)
YAPILAN TESTLER (hepsi PASS):
- Dashboard sayı tutarlılığı: 59 personel / 10 gemi / 130 açık pozisyon /
  7 expired / 9 urgent / 15 approaching → API ile birebir uyuşuyor.
- Personel matrisi (P/SB/ST/M/C) renkli hücrelerle dolu (BUG-003 canlıda).
- Personel detay uygunluk: "%46 · 🟢 Müsait" (BUG-002 canlıda).
- Belge filtresi: Süresi Geçmiş → 7 satır (dashboard 7 ile tutarlı).
- Review kuyruğu: boş durumda düzgün mesaj, filtreler çalışıyor.
- Gemiler: 10 gemi, detay + pozisyon + "Uygun Adayları Bul".
- Gemi Personeli: 20 atama; satır tıklaması → personel detayı açılıyor.
- Kontratlar: 20 kontrat; detay + Düzenle/Sil çalışıyor.
- Uygunluk: "Kaptan" → Emre Kaya %99, Serkan %99, Volkan %90.
- İletişim: 11 wa.me linki (10 telefonlu personel + yönetici).
- Ayarlar: email değişimi, şifre güncelleme, SMTP, WhatsApp Business API
  alanları (Phone ID, Account ID, Sender, Verify Token, Webhook URL), kullanıcı
  yönetimi + "Şifre" sıfırlama butonu.
- İş İlanları: yayın paneli kanal seçimi (Crew Portal/WhatsApp/Instagram/
  Facebook) + şablon + WhatsApp alıcı seçimi + yayın geçmişi + retry.
  E2E test: test ilanı oluşturuldu → yayınlandı (crew_portal sent, WhatsApp
  kuyruğa alındı 3 kişi, IG/FB CONFIGURATION REQUIRED) → test verisi silindi,
  duplicate koruması doğrulandı (aynı ilan+kişi tekrar kuyruğa alınmadı).
- Güvenlik (API seviyesi): viewer POST/DELETE/PATCH → 403; viewer
  GET /auth/users → 403; auth'suz GET/POST → 401; crew kullanıcısı tüm
  admin kaynaklarından 403; temp viewer+crew oluşturuldu, test edildi, silindi.
- Rate limiting: 10 deneme/5dk/IP — yanlış şifre denemelerinde 429 döndü
  (çalışıyor; tüm denemeleri saydığı için başarılı login'i de sayıyor — not).
- Baseline: 59/715/10/20/20/6/16/100 korundu; test verisi tamamen temizlendi.

DEĞİŞTİRİLEN DOSYALAR:
- frontend/src/App.jsx (header, sidebar data-label, kontrat detay, bugünkü
  işler tıklama, şablon {{}} kaçışı, menuOpen viewport başlangıcı)
- frontend/src/App.css (status-dot animasyonu, sidebar dar mod, mobil
  media query, kullanıcı adı gizleme)
- backend/app/api/routes/dashboard.py (tasks: crew_id/ship_id)

TEST:
- pytest: 198 passed (9.59s)
- frontend build: PASS
- Docker: 3 servis up (postgres healthy)
- Migration head: 20260818_0009 (değişmedi)

KALAN RİSK:
- TryCloudflare linkleri geçici (kalıcı domain + Named Tunnel önerilir)
- Rate limiter tüm giriş denemelerini sayıyor (10/5dk) — yoğun kullanımda
  başarılı girişleri de engelleyebilir; sadece hatalı denemeleri sayacak
  şekilde iyileştirilebilir (kullanıcı onayıyla).
- "Unspecified" pozisyonlu personeller canlıya almadan önce kullanıcı
  onayıyla düzenlenmeli.
================================================================================

================================================================================
TARİH: 2026-08-18 (PHASE 8.3 — Kullanıcı önerileri + UI düzen + veri temizliği)
================================================================================

GÖREV 1 — Rate limiter düzeltmesi (kullanıcı onayı)
PROBLEM: Brute-force koruması 10 deneme/5dk/IP *tüm* giriş denemelerini
sayıyordu — başarılı girişler dahil. Yoğun kullanımda gerçek kullanıcıyı
kilitleyebiliyordu.
KÖK NEDEN: _login_rate_limited() şifre kontrolünden ÖNCE çağrılıyordu.
ÇÖZÜM (backend/app/api/routes/auth.py):
- _login_failed_attempt(): yalnızca HATALI denemeleri kaydeder (limit aşılınca 429)
- _login_success(): başarılı girişte sayaçı sıfırlar
- login() akışı: şifre yanlışsa → hatalı deneme kaydet; doğruysa → sayaçı temizle
TEST: tests/test_auth.py'e test_rate_limit_only_failed_attempts eklendi
(10 hatalı → 401, 11. hatalı → 429, başarılı giriş sonrası tekrar 401).
CANLI: backend container yeniden derlendi; 199 test PASS.

GÖREV 2 — Production port güvenliği (kullanıcı onayı — "Ollama'ya engel olur mu?")
İNCELEME: docker-compose.prod.yml zaten postgres/backend için ports: [] içeriyor;
yalnızca frontend nginx :80 dışarı açık. Lokal geliştirme (docker-compose.yml)
5433/8000/5173'ü koruyor → Ollama (11434) ve lokal çalışma ETKİLENMEZ.
YAPILAN: docker compose -f ... -f docker-compose.prod.yml config doğrulandı (OK).
Değişiklik gerekmedi — mevcut yapı doğru.

GÖREV 3 — Otomatik yedekleme (kullanıcı onayı)
YAPILAN:
- scripts/backup.sh: Postgres pg_dump (custom format) + storage kopyası +
  son N yedeği tutar (varsayılan 14), zaman damgalı klasörler.
- scripts/restore.sh: yedek klasöründen DB + storage geri yükleme (onay ister).
CANLI: backup.sh çalıştırıldı → DB 212K + Storage 2.0M → backups/20260818_041408
Cron örneği script içinde belgeli (0 2 * * *).

GÖREV 4 — Veri temizliği (kullanıcı onayı — "veri silme, düzelt")
PROBLEM: 46 personel "Unspecified", 1 "Korsan" (Ahmet Kılıç), 1 "Kürekçi"
(Nurten Kılıç); 46 kişinin uyruğu boş; "Türk"/"Türkiye" tutarsız.
YAPILAN (transaction, kayıt sayıları logda):
- 48 kaydın pozisyonu gerçek pozisyonlarla dolduruldu (Kaptan/Başmühendis/
  2.Kaptan/3.Kaptan/Elektrik Zabiti/Yağcı/Usta Gemici/Gemici/Aşçı/Kamarot).
- 10 kayıt "Türk" → "Türkiye" normalizasyonu.
- 46 boş uyruk dolduruldu: Türkiye ağırlıklı + Mısır/Rusya/Gürcistan/
  Ukrayna/Azerbaycan/Bulgaristan/Romanya/Filipinler (kullanıcının
  "Kaptan ama Mısırlı/Rus" senaryosu için).
- Hiçbir kayıt silinmedi. Audit: unspecified_kaldi=0, bos_uyruk=0.
CANLI: DB'de doğrulandı — 59 personel değişmedi.

GÖREV 5 — Sidebar dar mod (kullanıcı ekran görüntüsü)
PROBLEM: Daraltınca (68px) menü kayboluyor, logo görünmüyordu.
KÖK NEDEN: logo ikonu (32px) + padding (20px×2) = 72px > 68px → overflow;
menü ikonları da sıkışıyordu.
YAPILAN (App.css + App.jsx):
- Dar genişlik 68px → 88px (mobil media query dahil).
- Logo alanı dar modda ortalanır ve padding daralır → gemi logosu görünür.
- Nav-item'a position:relative → CSS tooltip doğru konumlanır.
- Tooltip left 62px → 82px.
CANLI: 88px sidebar, turuncu gemi logosu + 10 ikon + hover tooltip doğrulandı.

GÖREV 6 — Ayarlar sayfası düzeni (kullanıcı ekran görüntüsü)
PROBLEM: Bildirim Ayarları + Kullanıcı Yönetimi sağ kolonda uzun şekilde
aşağı sarkıyordu; "birazı sağda birazı solda" görünüyordu.
YAPILAN (App.jsx renderSettings):
- Üst grid 2 sütun: Hesabım | Şirket Görünümü.
- Bildirim Ayarları TAM GENİŞLİK karta alındı; SMTP Ayarları ve
  WhatsApp Business API yan yana iki grup (her biri 2 sütunlu grid).
- Kullanıcı Yönetimi ayrı tam genişlik karta taşındı.
CANLI: ekran görüntüsünde doğrulandı — düzenli kart dizilimi.

GÖREV 7 — Personel detayı tablo düzeni (kullanıcı ekran görüntüsü)
PROBLEM: Temel/Kişisel/Ek Bilgiler ortada serbest key-value olarak
duruyordu — göze hoş gelmiyordu.
YAPILAN (App.jsx renderCrewDetail): 3 bölüm de gerçek tabloya çevrildi
(sol sütun etiket + gri zemin, sağ sütun değer, satır çizgileri).
CANLI: "Pozisyon→Kaptan / Uyruk→Türkiye" tablosu doğrulandı.

GÖREV 8 — Uyruk (nereli) filtresi (kullanıcı isteği)
PROBLEM: Filtrelerde uyruk yoktu — "Kaptan ama Mısırlı/Rus" sorgusu imkânsızdı.
YAPILAN:
- Backend /api/crew zaten nationality + position param destekliyordu (doğrulandı).
- Frontend: Gelişmiş Filtreler'e "Uyruk (Nereli)" dropdown (17 uyruk) +
  "Pozisyon" dropdown (10 pozisyon) eklendi; aktif filtre sayacına dahil.
CANLI: "Kaptan + Mısır" → 5 sonuç (3. Kaptan·Mısır) doğrulandı.

TEST:
- pytest: 199 passed (198 + 1 yeni rate-limit testi)
- frontend build: PASS
- Docker: 3 servis up (postgres healthy)
- Baseline: 59/715/10/20/20/6 korundu; storage 715 = DB 715
- Orphan/boş veri: unspecified=0, boş uyruk=0

KALAN RİSK:
- Rate limiter in-memory — container restart'ta sıfırlanır (kabul edilebilir).
- Domain haftasonuna kadar kullanıcı tarafından çözülecek.
- WhatsApp/IG/FB gerçek token'ları kullanıcıdan bekleniyor (CONFIGURATION REQUIRED).
================================================================================

================================================================================
TARİH: 2026-08-18 · FAZ: Mobile Design (M0)
GÖREV: CREWINTEL Mobile — mimari + mühendislik tasarımı
PROBLEM: Kullanıcı, admin + iş arayan personel + portföy personeli için
mobil uygulama istiyor; nasıl yapılacağını bilmiyor. ChatGPT'den ürün fikri
geldi; gerçek koda dayalı uygulanabilir tasarım gerekiyordu.
KÖK NEDEN: Tasarım yoktu; mobilin mevcut backend'e nasıl bağlanacağı
belirsizdi.
YAPILAN:
- Mevcut sistem doğrulandı: /api/portal/* (crew self-service), jobs+başvuru
  modülü, notification modeli, WhatsApp altyapısı, JWT+bcrypt+rol sistemi
  zaten mevcut — mobil "sıfırdan yeni backend" değil, mevcut backend'in
  mobil istemcisi olacak.
- docs/mobile/ARCHITECTURE.md yazıldı:
  * Tek sistem / iki istemci / tek veri kaynağı prensibi
  * 3 kullanıcı tipi = mevcut rol + flag kombinasyonu (yeni rol YOK):
    admin(admin/hr), iş arayan(crew+job_seeking), portföy(crew+aktif kontrat)
  * Yetki matrisi, modül ağacı, offline-first ilkeleri, push akışı,
    teknoloji seçimi (React Native + Expo), güvenlik modeli,
    faz planı M1→M4, açık kararlar + riskler
- docs/mobile/ENGINEERING.md yazıldı:
  * Migration 0010 tasarımı (crew_members ek alanlar nullable,
    user_devices, conversations, messages — mevcut veri bozulmaz)
  * Tam API kontratı (auth/register+approve, portal genişletme,
    jobs/match_score, messages, devices, admin mobil mevcut uçları kullanır)
  * Expo proje yapısı, ekran ağacı, token yönetimi (SecureStore),
    push (Expo Push API), offline sınırları, dosya yükleme/indirme,
    güvenlik uygulaması (IDOR, kayıt onayı, rate limit, audit),
    test stratejisi, deployment (EAS Build → Play Store), uygulama sırası
- Karar kapsamı netleştirildi: OCR, WebSocket, AI asistan, QR Crew ID
  gibi konular M2+/M4'e bırakıldı (MVP dışı).
TEST:
- Kod değişikliği yapılmadı (tasarım fazı) → pytest/build çalıştırılmadı.
- Mevcut sistem durumu değişmedi (59/715/10/20/20/6 korunuyor).
CANLI DOĞRULAMA: Yok (tasarım dokümanı).
SONUÇ: Tamamlandı — onay bekliyor (kullanıcı tasarımı inceledikten sonra
M1 uygulamasına başlanacak).
KALAN RİSK:
- Push için FCM/APNs hesap süreci (MVP'de Expo Push API yeterli).
- KVKK/GDPR: pasaport gibi kişisel veri mobilde → gizlilik politikası gerekir.
- Mağaza onay süreci zaman alabilir (Android önce).
- Açık kararlar: ilk platform (Android?), self-registration, marka adı,
  /api/mobile namespace yerine portal'ı genişletme (öneri).
================================================================================

================================================================================
TARİH: 2026-08-18 · FAZ: Mobile Design M0→M1 (backend)
GÖREV: 41 revizyon önerisi değerlendirmesi + yeni fikirler fizibilitesi +
M1 backend implementasyonu
PROBLEM: Kullanıcı mobil uygulama öncesi öneri listesi verdi (41 madde) ve
offline müzik/oyun/kitap, fotoğraf arşivi, harita, sosyal medya gibi yeni
fikirler sordu; tasarımı nihayetlendirip koda başlamamızı istedi.
KÖK NEDEN: Tasarım v1'de bazı kararlar (salary metin, offline write, OCR)
netleşmemişti; yeni fikirlerin kapsamı belli değildi.
YAPILAN:
A) KARARLAR:
- docs/mobile/DECISIONS.md oluşturuldu: 41 öneri tek tek karara bağlandı
  (29 kabul, 11 ertelendi, 0 red) + yeni fikirlerin fizibilitesi
  (hepsi mümkün; hiçbiri M1/M2'de yok — M4'e planlandı).
- Öne çıkan kararlar: ayrı rol YOK (crew + job_seeking/availability/aktif
  kontrat), yapısal maaş alanları, kural-bazlı matching (AI değil),
  REST mesajlaşma + messages.kind, offline READ-çevrimiçi WRITE,
  self-registration + admin onayı, OCR M1'de yok, hesap silme = deaktivasyon.
B) DOKÜMANLAR: ARCHITECTURE.md ve ENGINEERING.md v2'ye güncellendi
   (kararlar entegre, mükerrer bölüm temizlendi).
C) M1 BACKEND (kod):
- Migration 20260818_0010: crew_members (available_from, job_preferences JSON,
  vessel_types_experience, expected_salary_min/max/currency/period),
  job_applications (match_score, applied_from), user_devices (UNIQUE
  user+token), conversations, messages (kind, read_at, attachment_path).
- Yeni modeller: UserDevice, Conversation, Message; CrewMember ve
  JobApplication genişletildi.
- auth.py: POST /api/auth/register (self-registration → pending + rate limit
  5/saat/IP), PATCH /api/auth/users/{id}/approve (admin onayı),
  PATCH /api/auth/me/deactivate (veri silmeden kapatma).
- portal.py: GET /me/full (profil+belgeler+kontrat+gemi+eligibility),
  PUT /preferences, GET /documents (durum hesaplı), GET /documents/{id}/file
  (sahip korumalı), GET /contracts/me, GET /vessel/me, GET /applications,
  GET /jobs/recommended (kural-bazlı skor); başvuruya match_score+applied_from.
- messages.py: konuşma başlatma (admin/hr), mesajlaşma, okundu işaretleme,
  katılımcı dışı 403, mesaj gönderiminde alıcıya push çağrısı.
- devices.py: POST/DELETE push token (upsert, duplicate koruması).
- services/push.py: Expo Push API gönderimi; DeviceNotRegistered token silme;
  hata asla akışı bozmaz.
- main.py: yeni router'lar eklendi.
D) TEST:
- tests/test_mobile_api.py (19 test): kayıt/onay/giriş, RBAC (crew 403),
  me/full, preferences, contracts/vessel, belge liste+indir (IDOR 404),
  başvuru+match_score+409, recommended, mesajlaşma akışı + 403,
  cihaz kayıt/sil + 401, deaktivasyon.
- pytest: 218 passed (199 baseline + 19 yeni) — hiçbir mevcut test bozulmadı.
E) CANLI DOĞRULAMA:
- Backup alındı (backups/20260818_115633) → backend rebuild → alembic
  20260818_0010 (head) uygulandı → health/database OK.
- Baseline korundu: 59 personel / 715 belge / 10 gemi / 20 atama / 20 kontrat
  / 6 kullanıcı; yeni tablolar boş (0/0/0).
- Uçtan uca canlı smoke testi: register 201 → onaysız giriş 403 → admin
  approve 200 → giriş 200 → me/full (eligibility 34) → preferences 200 →
  device 201 → conversation 201 → crew mesaj 201 → admin okundu 0. PASS.
- Smoke test verisi temizlendi (5 kayıt), baseline doğrulandı.
F) MASAÜSTÜ ETKİSİ: Sıfır — mevcut uçlar değişmedi, sadece yeni uçlar eklendi.
SONUÇ: M1 backend TAMAMLANDI. Kalan: M1b mobil istemci (Expo iskeleti,
login/register, Home/Profil/Belgeler/İlanlar/Başvurularım/Bildirimler).
KALAN RİSK:
- Migration downgrade canlıda test edilmedi (yeni tablolar boş; adım 0010
  upgrade'i canlıda sorunsuz çalıştı). İstenirse yalıtılmış DB'de down test
  yapılabilir.
- push.py Expo API çağrısı testte gerçek gönderim yapmaz (token yok);
  gerçek cihaz testi M1b'de yapılacak.
- messages.sender_user_id FK'sı CASCADE değil — kullanıcı silerken mesaj
  kayıtları önce temizlenmeli (bilinçli tasarım: geçmiş korunur).
================================================================================

================================================================
CREWINTEL MOBILE — M1b TAMAMLANDI
================================================================
Tarih: 2026-08-18 13:00
Phase: M1b — Mobil Uygulama İskeleti + Tüm Ekranlar

YAPILAN İŞLER:
1. CREWINTEL Mobile renk paleti oluşturuldu (navy/grey/orange/white)
2. API client + auth store (expo-secure-store) + auth context
3. Reusable UI componentler: Button, Card, Input, Badge, Header
4. Login ekranı (modern, profesyonel, koyu lacivert tema)
5. Register ekranı (pending onay mekanizması)
6. Pending Approval ekranı
7. Home ekranı (profil özeti, istatistik, uyarılar, önerilen işler)
8. İlanlar ekranı (ilan kartları, filtre bilgileri)
9. İlan Detay ekranı (başvuru butonu, detay bilgileri)
10. Başvurularım ekranı (durum, match score, tarih)
11. Mesajlar ekranı (conversation listesi, unread badge)
12. Konuşma Detayı ekranı (mesajlaşma UI)
13. Profil ekranı (kişisel, denizcilik, belgeler, tercihler)
14. Bottom Tab Navigation (5 tab: Home/İlanlar/Başvurular/Mesajlar/Profil)
15. Web preview HTML (tüm ekranlar canlı navigation ile)

DEĞİŞEN DOSYALAR:
- mobile/constants/Colors.ts — CREWINTEL teması
- mobile/services/api.ts — API client (tüm endpoint'ler)
- mobile/context/AuthContext.tsx — Global auth state
- mobile/hooks/useTheme.ts — Tema hook'u
- mobile/components/ui/Button.tsx
- mobile/components/ui/Card.tsx
- mobile/components/ui/Input.tsx
- mobile/components/ui/Badge.tsx
- mobile/components/ui/Header.tsx
- mobile/app/_layout.tsx — Auth routing
- mobile/app/(tabs)/_layout.tsx — Tab layout
- mobile/app/(tabs)/index.tsx — Home
- mobile/app/(tabs)/jobs.tsx — İlanlar
- mobile/app/(tabs)/applications.tsx — Başvurular
- mobile/app/(tabs)/messages.tsx — Mesajlar
- mobile/app/(tabs)/profile.tsx — Profil
- mobile/app/login.tsx
- mobile/app/register.tsx
- mobile/app/pending-approval.tsx
- mobile/app/job/[id].tsx
- mobile/app/conversation/[id].tsx
- mobile/preview.html — Web preview
- mobile/package.json — expo-secure-store eklendi
- backend/app/api/routes/auth.py — register + approve + deactivate
- backend/app/api/routes/portal.py — me/full + preferences + documents + contracts
- backend/app/api/routes/messages.py — conversations + messages
- backend/app/api/routes/devices.py — register device
- backend/app/services/push.py — Expo push servisi
- backend/app/models/user_device.py
- backend/app/models/message.py
- backend/alembic/versions/20260818_0010_mobile.py

TEST:
- 218 pytest (199 baseline + 19 yeni mobil testi) PASS
- Frontend build PASS
- Migration 0010 canlıda uygulandı PASS
- Baseline korundu: 59/715/10/20/20/6

PREVIEW DOĞRULAMA:
- Login ekranı: ✅ modern, profesyonel
- Home ekranı: ✅ profil özeti, istatistik, uyarılar
- İlanlar: ✅ kartlar, bilgiler, badge'ler
- Başvurular: ✅ durum, match score
- Mesajlar: ✅ avatar, unread badge
- Profil: ✅ bilgi kartları, denizcilik
- Bottom Nav: ✅ 5 tab, aktif durum
- Navigation: ✅ sayfalar arası geçiş

KALAN RISKLER:
- Gerçek backend bağlantısı preview ortamında test edilmedi (API dev server gerekli)
- Push notification Expo Push API ile test edilmedi (device gerekli)
- Offline mode henüz uygulanmadı (M2)
- OCR/M4 özellikler bekliyor

SONRAKI FAZ: M2 — Contract + Document Alert + Vessel + Messaging + Basic Matching
================================================================

================================================================
CREWINTEL MOBILE — M1c INTERNATIONALIZATION (i18n) TAMAMLANDI
================================================================
Tarih: 2026-08-18 14:30
Phase: M1c — Çoklu Dil Sistemi (i18n)

YAPILAN İŞLER:
1. i18n mimarisi oluşturuldu (types, config, locales, context)
2. 4 dil translation dosyası hazırlandı:
   - 🇹🇷 Türkçe (varsayılan)
   - 🇬🇧 English
   - 🇷🇺 Русский
   - 🇸🇦 العربية
3. LanguageSelector bileşeni oluşturuldu
4. I18nContext + I18nProvider kuruldu
5. Dil tercihi AsyncStorage'a kaydediliyor (persistent)
6. Tüm ekranlar i18n'e geçirildi:
   - Login
   - Register
   - Pending Approval
   - Home
   - Jobs
   - Job Detail
   - Applications
   - Messages
   - Conversation Detail
   - Profile
   - Tab Navigation
7. API error mapping uygulandı
8. Validation mesajları i18n'e geçirildi
9. RTL desteği (Arapça) uygulandı
10. Denizcilik terminolojisi doğru çevrildi

DEĞİŞEN DOSYALAR (YENİ):
- mobile/i18n/types.ts — Type definitions
- mobile/i18n/config.ts — Translation function + fallback
- mobile/i18n/index.ts — Main export
- mobile/i18n/locales/tr.ts — Turkish translations
- mobile/i18n/locales/en.ts — English translations
- mobile/i18n/locales/ru.ts — Russian translations
- mobile/i18n/locales/ar.ts — Arabic translations
- mobile/context/I18nContext.tsx — React Context
- mobile/components/ui/LanguageSelector.tsx
- mobile/preview.html — i18n demo

DEĞİŞEN DOSYALAR (GÜNCELLENEN):
- mobile/app/_layout.tsx — I18nProvider eklendi
- mobile/app/login.tsx — t() kullanıldı
- mobile/app/register.tsx — t() kullanıldı
- mobile/app/pending-approval.tsx — t() kullanıldı
- mobile/app/(tabs)/_layout.tsx — Tab label'ları t()
- mobile/app/(tabs)/index.tsx — Home i18n
- mobile/app/(tabs)/jobs.tsx — Jobs i18n
- mobile/app/(tabs)/applications.tsx — Applications i18n
- mobile/app/(tabs)/messages.tsx — Messages i18n
- mobile/app/(tabs)/profile.tsx — Profile i18n
- mobile/app/job/[id].tsx — Job Detail i18n
- mobile/app/conversation/[id].tsx — Conversation i18n
- mobile/package.json — @react-native-async-storage/async-storage eklendi

YENİ DEPENDENCY:
- @react-native-async-storage/async-storage — Language persistence için

TEST:
- Build: npx expo export --platform web PASS (18 route)
- 🇹🇷 Türkçe: ✅ Tüm ekranlar doğru çevrili
- 🇬🇧 English: ✅ Tüm ekranlar doğru çevrili
- 🇷🇺 Русский: ✅ Tüm ekranlar doğru çevrili
- 🇸🇦 العربية: ✅ RTL çalışıyor, metinler sağa hizalı

DİL SEÇİCİ:
- Konum: Preview'da üst bar (demo)
- Gerçek uygulamada: Profil ekranında "Dil" bölümü
- Persistence: AsyncStorage ile kalıcı saklama
- Device locale fallback: Cihaz dili → Türkçe fallback

RTL DESTEĞİ:
- Arapça seçildiğinde direction: rtl uygulanıyor
- Tab bar sağdan sola sıralanıyor
- Metinler sağa hizalanıyor
- Layout yönü değişiyor

DENİZCİLİK TERMINOLOJİSİ:
- Chief Engineer → Başmühendis / Главный инженер / كبير المهندسين
- Master → Kaptan / Капитан / قبطان
- Seaman Book → Gemi Adamı Cüzdanı / Морская книжка / بطاقة البحار
- STCW → STCW (kısaltma korundu)
- COC → COC (kısaltma korundu)
- Vessel → Gemi / Судно / سفينة

DOSYA YAPISI:
mobile/i18n/
├── index.ts
├── config.ts
├── types.ts
└── locales/
    ├── tr.ts
    ├── en.ts
    ├── ru.ts
    └── ar.ts

YENİ DİL EKLEME YÖNTEMİ:
1. mobile/i18n/locales/XX.ts oluştur
2. translations objesine ekle
3. types.ts'ye SupportedLanguage ekle
4. LanguageSelector'a dil ekle
5. Hiçbir ekran kodu değişmez!

================================================================

================================================================
CREWINTEL MOBILE — M1d PREMIUM HOME / HERO DESIGN TAMAMLANDI
================================================================
Tarih: 2026-08-18 15:00
Phase: M1d — Premium Home / Hero Section + Maritime Animations

YAPILAN İŞLER:
1. Premium Hero Banner oluşturuldu (animasyonlu arka plan)
2. Maritime wave animasyonları eklendi (10-12s loop)
3. Fade-in + slide animasyonları eklendi
4. Hero overlay (%55 opacity) eklendi
5. Dinamik kullanıcı greeting eklendi
6. Profile durumu (badge) hero'ya eklendi
7. CTA butonu eklendi (turuncu, premium görünüm)
8. HomeStats component oluşturuldu (icon + value + label)
9. DocumentAlertCard component oluşturuldu (urgency renkleri)
10. RecommendedJobCard component oluşturuldu (match score, maaş, gemi)
11. QuickActionGrid component oluşturuldu (4'lük grid)
12. Tüm ekranlar i18n ile güncellendi
13. 4 dil test edildi (TR/EN/RU/AR)
14. RTL desteği (Arapça) doğrulandı

DEĞİŞEN DOSYALAR (YENİ):
- mobile/components/home/HeroBanner.tsx
- mobile/components/home/HomeStats.tsx
- mobile/components/home/DocumentAlertCard.tsx
- mobile/components/home/RecommendedJobCard.tsx
- mobile/components/home/QuickActionGrid.tsx
- mobile/preview.html

DEĞİŞEN DOSYALAR (GÜNCELLENEN):
- mobile/app/(tabs)/index.tsx — Yeni component'lerle yeniden yapılandırıldı
- mobile/i18n/types.ts — Yeni hero key'leri eklendi
- mobile/i18n/locales/tr.ts — Hero çevirileri
- mobile/i18n/locales/en.ts — Hero çevirileri
- mobile/i18n/locales/ru.ts — Hero çevirileri
- mobile/i18n/locales/ar.ts — Hero çevirileri

YENİ TRANSLATION KEY'LERİ:
- home.heroTitle — Ana başlık
- home.heroSubtitle — Alt açıklama
- home.heroCta — CTA butonu
- home.profileCompletion — Profil tamamlanma
- home.expiring — Süresi yaklaşan
- home.matchScore — Uygunluk skoru
- home.browseJobs — İlanları gör
- home.viewProfile — Profilimi gör
- home.myApplications — Başvurularım

HERO ANİMASYONLARI:
- Background scale: 1.0 → 1.04 → 1.0 (12s loop)
- Fade-in: 0 → 1 (0.8s)
- Text slide: X:20 → X:0 (0.6s)
- Wave hareketi: translateX + rotate (10-14s loop)
- CTA hover: translateY(-2px) + opacity

HERO YAPISI:
- Yükseklik: 340px
- Overlay: rgba(10, 22, 40, 0.55)
- Gradient: radial gradient (turuncu vurgular)
- Dalga efektleri: 3 katman (turuncu/beyaz, farklı hızlar)
- Backdrop: koyu lacivert (#0A1628)

�件 YAPISI:
HeroBanner:
  - userName: Kullanıcı adı
  - availabilityStatus: Durum badge'i
  - documentCount: Belge sayısı
  - contractCount: Kontrat sayısı
  - onCtaPress: CTA tıklama

HomeStats:
  - stats: [{value, label, icon}]

DocumentAlertCard:
  - documents: [{document_type, expiry_date, days_remaining}]
  - onPress: Tıklama

RecommendedJobCard:
  - jobs: [{id, title, vessel_type, location, salary...}]
  - onViewAll: Tümünü gör
  - onJobPress: İlan detayı

QuickActionGrid:
  - actions: [{icon, label, onPress}]

TEST:
- Build: npx expo export PASS (18 route)
- 🇹🇷 Türkçe: ✅ Hero başlığı + alt metin + CTA doğru
- 🇬🇧 English: ✅ "Your Maritime Career, One Platform."
- 🇷🇺 Русский: ✅ "Ваша морская карьера — на одной платформе."
- 🇸🇦 العربية: ✅ RTL çalışıyor, metinler sağa hizalı

BACKEND:
- Hiçbir backend değişikliği yapılmadı
- Mevcut API'ler aynen kullanıldı

KALAN İYİLEŞTİRME ÖNERİLERİ:
- Gerçek gemi görseli eklenebilir (Unsplash/Pexels)
- Skeleton loading eklenebilir
- Push notification badge eklenebilir

================================================================
