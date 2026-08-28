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


def extract_text(filename: str, content: bytes) -> str:
    """Dosya içinden metin çıkarır.

    Bozuk/şifreli/taramalı PDF durumunda boş string dönmez —
    çağrının bu durumu ele alması gerekir.
    """
    if filename.lower().endswith(".txt"):
        return content.decode("utf-8", errors="replace")

    if filename.lower().endswith(".pdf"):
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

            # Taramalı PDF (metin yok, sadece resim)
            if not full_text.strip():
                return "[taramalı PDF — metin katmanı yok, OCR gerekli]"

            return full_text

        except Exception:
            return "[PDF okunamadı — bozuk veya desteklenmeyen format]"

    return ""


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

    if match:
        first = match.group(1).title()
        last = match.group(2).title()
        skip = {"and", "the", "holder", "certificate", "employee", "employer"}
        if first.lower() in skip:
            after = combined[match.end():].strip()
            next_m = re.match(r"([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)", after)
            if next_m:
                return (next_m.group(1).title(), next_m.group(2).title())
        else:
            return (first, last)

    ignored = {
        "passport", "pasaport", "stcw", "goc", "eng1", "cv",
        "crew", "medical", "contract", "seaman", "certificate",
        "fitness", "agreement", "resume",
    }

    parts = [
        part
        for part in re.split(r"[_\-\s]+", Path(filename).stem)
        if len(part) > 2
        and part.lower() not in ignored
    ]

    if len(parts) >= 2:
        return parts[0].title(), parts[1].title()

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
