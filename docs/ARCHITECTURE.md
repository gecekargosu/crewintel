# CREWINTEL mimarisi

CREWINTEL, gemi personeli operasyonları için tek bir HTTP API ve iki istemci yüzeyi etrafında tasarlanmıştır. Mevcut teknoloji seçimi korunur: FastAPI, React/Vite ve PostgreSQL.

## Bileşenler

```text
React/Vite frontend  ──HTTP──>  FastAPI backend  ──SQLAlchemy/Alembic──> PostgreSQL
```

- **Frontend:** `frontend/` altında React ve Vite. API adresi `VITE_API_URL` ile belirlenir.
- **Backend:** `backend/app/` altında FastAPI route, Pydantic schema ve SQLAlchemy model katmanları bulunur.
- **Database:** PostgreSQL; yerel Docker portu `5433`, Docker ağı içindeki adı `postgres:5432`.
- **Migration:** `backend/alembic/`. Şema değişiklikleri yalnızca Alembic migration ile uygulanır.

## Çekirdek veri modeli

| Model | Amaç | Temel ilişkiler |
| --- | --- | --- |
| `users` | İlerideki giriş/yetkilendirme için kullanıcı altyapısı | `role`: admin, manager, hr, operator veya viewer için hazır alan |
| `ships` | Gemi envanteri | Atama ve kontratlarla bire-çoğa ilişki |
| `crew_members` | Personel özlük ve iletişim bilgileri | Atama ve kontratlarla bire-çoğa ilişki |
| `ship_crew_assignments` | Personel-gemi ataması | Bir gemi ve bir personele foreign key |
| `contracts` | Personel kontratları | Bir gemi ve bir personele foreign key |

`ships.imo_number`, `users.email` ve `contracts.contract_number` unique tanımlıdır. Atama ve kontrat foreign key alanlarında indeks bulunur. Mevcut aşamada kullanıcı kaydı authentication veya yetki kontrolü uygulamaz.

## Çalışma ortamları

- Yerel backend, `backend/.env` içindeki `DATABASE_URL` ile `127.0.0.1:5433` PostgreSQL adresine bağlanır.
- Docker Compose backend’i bağlantıyı `postgres:5432` üzerinden kurar.
- CORS origin’leri `CORS_ORIGINS` ile merkezi olarak yönetilir.
- Gerçek parolalar `.env` dosyalarında bulunur ve Git’e eklenmez; yalnızca güvenli yer tutucular içeren `.env.example` dosyaları izlenir.
