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
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".txt"):
        return content.decode("utf-8", errors="replace")

    if filename.lower().endswith(".pdf"):
        import io

        try:
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )
        except Exception:
            return ""

    return ""


def parse_date(value: str | None) -> date | None:
    if not value:
        return None

    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    return None


def _extract_labeled_date(
    text: str,
    labels: list[str],
) -> date | None:
    label_pattern = "|".join(re.escape(label) for label in labels)

    match = re.search(
        rf"(?:{label_pattern})\s*[:#-]?\s*"
        rf"(\d{{1,2}}[./-]\d{{1,2}}[./-]\d{{4}})",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return parse_date(match.group(1))


def extract_metadata(filename: str, text: str) -> dict:
    combined = f"{filename}\n{text}"

    email = re.search(
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        combined,
    )

    passport = re.search(
        r"(?:passport|pasaport)"
        r"\s*(?:no|number|numarası|numarasi)?"
        r"\s*[:#-]?\s*([A-Z0-9]{6,15})",
        combined,
        re.IGNORECASE,
    )

    seaman = re.search(
        r"(?:seaman(?:'s)?\s*book|gemiadamı|gemiadami)"
        r"\s*(?:no|number|numarası|numarasi)?"
        r"\s*[:#-]?\s*([A-Z0-9]{5,15})",
        combined,
        re.IGNORECASE,
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
            "son geçerlilik tarihi",
            "son gecerlilik tarihi",
        ],
    )

    upper = normalize(combined)

    document_types = {
        "cv": ["curriculum vitae", "resume", "cv"],
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

    return {
        "email": email.group(0).lower() if email else None,
        "passport_number": (
            passport.group(1).upper()
            if passport
            else None
        ),
        "seaman_book_number": (
            seaman.group(1).upper()
            if seaman
            else None
        ),
        "date_of_birth": date_of_birth,
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "document_type": document_type,
        "filename": filename,
    }


def extract_name(
    filename: str,
    text: str,
) -> tuple[str | None, str | None]:
    combined = f"{filename}\n{text}"

    match = re.search(
        r"(?:name|adı soyadı|adi soyadi|ad soyad|full name)"
        r"\s*[:#-]?\s*"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)"
        r"\s+"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)",
        combined,
        re.IGNORECASE,
    )

    if match:
        return (
            match.group(1).title(),
            match.group(2).title(),
        )

    ignored = {
        "passport",
        "pasaport",
        "stcw",
        "goc",
        "eng1",
        "cv",
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
            if normalize(metadata["passport_number"]) != normalize(
                crew.passport_number
            ):
                continue
            score += 100

        if (
            metadata.get("seaman_book_number")
            and crew.seaman_book_number
        ):
            if normalize(metadata["seaman_book_number"]) != normalize(
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
