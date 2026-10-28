# CREWINTEL geliştirme kurulumu

CREWINTEL; FastAPI backend, React/Vite frontend ve PostgreSQL veritabanından oluşur.
Bu doküman Aşama 1 altyapısını yerelde veya Docker ile çalıştırma adımlarını içerir.

## Gereksinimler

- Python 3.13
- Node.js 24 (Node.js 20.19+ da Vite gereksinimini karşılar)
- Docker Desktop ve Docker Compose (Docker ile çalışma için)
- Yerel çalıştırmada PostgreSQL 17 veya Compose ile başlatılmış PostgreSQL

## Environment kurulumu

Şablon dosyaları gizli değer içermez; gerçek `.env` dosyaları Git tarafından yok sayılır.

PowerShell ile kökte Docker değişkenleri için:

```powershell
Copy-Item .env.example .env
```

`backend` klasöründe yerel API için:

```powershell
Copy-Item .env.example .env
```

Bu komutu `backend` klasöründe çalıştırın ve `DATABASE_URL` içindeki parola yer tutucusunu kendi yerel PostgreSQL parolanızla değiştirin.

Frontend için isteğe bağlı olarak `frontend/.env.example` dosyasını `frontend/.env.local` adına kopyalayın. `VITE_API_URL`, varsayılan olarak `http://127.0.0.1:8000` değerini kullanır.

## Yerel PostgreSQL

Kök dizinde `.env` oluşturduktan sonra sadece veritabanını başlatmak için:

```powershell
docker compose up -d postgres
```

Yerel backend için `backend/.env` içindeki `DATABASE_URL` hostu `127.0.0.1`, portu `5433` olmalıdır.

## Backend çalıştırma

```powershell
Set-Location backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
python -m app.run
```

`BACKEND_HOST` ve `BACKEND_PORT` değerleri `backend/.env` dosyasından okunur. Geliştirme sırasında otomatik yeniden yükleme istenirse aynı environment ile `uvicorn app.main:app --reload` komutu kullanılabilir.

API sağlık uçları:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/health/database`

`/health` API işlemini; `/health/database` ise ayrıca PostgreSQL bağlantısını denetler.

## Frontend çalıştırma

Yeni bir terminalde:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Vite varsayılan olarak `http://localhost:5173` adresinde açılır. Backend CORS ayarları bu origin ile `http://127.0.0.1:5173` için varsayılan izin sağlar.

## Migration çalıştırma

Migration komutları `backend` klasöründe ve geçerli `DATABASE_URL` ile çalıştırılır:

```powershell
Set-Location backend
alembic upgrade head
alembic current
```

İlk migration, `crew_members` tablosu zaten varsa onu silmez veya yeniden oluşturmaz. Mevcut tabloyu Alembic altında işaretlemek için önce yedek alın, ardından yalnızca tablo şeması uygunsa `alembic stamp head` kullanın.

İkinci migration; mevcut personel tablosunu yeni profil alanlarıyla genişletir ve `users`, `ships`, `ship_crew_assignments`, `contracts` tablolarını ekler. Migration geri alma komutu veri kaybını önlemek için tablo silmez.

## Çekirdek API uçları

Tüm CRUD uçları JSON kullanır ve FastAPI doğrulama hatalarında `422`, bulunamayan kayıtlarda `404` döner.

| Kaynak | Uçlar |
| --- | --- |
| Personel | `GET/POST /api/crew/`, `GET/PUT/DELETE /api/crew/{id}` |
| Gemiler | `GET/POST /api/ships/`, `GET/PUT/DELETE /api/ships/{id}` |
| Atamalar | `GET/POST /api/assignments/`, `GET/PUT/DELETE /api/assignments/{id}` |
| Kontratlar | `GET/POST /api/contracts/`, `GET/PUT/DELETE /api/contracts/{id}` |

Personel listeleme; `name`, `surname`, `position`, `nationality`, `status`, `ship_id`, `rank`, `languages`, `experience_years_min`, `sea_service_months_min`, `contract_status`, `contract_expiring_days`, `has_no_documents`, `show_problematic`, `offset` ve `limit` sorgu parametrelerini destekler. `limit` en fazla 200'dür.

## Docker ile çalıştırma

Kök dizinde `.env.example` dosyasını `.env` olarak kopyalayıp gerçek bir yerel geliştirme parolası tanımlayın. Sonra:

```powershell
docker compose up --build
```

Docker ağı içinde backend, PostgreSQL’e `postgres:5432` üzerinden bağlanır. Tarayıcıdan frontend `http://localhost:5173`, API `http://127.0.0.1:8000` adresindedir.

Konfigürasyonu konteyner başlatmadan doğrulamak için:

```powershell
docker compose --env-file .env.example config
```

## Test çalıştırma

Testler geçici, bellek içi SQLite veritabanı kullanır; yerel PostgreSQL gerektirmez.

```powershell
Set-Location backend
pytest ..\tests
```

## Frontend derleme

```powershell
Set-Location frontend
npm run build
```
