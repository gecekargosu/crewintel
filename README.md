# CREWINTEL

**Gemi Personeli & İnsan Kaynakları Yönetim Sistemi** — personel özlük, gemi
atamaları, kontratlar, OCR destekli belge arşivi ve belge→personel otomatik
eşleştirme, geçerlilik takibi, iş ilanları ve portal, AI modülleri.

| | |
|---|---|
| Backend | FastAPI + SQLAlchemy/Alembic + PostgreSQL (`backend/`, port 8000) |
| Frontend | React + Vite, 4 dil (`frontend/`, port 5173) |
| Mobil | Android/Kotlin (`mobile-app/`) |
| Servisler | `docker-compose.yml`: postgres, backend, frontend (+ social-downloader, umay-agent) |
| Test | `backend/.venv/Scripts/python -m pytest tests/ -q` → **284 passed / 2 skipped** |
| GitHub | https://github.com/gecekargosu/crewintel |

## Hızlı başlangıç

```bash
docker compose up -d                      # servisleri başlat
docker compose build frontend && docker compose up -d frontend   # arayüz değişince
```

- Web arayüzü: `http://localhost:5173` · API: `http://localhost:8000`
- Giriş: `backend/.env` / seed kayıtlarındaki admin hesabı (repoda tutulmaz).

## Dokümantasyon

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — sistem mimarisi, yükleme hattı, match motoru
- [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md) — proje belleği + CHANGELOG
- [docs/DUZELTME_LISTESI_UPLOAD.md](docs/DUZELTME_LISTESI_UPLOAD.md) — H1–H14 hata/düzeltme listesi
- [CLAUDE.md](CLAUDE.md) — AI/yeni geliştirici giriş rehberi (komutlar, sınırlar, tuzaklar)

## Öne çıkanlar

- **18 formatlı yükleme**: PDF, Word, Excel, resimler; iç içe klasör sürükle-bırak.
- **Otomatik PDF dönüşümü**: ofis → LibreOffice, resim → Pillow, txt → fpdf2.
- **OCR**: tesseract (eng+tur) resimler ve taramalı PDF'ler için.
- **Eşleştirme motoru**: güçlü identifier + isim + dosya adı + metin içi tam isim
  sinyalleri; GERMAN SKY 187 belgede 58 otomatik eşleşme.
- **Limit**: yükleme 100MB (istemci, backend, nginx, compose, installer — hepsi eşit).
