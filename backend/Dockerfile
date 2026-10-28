FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Belge işleme için sistem paketleri:
#   tesseract-ocr      → resim/taranmış PDF OCR (TR/EN/RU/AR/DE/FR)
#   poppler-utils      → pdf2image (taranmış PDF sayfalarını resme çevirme)
#   libreoffice        → eski .doc/.xls/.odt belgelerini PDF'e çevirme
#   fonts-liberation   → dönüştürülen PDF'lerde Türkçe/Kiril karakterler
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng tesseract-ocr-tur tesseract-ocr-rus \
        tesseract-ocr-ara tesseract-ocr-deu tesseract-ocr-fra \
        poppler-utils \
        libreoffice-writer-nogui libreoffice-calc-nogui \
        fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m app.run"]
