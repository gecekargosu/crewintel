FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ffmpeg: social downloader · tesseract: resimden OCR · libreoffice: doc/docx/xlsx -> PDF
# poppler-utils: pdftotext (taramalı PDF kontrolü) · fonts: LibreOffice output
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-tur \
        libreoffice-writer libreoffice-calc \
        poppler-utils fonts-liberation \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m app.run"]
