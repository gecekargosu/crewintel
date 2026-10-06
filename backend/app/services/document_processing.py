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


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".bmp", ".tiff", ".tif"}
OFFICE_EXTENSIONS = {".doc", ".docx", ".odt", ".rtf", ".xlsx", ".xls", ".ods", ".csv"}
PDF_CONVERTIBLE_EXTENSIONS = IMAGE_EXTENSIONS | OFFICE_EXTENSIONS | {".txt", ".pdf"}


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


def _ocr_image(content: bytes) -> str:
    """Resimden metin okur (tesseract). Kurulu değilse boş döner."""
    import io

    from PIL import Image

    try:
        import pytesseract

        img = Image.open(io.BytesIO(content))
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        return pytesseract.image_to_string(img, lang="eng+tur")
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
    from uuid import uuid4

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
        produced = list(out_dir.glob(f"*.{target}"))
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
        # A4 (595x842 pt) içine sığdır, kenar boşluğu 12pt
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
    """Türkçe destekli bir TTF font yolu bulur (fpdf2 için)."""
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
        if text:
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
    gelen NUL, PostgreSQL text alanlarında `DataError` ile500 üretiyordu.
    """
    try:
        text = _extract_text_raw(filename, content)
    except Exception:
        return ""
    return text.replace("\x00", "") if isinstance(text, str) else ""


def _extract_text_raw(filename: str, content: bytes) -> str:
    """Dosya içinden metin çıkarır.

    Desteklenen: PDF, TXT, DOCX, XLSX/ODS/CSV, resimler (OCR), DOC (LibreOffice).
    Bozuk/şifreli/taramalı PDF durumunda boş string dönmez —
    çağrının bu durumu ele alması gerekir.
    """
    lower = filename.lower()

    if lower.endswith(".txt") or lower.endswith(".csv"):
        return content.decode("utf-8", errors="replace")

    if lower.endswith(".docx"):
        text = _extract_docx(content)
        return text or "[DOCX okunamadı]"

    if lower.endswith((".xlsx", ".xlsm")):
        text = _extract_xlsx(content)
        return text or "[XLSX okunamadı]"

    if Path(lower).suffix in IMAGE_EXTENSIONS:
        text = _ocr_image(content)
        return text or "[resim — OCR metin çıkaramadı]"

    if lower.endswith(".pdf"):
        import io

        try:
            reader = PdfReader(io.BytesIO(content))

            # Şifreli PDF kontrolü
            if reader.is_encrypted:
                try:
                    reader.decrypt("")  # boş şifre ile dene
                except Exception:
                    return "[şifreli PDF — metin çıkarılamadı]"

            pages_text = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)

            full_text = "\n".join(pages_text)

            # Taramalı PDF (metin yok, sadece resim) → OCR dene
            if not full_text.strip():
                ocr_text = _ocr_pdf_pages(content)
                if ocr_text:
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


def _ocr_pdf_pages(content: bytes) -> str:
    """Taramalı PDF'i sayfa resimlerine çevirip OCR uygular.

    pdf2image/poppler kurulu değilse boş döner.
    """
    try:
        import io

        from pdf2image import convert_from_bytes
        from PIL import Image

        import pytesseract

        pages = convert_from_bytes(content, dpi=200, last_page=5)
        texts = []
        for page in pages:
            if not isinstance(page, Image.Image):
                continue
            texts.append(pytesseract.image_to_string(page, lang="eng+tur"))
        return "\n".join(texts)
    except Exception:
        return ""


# Dosya adında isim olmayan kelimeler (belge tipi/ek ifadeler)
FILENAME_NOISE = {
    "passport", "pasaport", "stcw", "goc", "eng1", "cv",
    "crew", "medical", "contract", "seaman", "certificate",
    "fitness", "agreement", "resume", "new", "old", "copy",
    "final", "revised", "scan", "scanned", "document", "file",
    "certificate", "certificates", "republic", "panama", "vessel",
    "ships", "employment", "word", "doc", "signed", "signature",
    "page", "img", "image", "pic", "photo", "pic1", "edit",
}

# Text'ten üretilen isim adaylarında gürültü kelimeleri.
# DİKKAT: gerçek ad/soyad olabilecek kelimeler (test, date, valid…)
# burada OLMAMALI — yanlış skip gerçek eşleşmeyi kırar (ör. soyad "Test").
NAME_NOISE = {
    "and", "the", "holder", "certificate", "employee", "employer",
    "ards", "certicate", "certifcate", "republic", "copy", "name",
    "medical", "contract", "passport", "seaman", "untitled",
}


TURKISH_MONTHS = {
    "ocak": "january", "şubat": "february", "subat": "february",
    "mart": "march", "nisan": "april", "mayıs": "may", "mayis": "may",
    "haziran": "june", "temmuz": "july", "ağustos": "august", "agustos": "august",
    "eylül": "september", "eylul": "september", "ekim": "october",
    "kasım": "november", "kasim": "november", "aralık": "december", "aralik": "december",
}


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
)


def _normalize_month_names(value: str) -> str:
    """Translate Turkish month names to English so strptime can parse them."""
    lowered = value.lower()
    for turkish, english in TURKISH_MONTHS.items():
        lowered = lowered.replace(turkish, english)
    return lowered


def parse_date(value: str | None) -> date | None:
    if not value:
        return None

    candidate = _normalize_month_names(re.sub(r"[,;]", "", value.strip()))

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

    # Broad date token: numeric separators or English/Turkish month words.
    date_token = (
        r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
        r"|\d{4}[./-]\d{1,2}[./-]\d{1,2}"
        r"|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)\.?\s*\d{2,4}"
        r"|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)\.?\s+\d{1,2},?\s*\d{2,4}"
        r"|(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s*\d{2,4}"
        r"|\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s*\d{2,4}"
    )

    match = re.search(
        rf"(?:{label_pattern})\s*[:#-]?\s*"
        rf"({date_token})",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    # Strip commas and stray punctuation before parsing.
    raw = re.sub(r"[,;]", "", match.group(1))
    return parse_date(raw)


def extract_metadata(filename: str, text: str) -> dict:
    combined = f"{filename}\n{text}"

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
            rf"[ \t]*(?:no|number|numarası|numarasi)?"
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
        # Second: two space-separated groups, e.g. "AB12 3456".
        for match in re.finditer(
            rf"{anchored}([A-Z0-9]{{2,6}}[ \t]\d{{2,6}})",
            combined,
            re.IGNORECASE,
        ):
            value = re.sub(r"[^A-Z0-9]", "", match.group(1).upper())
            if 5 <= len(value) <= 15:
                return value
        return None

    # Passport: hem "Passport No:" hem "Document No:" formatlarını yakala.
    # "Document No:" yalnızca belge tipi passport/pasaport ise kullanılır.
    passport = _extract_identifier(r"(?:passport|pasaport)")
    if not passport and re.search(r"passport|pasaport", combined, re.IGNORECASE):
        passport = _extract_identifier(r"document")
    seaman = _extract_identifier(
        r"(?:seaman(?:'s)?\s*book|gemiadamı|gemiadami)"
    )

    date_of_birth = _extract_labeled_date(
        combined,
        [
            "dob",
            "birth date",
            "date of birth",
            "doğum tarihi",
            "dogum tarihi",
        ],
    )

    issue_date = _extract_labeled_date(
        combined,
        [
            "issue date",
            "date of issue",
            "veriliş tarihi",
            "verilis tarihi",
        ],
    )

    expiry_date = _extract_labeled_date(
        combined,
        [
            "expiry date",
            "expiration date",
            "date of expiry",
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
        ],
    )

    upper = normalize(combined)

    document_types = {
        "cv": ["curriculum vitae", "resume", "cv"],
        "seaman_book": [
            "seaman book",
            "seaman s book",
            "seamans book",
            "gemiadami cuzdani",
            "gemi adami cuzdani",
        ],
        "passport": ["passport", "pasaport"],
        "stcw": ["stcw"],
        "goc": ["goc"],
        "medical": ["eng1", "medical", "medical certificate"],
        "contract": ["contract", "sozlesme", "sözleşme"],
    }

    document_type = next(
        (
            kind
            for kind, words in document_types.items()
            if any(normalize(word) in upper for word in words)
        ),
        "other",
    )

    # Maritime relevance: belge içeriğinde gemcilik anahtar kelimesi var mı?
    maritime_keywords = [
        "maritime", "vessel", "ship", "crew", "officer", "captain",
        "engineer", "sailor", "port", "voyage", "seaman", "stcw",
        "gemi", "deniz", "denizcilik", "personel", "mürettebat",
        "sefer", "liman", "kaptan", "başmühendis", "gemici",
        "çarkçı", "tanamatör", "kokpit", "makine", "ustabaşı",
        "naval", "merchant", "tonnage", "hull", "bridge",
    ]
    text_lower = f"{filename} {text}".lower()
    maritime_hits = sum(1 for kw in maritime_keywords if kw in text_lower)
    # CV, passport, STCW, seaman_book, medical, contract = otomatik yüksek
    high_relevance_types = {"cv", "passport", "seaman_book", "stcw", "goc", "medical", "contract"}
    if document_type in high_relevance_types:
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
        "maritime_relevance": maritime_relevance,
    }


def extract_name(
    filename: str,
    text: str,
) -> tuple[str | None, str | None]:
    combined = f"{filename}\n{text}"

    # 0) Türkçe formatlar:
    #    a) "Adı Soyadı: Ahmet Yılmaz" (birleşik etiket, tek satır)
    #    b) "Adı: Ayşe\nSoyadı: Çelik" (farklı satırlarda)
    tr_combined = re.search(
        r"\bad[ıi]\s+soyad[ıi]\s*[:#-]\s*"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]{2,})\s+([A-Za-zÇĞİÖŞÜçğıöşü]{2,})",
        combined, re.IGNORECASE,
    )
    if tr_combined:
        return (tr_combined.group(1).title(), tr_combined.group(2).title())
    # b) Farklı satırlarda: Adı: X / Soyadı: Y
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
        skip = NAME_NOISE
        if first.lower() in skip or last.lower() in skip:
            after = combined[match.end():].strip()
            next_m = re.match(r"([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)", after)
            if next_m and next_m.group(1).lower() not in skip and next_m.group(2).lower() not in skip:
                first, last = next_m.group(1).title(), next_m.group(2).title()
            elif fn_candidate:
                # Text gürültüsü — dosya adındaki gerçek isme düş.
                return fn_candidate[0].title(), fn_candidate[1].title()

        # Doğrulama: text adayı dosya adıyla desteklenmiyorsa gürültidir
        # (ör. "Ards Certicate" — "certificate" etiketinden üretilmiş sahte isim).
        if fn_candidate:
            fn_norm = normalize(" ".join(fn_parts))
            words = set(normalize(f"{first} {last}").split())
            if words and not any(w in fn_norm for w in words):
                return fn_candidate[0].title(), fn_candidate[1].title()

        return (first, last)

    if fn_candidate:
        return fn_candidate[0].title(), fn_candidate[1].title()

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
