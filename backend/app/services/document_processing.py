"""Belge işleme yardımcıları (metin çıkarma + alan çıkarımı + eşleştirme).

Desteklenen formatlar:
    PDF (metin katmanlı, taranmış -> OCR), TXT/CSV, DOCX, XLSX, ODT/ODS/RTF,
    DOC/XLS (LibreOffice), JPEG/PNG/WebP/TIFF/BMP (OCR).

Tasarım notları:
- Metin çıkarma hiçbir zaman sessizce boş dönmez; okunamayan dosyada
  `[ ... ]` biçiminde açıklayıcı bir işaret döner. Çağıran taraf bunu
  `extraction_error` olarak kaydeder.
- OCR dili kurulu tesseract dillerine göre seçilir (Türkçe/Rusça/Arapça
  pasaportlar için önemli).
- Alan çıkarımı yalnızca belgede YAZANI döndürür; tahmin üretmez.
"""
import hashlib
import re
import unicodedata
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.crew_member import CrewMember
from app.services.mrz import parse_mrz

# ── Desteklenen formatlar ────────────────────────────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".bmp", ".tiff", ".tif"}
OFFICE_EXTENSIONS = {".doc", ".docx", ".odt", ".rtf", ".xlsx", ".xls", ".ods", ".csv"}
PDF_CONVERTIBLE_EXTENSIONS = IMAGE_EXTENSIONS | OFFICE_EXTENSIONS | {".txt", ".pdf"}

# OCR için tercih edilen diller (kurulu olanlar kullanılır).
OCR_PREFERRED_LANGUAGES = ("tur", "eng", "rus", "ara", "deu", "fra")


def normalize(value: str | None) -> str:
    """İsim/alan normalizasyonu: Türkçe karakterleri ASCII'ye indirger.

    NFKD ç/ğ/ö/ş/ü çözer ama dotless-ı (U+0131) ve dotted-İ (U+0130) çözülmez;
    elle eşlenir ki "Yılmaz" ile "Yilmaz" aynı token üretsin.
    """
    if not value:
        return ""
    value = value.replace("ı", "i").replace("İ", "i").replace("I", "i")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


# ── Metin çıkarma: yardımcılar ───────────────────────────────────────────────

def _extract_docx(content: bytes) -> str:
    """DOCX: paragraf + tablo metinlerini çıkarır."""
    import io

    from docx import Document

    try:
        doc = Document(io.BytesIO(content))
        parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception:
        return ""


def _extract_xlsx(content: bytes) -> str:
    """XLSX: tüm hücre değerlerini satır satır çıkarır."""
    import io

    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        parts: list[str] = []
        for ws in wb.worksheets:
            parts.append(f"[{ws.title}]")
            for row in ws.iter_rows(values_only=True):
                values = [str(v).strip() for v in row if v is not None and str(v).strip()]
                if values:
                    parts.append(" | ".join(values))
        return "\n".join(parts)
    except Exception:
        return ""


def _ocr_languages() -> str:
    """Kurulu tesseract dillerinden OCR dil zinciri üretir."""
    try:
        import pytesseract

        available = set(pytesseract.get_languages(config=""))
    except Exception:
        return "eng"
    selected = [lang for lang in OCR_PREFERRED_LANGUAGES if lang in available]
    if not selected:
        return "eng" if "eng" in available else (next(iter(available)) if available else "eng")
    return "+".join(selected)


def _ocr_image(content: bytes) -> str:
    """Resimden metin okur (tesseract). Kurulu değilse boş döner."""
    import io

    from PIL import Image

    try:
        import pytesseract

        img = Image.open(io.BytesIO(content))
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        if img.mode != "L":
            img = img.convert("L")
        # Küçük görseller (telefonla çekilmiş pasaport kırpmaları) büyütülür;
        # tesseract 300 DPI civarında en iyi sonucu verir.
        if img.width < 2400:
            ratio = 2400 / img.width
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
        return pytesseract.image_to_string(img, lang=_ocr_languages(), config="--psm 3")
    except Exception:
        return ""


def _ocr_pdf_pages(content: bytes, max_pages: int = 5) -> str:
    """Taramalı PDF'i sayfa resimlerine çevirip OCR uygular.

    pdf2image/poppler kurulu değilse boş döner.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        from PIL import Image

        pages = convert_from_bytes(content, dpi=200, last_page=max_pages)
        lang = _ocr_languages()
        texts = []
        for page in pages:
            if not isinstance(page, Image.Image):
                continue
            texts.append(pytesseract.image_to_string(page.convert("L"), lang=lang))
        return "\n".join(texts)
    except Exception:
        return ""


def _soffice_convert(content: bytes, source_name: str, target: str) -> bytes | None:
    """LibreOffice headless ile dosyayı dönüştürür (target: 'pdf').

    Tek instance kilidi olmaması için her çağrıya özel UserInstallation verilir.
    LibreOffice kurulu değilse None döner.
    """
    import shutil
    import subprocess
    import tempfile

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None

    suffix = Path(source_name).suffix.lower() or ".dat"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"input{suffix}"
        src.write_bytes(content)
        out_dir = Path(tmp) / "out"
        out_dir.mkdir()
        profile = Path(tmp) / "profile"
        try:
            subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--norestore",
                    f"-env:UserInstallation=file://{profile}",
                    "--convert-to",
                    target,
                    "--outdir",
                    str(out_dir),
                    str(src),
                ],
                check=True,
                capture_output=True,
                timeout=90,
            )
        except Exception:
            return None
        produced = sorted(out_dir.glob(f"*.{target}"))
        if not produced:
            return None
        return produced[0].read_bytes()


def _image_to_pdf(content: bytes) -> bytes | None:
    """Resmi A4 dikey sayfaya yerleştirip PDF yapar."""
    import io

    from PIL import Image

    try:
        img = Image.open(io.BytesIO(content))
        if img.mode not in ("L", "RGB", "RGBA"):
            img = img.convert("RGB")
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        max_w, max_h = 595 - 24, 842 - 24
        ratio = min(max_w / img.width, max_h / img.height)
        new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
        img = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PDF", resolution=150)
        return buf.getvalue()
    except Exception:
        return None


def _find_ttf_font() -> str | None:
    """Türkçe/Kiril destekli bir TTF font yolu bulur (fpdf2 için)."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    return None


def _text_to_pdf(title: str, text: str) -> bytes:
    """Düz metni PDF'e çevirir. Türkçe font bulunamazsa latin-1'e düşer."""
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    font_path = _find_ttf_font()
    if font_path:
        pdf.add_font("body", "", font_path)
        pdf.set_font("body", size=11)
    else:
        pdf.set_font("helvetica", size=11)
        text = text.encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 6, text[:200000])
    return bytes(pdf.output())


def convert_to_pdf(filename: str, content: bytes) -> tuple[bytes | None, str]:
    """Desteklenen herhangi bir belgeyi PDF'e çevirir.

    Returns:
        (pdf_bytes, error) — başarılıysa error boş.
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return content, ""

    if suffix in IMAGE_EXTENSIONS:
        pdf = _image_to_pdf(content)
        if pdf:
            return pdf, ""
        return None, "Resim PDF'e çevrilemedi."

    if suffix in OFFICE_EXTENSIONS:
        pdf = _soffice_convert(content, filename, "pdf")
        if pdf:
            return pdf, ""
        # Fallback: metin çıkarıp basit PDF üret
        text = extract_text(filename, content)
        if text and not (text.startswith("[") and text.endswith("]")):
            try:
                return _text_to_pdf(filename, text), ""
            except Exception:
                pass
        return None, "LibreOffice dönüştürme başarısız."

    if suffix == ".txt":
        try:
            return _text_to_pdf(filename, content.decode("utf-8", errors="replace")), ""
        except Exception:
            return None, "Metin PDF'e çevrilemedi."

    return None, f"Desteklenmeyen format: {suffix}"


def extract_text(filename: str, content: bytes) -> str:
    """Genel metin çıkarma girişi (tüm formatlar).

    NUL (0x00) byte'ları temizlenir: OCR/ofis çıktısı veya bozuk PDF'ten
    gelen NUL, PostgreSQL text alanlarında `DataError` ile 500 üretiyordu.
    """
    try:
        text = _extract_text_raw(filename, content)
    except Exception:
        return ""
    return text.replace("\x00", "") if isinstance(text, str) else ""


def _extract_text_raw(filename: str, content: bytes) -> str:
    """Dosya içinden metin çıkarır (format bazlı)."""
    lower = filename.lower()

    if lower.endswith((".txt", ".csv")):
        return content.decode("utf-8", errors="replace")

    if lower.endswith(".docx"):
        return _extract_docx(content) or "[DOCX okunamadı]"

    if lower.endswith((".xlsx", ".xlsm")):
        return _extract_xlsx(content) or "[XLSX okunamadı]"

    if Path(lower).suffix in IMAGE_EXTENSIONS:
        return _ocr_image(content) or "[resim — OCR metin çıkaramadı]"

    if lower.endswith(".pdf"):
        import io

        try:
            reader = PdfReader(io.BytesIO(content))

            if reader.is_encrypted:
                try:
                    reader.decrypt("")  # boş şifre ile dene
                except Exception:
                    return "[şifreli PDF — metin çıkarılamadı]"

            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)

            full_text = "\n".join(pages_text)

            # Taramalı PDF (metin yok, sadece resim) → OCR dene
            if not full_text.strip():
                ocr_text = _ocr_pdf_pages(content)
                if ocr_text.strip():
                    return ocr_text
                return "[taramalı PDF — metin katmanı yok, OCR gerekli]"

            return full_text
        except Exception:
            return "[PDF okunamadı — bozuk veya desteklenmeyen format]"

    if Path(lower).suffix in OFFICE_EXTENSIONS:
        # Eski .doc / .xls / .odt: LibreOffice ile PDF yapıp metin çıkar
        pdf_bytes = _soffice_convert(content, filename, "pdf")
        if pdf_bytes:
            text = extract_text("converted.pdf", pdf_bytes)
            if text and not text.startswith("["):
                return text
        text = _extract_docx(content) if "doc" in lower else ""
        return text or "[ofis belgesi okunamadı — LibreOffice gerekli]"

    return ""


# ── Tarih ayrıştırma ─────────────────────────────────────────────────────────

TURKISH_MONTHS = {
    "ocak": "january", "şubat": "february", "subat": "february",
    "mart": "march", "nisan": "april", "mayıs": "may", "mayis": "may",
    "haziran": "june", "temmuz": "july", "ağustos": "august", "agustos": "august",
    "eylül": "september", "eylul": "september", "ekim": "october",
    "kasım": "november", "kasim": "november", "aralık": "december", "aralik": "december",
}

# Rus / Alman / Fransız / İspanyol ay adları: bu dillerdeki belgelerde tarih
# "12 МАР 2020", "12. März 2020" gibi yazılabiliyor.
_FOREIGN_MONTHS = {
    # Rusça (tam + kısaltma)
    "января": "january", "январь": "january", "янв": "january",
    "февраля": "february", "февраль": "february", "фев": "february",
    "марта": "march", "март": "march", "мар": "march",
    "апреля": "april", "апрель": "april", "апр": "april",
    "мая": "may", "май": "may",
    "июня": "june", "июнь": "june", "июн": "june",
    "июля": "july", "июль": "july", "июл": "july",
    "августа": "august", "август": "august", "авг": "august",
    "сентября": "september", "сентябрь": "september", "сен": "september",
    "октября": "october", "октябрь": "october", "окт": "october",
    "ноября": "november", "ноябрь": "november", "ноя": "november",
    "декабря": "december", "декабрь": "december", "дек": "december",
    # Almanca
    "januar": "january", "februar": "february", "märz": "march", "maerz": "march",
    "mai": "may", "juni": "june", "juli": "july", "oktober": "october",
    "dezember": "december",
    # Fransızca
    "janvier": "january", "février": "february", "fevrier": "february",
    "mars": "march", "avril": "april", "juin": "june", "juillet": "july",
    "août": "august", "aout": "august", "septembre": "september",
    "octobre": "october", "novembre": "november", "décembre": "december", "decembre": "december",
    # Arapça
    "يناير": "january", "فبراير": "february", "مارس": "march", "أبريل": "april",
    "ابريل": "april", "مايو": "may", "يونيو": "june", "يوليو": "july",
    "أغسطس": "august", "اغسطس": "august", "سبتمبر": "september",
    "أكتوبر": "october", "اكتوبر": "october", "نوفمبر": "november",
    "ديسمبر": "december",
}

_MONTH_NAME_PATTERN = (
    r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
    r"|ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos"
    r"|eylül|eylul|ekim|kasım|kasim|aralık|aralik"
    r"|янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек"
    r"|января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"
    r"|januar|februar|märz|maerz|juni|juli|oktober|dezember"
    r"|janvier|février|fevrier|avril|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre"
    r"|يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر"
)

_DATE_FORMATS = (
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d %b %Y",
    "%b %d %Y",
    "%d %B %Y",
    "%B %d %Y",
    "%Y %b %d",
    "%d.%m.%y",
    "%d/%m/%y",
)

# Tüm diller tek sözlükte: sıralı `replace` zinciri "ocak" → "january" →
# "januaryy" gibi bozuk çıktı üretiyordu. Tek geçişli regex ile değiştirilir.
_MONTH_LOOKUP = {**_FOREIGN_MONTHS, **TURKISH_MONTHS}
_MONTH_REGEX = re.compile(
    r"\b(" + "|".join(
        sorted((re.escape(name) for name in _MONTH_LOOKUP), key=len, reverse=True)
    ) + r")\b",
    re.IGNORECASE,
)


def _normalize_month_names(value: str) -> str:
    """Ay adlarını İngilizceye çevirir (TR + RU + DE + FR + AR)."""
    return _MONTH_REGEX.sub(lambda match: _MONTH_LOOKUP[match.group(1).lower()], value)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None

    candidate = _normalize_month_names(re.sub(r"[,;]", "", value.strip()))
    # "12. März 2024" / "12. март 2024" → gün numarasından sonraki nokta
    # kaldırılır, aksi halde ay adlı biçimler eşleşmez.
    candidate = re.sub(r"(\d{1,2})\s*\.\s*([^\W\d_])", r"\1 \2", candidate, count=1)

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue

    return None


def _extract_labeled_date(
    text: str,
    labels: list[str],
) -> date | None:
    # Longer labels first so e.g. "expiration date" wins over "expiry".
    ordered_labels = sorted(labels, key=len, reverse=True)
    label_pattern = "|".join(re.escape(label) for label in ordered_labels)

    date_token = (
        r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
        rf"|\d{{4}}[./-]\d{{1,2}}[./-]\d{{1,2}}"
        rf"|\d{{1,2}}\s+(?:{_MONTH_NAME_PATTERN})\.?\s*\d{{2,4}}"
        rf"|(?:{_MONTH_NAME_PATTERN})\.?\s+\d{{1,2}},?\s*\d{{2,4}}"
    )

    # Ayırıcı olarak "." de kabul edilir: OCR bazen "Date of Expiry. 17/08/2026"
    # üretiyor; etiketin hemen ardındaki tek nokta/çift nokta zararsızdır.
    match = re.search(
        rf"(?:{label_pattern})\s*[:#.-]{{0,2}}\s*"
        rf"({date_token})",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    raw = re.sub(r"[,;]", "", match.group(1))
    return parse_date(raw)


# ── Belge tipi sınıflandırma ─────────────────────────────────────────────────

# Belge tipi anahtar kelimeleri. Sıra, eşit skorda öncelik anlamına gelir.
DOCUMENT_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "seaman_book": (
        "seaman book",
        "seaman s book",
        "seamans book",
        "gemiadami cuzdani",
        "gemi adami cuzdani",
        "identity and sea service record book",
    ),
    "passport": ("passport", "pasaport", "паспорт", "reisepass", "passeport", "جواز سفر"),
    "stcw": ("stcw",),
    "goc": ("goc",),
    "medical": (
        "eng1",
        "medical certificate",
        "medical fitness",
        "health certificate",
        "medical",
        "medikal",
        "sağlık raporu",
        "saglik raporu",
    ),
    "contract": ("contract", "sozlesme", "sözleşme", "employment agreement", "контракт"),
    "cv": ("curriculum vitae", "resume", "cv", "özgeçmiş", "ozgecmis"),
}


def _keyword_hits(haystack: str, keyword: str) -> bool:
    """Kısa anahtar kelimelerde (cv, goc…) kelime sınırı arar."""
    if len(keyword) <= 3:
        return re.search(rf"\b{re.escape(keyword)}\b", haystack) is not None
    return keyword in haystack


def classify_document_type(filename: str, text: str) -> str:
    """Belge tipini ağırlıklı skorla belirler.

    Eski davranış ilk eşleşen anahtar kelimeyi seçiyordu; bu yüzden içinde
    "Passport: ..." alanı bulunan bir SAĞLIK belgesi "passport" olarak
    sınıflandırılıyordu. Artık başlık bölgesi (ilk 3 dolu satır), dosya adı ve
    gövde ayrı ağırlıklarla puanlanır, uzun (daha spesifik) anahtar kelimeler
    daha yüksek puan alır ve en yüksek skorlu tip kazanır.

    Dosya adı en güçlü sinyaldir: bir CV gövdesinde "Medical Fitness
    Certificate" gibi satırlar geçebilir, bu belgeyi sağlık raporu yapmaz.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    header = normalize("\n".join(lines[:3]))
    stem = normalize(Path(filename).stem)
    body = normalize(f"{filename}\n{text}")

    # OCR bazen kelimeleri birleştirir ("MEDICAL FITNESSCERTIFICATE");
    # boşluksuz karşılaştırma bu durumda da anahtar kelimeyi yakalar.
    header_compact = header.replace(" ", "")
    stem_compact = stem.replace(" ", "")
    body_compact = body.replace(" ", "")

    best_type = "other"
    best_score = 0.0
    for kind, words in DOCUMENT_TYPE_KEYWORDS.items():
        score = 0.0
        for word in words:
            keyword = normalize(word)
            if not keyword:
                continue
            compact = keyword.replace(" ", "")
            # Kısa anahtar kelimelerde (cv, goc) boşluksuz arama yanlış
            # eşleşme üretir; yalnızca 5+ karakterlik kelimelerde uygulanır.
            compact_hit = len(compact) >= 5
            weight = 1 + len(keyword) / 20
            if _keyword_hits(header, keyword) or (compact_hit and compact in header_compact):
                score += 3 * weight
            if _keyword_hits(stem, keyword) or (compact_hit and compact in stem_compact):
                score += 4 * weight
            elif _keyword_hits(body, keyword) or (compact_hit and compact in body_compact):
                score += weight
        if score > best_score:
            best_type, best_score = kind, score

    # Yalnızca gövdede geçen zayıf bir eşleşme (ör. CV içinde anılan
    # "contract") yanlış sınıflandırma riski taşır; en az 2 puan (bir başlık
    # veya dosya adı eşleşmesi) aranır.
    return best_type if best_score >= 2 else "other"


# Dosya adında isim olmayan kelimeler (belge tipi/ek ifadeler)
FILENAME_NOISE = {
    "passport", "pasaport", "stcw", "goc", "eng1", "cv",
    "crew", "medical", "contract", "seaman", "certificate",
    "fitness", "agreement", "resume", "new", "old", "copy",
    "final", "revised", "scan", "scanned", "document", "file",
    "certificates", "republic", "panama", "vessel", "ships",
    "employment", "word", "doc", "signed", "signature",
    "page", "img", "image", "pic", "photo", "pic1", "edit",
    "belge", "tarama", "kopya", "pasaportu", "cuzdan", "cuzdani",
}

# Metinden üretilen isim adaylarında gürültü kelimeleri.
# DİKKAT: gerçek ad/soyad olabilecek kelimeler (test, date, valid…)
# burada OLMAMALI — yanlış skip gerçek eşleşmeyi kırar (ör. soyad "Test").
NAME_NOISE = {
    "and", "the", "holder", "certificate", "employee", "employer",
    "ards", "certicate", "certifcate", "republic", "copy", "name",
    "medical", "contract", "passport", "seaman", "untitled",
    "belge", "ad", "soyad", "adı", "soyadı",
}


# ── Alan çıkarımı ────────────────────────────────────────────────────────────

def extract_metadata(filename: str, text: str) -> dict:
    combined = f"{filename}\n{text}"

    document_type = classify_document_type(filename, text)

    email = re.search(
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        combined,
    )

    # Identifier extraction: allow hyphens inside (AB-123456) or a single
    # space between groups (AB12 3456), but never spill into following words
    # (e.g. "AB123456 VALID UNTIL" must only capture the number) and never
    # capture the keyword itself ("Passport Number: ..." must not yield
    # "NUMBER"). Every captured value must contain at least one digit.
    def _extract_identifier(label_pattern: str) -> str | None:
        # Boşluklar satır içi ile sınırlıdır ([ \t]*): `\s*` yeni satırları da
        # yuttuğundan "PASSPORT\nPassport Number: X" gibi metinlerde ikinci
        # kelime identifier sanılabiliyordu.
        anchored = (
            rf"{label_pattern}"
            rf"[ \t]*(?:no|number|numarası|numarasi|номер)?"
            rf"[ \t]*[:#-]?[ \t]*"
        )
        # First: a compact token of letters/digits/hyphens (no spaces), e.g.
        # AB-123456 or AB123456. Iterate over candidates and keep the first
        # plausible one (contains a digit, 5-15 chars after stripping).
        for match in re.finditer(
            rf"{anchored}([A-Z0-9-]+)",
            combined,
            re.IGNORECASE,
        ):
            value = re.sub(r"[^A-Z0-9]", "", match.group(1).upper())
            if 5 <= len(value) <= 15 and any(char.isdigit() for char in value):
                return value
        # Second: two space-separated groups, e.g. "AB12 3456" veya
        # "51 2345678" (Rus pasaportu: seri + 7 haneli numara).
        for match in re.finditer(
            rf"{anchored}([A-Z0-9]{{2,6}}[ \t]\d{{2,10}})",
            combined,
            re.IGNORECASE,
        ):
            value = re.sub(r"[^A-Z0-9]", "", match.group(1).upper())
            if 5 <= len(value) <= 15:
                return value
        return None

    def _extract_mrz_number() -> str | None:
        """TD3 MRZ ikinci satırının ilk 9 karakteri belge numarasıdır.

        Bazı pasaport/kimlik belgelerinde numara yalnızca MRZ'de veya
        "Document Number" gibi genel bir etiketle geçer; bu yüzden MRZ'den
        okunan numara da kabul edilir.
        """
        for line in text.splitlines():
            candidate = line.strip().replace(" ", "")
            if len(candidate) < 30 or "<" not in candidate:
                continue
            if not re.fullmatch(r"[A-Z0-9<]{30,44}", candidate):
                continue
            value = candidate[:9].replace("<", "")
            if 5 <= len(value) <= 15 and any(char.isdigit() for char in value):
                return value
        return None

    passport = _extract_identifier(r"(?:passport|pasaport|паспорт|reisepass|passeport)")
    seaman = _extract_identifier(
        r"(?:seaman(?:'s)?\s*book|gemiadamı|gemiadami|gemi\s*adamı)"
    )

    # Pasaport/gemiadamı cüzdanı belgelerinde numara bazen yalnızca genel
    # "Document Number" etiketiyle veya yalnızca MRZ satırında yer alır.
    # Genel etiket yalnızca doğrulanmış belge tipinde kabul edilir; aksi
    # halde bir sözleşmenin "Contract Number" alanı pasaport numarası sanılır.
    if passport is None and document_type == "passport":
        passport = _extract_identifier(r"(?:document|belge)") or _extract_mrz_number()
    if seaman is None and document_type == "seaman_book":
        seaman = _extract_identifier(r"(?:document|belge)") or _extract_mrz_number()

    date_of_birth = _extract_labeled_date(
        combined,
        [
            "dob",
            "birth date",
            "date of birth",
            "doğum tarihi",
            "dogum tarihi",
            "дата рождения",
            "geburtsdatum",
            "date de naissance",
        ],
    )

    issue_date = _extract_labeled_date(
        combined,
        [
            "issue date",
            "date of issue",
            "veriliş tarihi",
            "verilis tarihi",
            "дата выдачи",
            "ausstellungsdatum",
            "date de délivrance",
            "date de delivrance",
            "مكتب الإصدار",
        ],
    )

    expiry_date = _extract_labeled_date(
        combined,
        [
            "expiry date",
            "expiration date",
            "date of expiry",
            "valid until",
            "valid to",
            "validity date",
            "validity",
            "expiry",
            "expires",
            "bitiş",
            "bitis",
            "son geçerlilik tarihi",
            "son gecerlilik tarihi",
            "son geçerlilik",
            "son gecerlilik",
            "geçerlilik tarihi",
            "gecerlilik tarihi",
            "geçerlilik",
            "gecerlilik",
            "действует до",
            "действителен до",
            "срок действия",
            "gültig bis",
            "valable jusqu",
            "scadenza",
            "fecha de caducidad",
            "fecha de vencimiento",
            "geldig tot",
            "تاريخ الانتهاء",
            "有效期",
        ],
    )

    # MRZ (pasaport altındaki iki satır) belgenin dilinden bağımsızdır.
    # Etiketli alanlar okunamadığında (Arapça/Rusça taranmış pasaportlar)
    # numara, doğum ve son geçerlilik tarihi buradan tamamlanır. Değerler
    # yalnızca ICAO kontrol basamağı tuttuğunda kabul edilir (bkz. mrz.py).
    mrz = parse_mrz(text)
    nationality = None
    if mrz is not None:
        nationality = mrz.nationality
        if passport is None and document_type in {"passport", "seaman_book"}:
            passport = mrz.document_number
        if date_of_birth is None:
            date_of_birth = mrz.date_of_birth
        if expiry_date is None:
            expiry_date = mrz.expiry_date

    # Sadece etiketsiz ("12.03.2024" tek başına) tarih var ama etiket yoksa
    # uydurmuyoruz: alanları boş bırakıyoruz.

    # Denizcilikle ilgililik: belge personel dosyasına ait mi?
    maritime_keywords = [
        "maritime", "vessel", "ship", "crew", "officer", "captain",
        "engineer", "sailor", "port", "voyage", "seaman", "stcw",
        "gemi", "deniz", "denizcilik", "personel", "mürettebat",
        "sefer", "liman", "kaptan", "başmühendis", "gemici",
        "çarkçı", "makine", "ustabaşı", "naval", "merchant", "tonnage",
        "hull", "bridge", "судно", "моряк", "экипаж",
    ]
    text_lower = f"{filename} {text}".lower()
    maritime_hits = sum(1 for kw in maritime_keywords if kw in text_lower)
    if document_type in {"cv", "passport", "seaman_book", "stcw", "goc", "medical", "contract"}:
        maritime_relevance = "high"
    elif maritime_hits >= 2:
        maritime_relevance = "high"
    elif maritime_hits == 1:
        maritime_relevance = "medium"
    else:
        maritime_relevance = "low"

    return {
        "email": email.group(0).lower() if email else None,
        "passport_number": passport,
        "seaman_book_number": seaman,
        "date_of_birth": date_of_birth,
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "document_type": document_type,
        "filename": filename,
        "nationality": nationality,
        "maritime_relevance": maritime_relevance,
    }


# ── İsim çıkarma ─────────────────────────────────────────────────────────────

def extract_name(
    filename: str,
    text: str,
) -> tuple[str | None, str | None]:
    combined = f"{filename}\n{text}"

    # 0) Türkçe formatlar:
    #    a) "Adı Soyadı: Ahmet Yılmaz" (birleşik etiket, tek satır)
    tr_combined = re.search(
        r"\bad[ıi]\s+soyad[ıi]\s*[:#-]\s*"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]{2,})\s+([A-Za-zÇĞİÖŞÜçğıöşü]{2,})",
        combined, re.IGNORECASE,
    )
    if tr_combined:
        return (tr_combined.group(1).title(), tr_combined.group(2).title())
    #    b) Farklı satırlarda: Adı: X / Soyadı: Y
    tr_ad2 = re.search(r"\bad[ıi]\s*[:#-]\s*([A-Za-zÇĞİÖŞÜçğıöşü]{2,})", combined, re.IGNORECASE)
    tr_soy2 = re.search(r"\bsoyad[ıi]\s*[:#-]\s*([A-Za-zÇĞİÖŞÜçğıöşü]{2,})", combined, re.IGNORECASE)
    if tr_ad2 and tr_soy2:
        return (tr_ad2.group(1).title(), tr_soy2.group(1).title())

    # 1) Rus pasaportu: "Surname: X" + "Given Names: Y" — en öncelikli
    surname_m = re.search(r"Surname:\s*([A-Za-zÇĞİÖŞÜçğıöşü]+)", combined, re.IGNORECASE)
    given_m = re.search(r"Given\s+Names?:\s*([A-Za-zÇĞİÖŞÜçğıöşü]+)", combined, re.IGNORECASE)
    if surname_m and given_m:
        return (given_m.group(1).title(), surname_m.group(1).title())

    # 2) Genel Name/Holder/And pattern
    match = re.search(
        r"(?<!\bCompany )"
        r"(?:name|adı soyadı|adi soyadi|ad soyad|full name|holder|certificate holder|and)"
        r"\s*[:#-]?\s*"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)"
        r"\s+"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)",
        combined,
        re.IGNORECASE,
    )

    # Dosya adı tabanlı aday (tüm anlamlı parçalar: "AHMED SABRY KAMAL ELHENAWY")
    fn_parts = [
        part
        for part in re.split(r"[_\-\s]+", Path(filename).stem)
        if len(part) > 2
        and part.lower() not in FILENAME_NOISE
    ]
    fn_candidate = (" ".join(fn_parts[:-1]), fn_parts[-1]) if len(fn_parts) >= 2 else None

    if match:
        first = match.group(1).title()
        last = match.group(2).title()
        if first.lower() in NAME_NOISE or last.lower() in NAME_NOISE:
            after = combined[match.end():].strip()
            next_m = re.match(r"([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)", after)
            if next_m and next_m.group(1).lower() not in NAME_NOISE and next_m.group(2).lower() not in NAME_NOISE:
                first, last = next_m.group(1).title(), next_m.group(2).title()
            elif fn_candidate:
                # Text gürültüsü — dosya adındaki gerçek isme düş.
                return fn_candidate[0].title(), fn_candidate[1].title()

        # Doğrulama: text adayı dosya adıyla desteklenmiyorsa gürültidir
        # (ör. "Ards Certicate" — "certificate" etiketinden üretilmiş sahte isim).
        if fn_candidate:
            fn_norm = normalize(" ".join(fn_parts))
            words = {word for word in normalize(f"{first} {last}").split() if len(word) > 2}
            if words and not any(word in fn_norm for word in words):
                return fn_candidate[0].title(), fn_candidate[1].title()

        return (first, last)

    if fn_candidate:
        return fn_candidate[0].title(), fn_candidate[1].title()

    # Son çare: MRZ'deki ad/soyad (Latin harfli, dil bağımsız).
    mrz = parse_mrz(text)
    if mrz and mrz.surname:
        return mrz.given_names, mrz.surname.title()

    return None, None


def normalize_identifier(value: str | None) -> str:
    """Compact identifier form: alphanumerics only, uppercased.

    Makes "AB-123456", "AB12 3456" and "ab123456" compare equal.
    """
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def match_crew(
    session: Session,
    filename: str,
    text: str,
    metadata: dict,
) -> tuple[CrewMember | None, str, int]:
    first_name, last_name = extract_name(filename, text)

    candidates = session.query(CrewMember).all()
    scored = []

    for crew in candidates:
        score = 0

        if metadata.get("passport_number") and crew.passport_number:
            if normalize_identifier(metadata["passport_number"]) != normalize_identifier(
                crew.passport_number
            ):
                continue
            score += 100

        if (
            metadata.get("seaman_book_number")
            and crew.seaman_book_number
        ):
            if normalize_identifier(metadata["seaman_book_number"]) != normalize_identifier(
                crew.seaman_book_number
            ):
                continue
            score += 100

        if metadata.get("email") and crew.email:
            if normalize(metadata["email"]) == normalize(crew.email):
                score += 70

        if first_name and last_name:
            first_similarity = SequenceMatcher(
                None,
                normalize(first_name),
                normalize(crew.first_name),
            ).ratio()

            last_similarity = SequenceMatcher(
                None,
                normalize(last_name),
                normalize(crew.last_name),
            ).ratio()

            similarity = (
                first_similarity + last_similarity
            ) / 2

            if similarity >= 0.999:
                score += 95
            elif similarity >= 0.98:
                score += 75
            elif similarity >= 0.80:
                score += 45

        if (
            metadata.get("date_of_birth")
            and crew.date_of_birth
            and metadata["date_of_birth"] == crew.date_of_birth
        ):
            score += 30

        if score:
            scored.append((score, crew))

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    if not scored:
        return None, "unmatched", 0

    best_score, best = scored[0]

    if (
        len(scored) > 1
        and best_score - scored[1][0] < 20
    ):
        return None, "pending", best_score

    if best_score >= 90:
        return best, "matched", min(best_score, 100)

    return None, "pending", best_score


def store_file(
    storage_path: str,
    original_filename: str,
    content: bytes,
) -> tuple[str, str, str]:
    root = Path(storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)

    checksum = hashlib.sha256(content).hexdigest()

    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4().hex}{suffix}"

    destination = root / stored_filename
    destination.write_bytes(content)

    return (
        str(destination),
        stored_filename,
        checksum,
    )


def document_expiry_status(
    expiry_date: date | None,
    today: date,
    urgent_days: int,
    approaching_days: int,
) -> str:
    if expiry_date is None:
        return "no_date"

    remaining = (expiry_date - today).days

    if remaining < 0:
        return "expired"

    if remaining <= urgent_days:
        return "urgent"

    if remaining <= approaching_days:
        return "approaching"

    return "valid"


def serialize_metadata_for_json(
    metadata: dict,
) -> dict:
    result = {}

    for key, value in metadata.items():
        if isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_metadata_for_json(value)
        else:
            result[key] = value

    return result
