"""Match engine testleri için sentetik belge üretici yardımcılar.

Production DB'ye dokunmaz; yalnızca test senaryolarında kullanılır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TURKISH_NAMES = [
    ("Cengiz", "Kılıç"),
    ("Ahmet", "Yılmaz"),
    ("Elif", "Yıldız"),
    ("Mehmet", "Çetin"),
    ("Ayşe", "Öztürk"),
    ("Furkan", "Aydın"),
    ("Zeynep", "Şahin"),
    ("Rıza", "Yıldırım"),
]

PASSPORTS = [
    "U1234567",
    "P9876543",
    "AB-123456",
    "TR-88213",
    "A12-345678",
    "B7654321",
    "C123-4567",
    "D987-6543",
]

SEAMAN_BOOKS = [
    "SB-10001",
    "SB-20002",
    "SB-30003",
    "SB-40004",
    "SB-50005",
    "SB-60006",
    "SB-70007",
    "SB-80008",
]


@dataclass
class DocSpec:
    """Sentetik belge içeriği spesifikasyonu."""

    doc_type: str
    first_name: str | None = None
    last_name: str | None = None
    passport: str | None = None
    seaman_book: str | None = None
    email: str | None = None
    dob: str | None = None
    expiry: str | None = None
    employer: str | None = None
    vessel: str | None = None
    extra_text: str = ""


def _name_line(first: str | None, last: str | None) -> str:
    if not first or not last:
        return ""
    return f"Name: {first} {last}"


def render_doc(spec: DocSpec) -> str:
    """Belge içeriği üretir — dosya adından bağımsız (içerik sinyali testi)."""
    lines: list[str] = []

    type_headers = {
        "cv": "CURRICULUM VITAE",
        "passport": "PASSPORT",
        "seaman_book": "SEAMAN'S BOOK",
        "contract": "EMPLOYMENT CONTRACT",
        "certificate": "CERTIFICATE OF COMPETENCY",
        "stcw": "STCW CERTIFICATE",
        "medical": "MEDICAL CERTIFICATE (ENG1)",
        "training": "TRAINING CERTIFICATE",
        "reference": "REFERENCE LETTER",
        "other": "DOCUMENT",
    }
    lines.append(type_headers.get(spec.doc_type, "DOCUMENT"))

    name_line = _name_line(spec.first_name, spec.last_name)
    if name_line:
        lines.append(name_line)

    if spec.passport:
        lines.append(f"Passport Number: {spec.passport}")
    if spec.seaman_book:
        lines.append(f"Seaman's Book No: {spec.seaman_book}")
    if spec.email:
        lines.append(f"Email: {spec.email}")
    if spec.dob:
        lines.append(f"Date of Birth: {spec.dob}")
    if spec.expiry:
        lines.append(f"Expiry Date: {spec.expiry}")
    if spec.employer:
        lines.append(f"Employer: {spec.employer}")
    if spec.vessel:
        lines.append(f"Vessel: {spec.vessel}")
    if spec.extra_text:
        lines.append(spec.extra_text)

    return "\n".join(lines)


def confusing_filename(index: int) -> str:
    """Bilinçli karıştırılmış dosya adları — içerik testi için.

    Upload doğrulaması uzantı-içerik uyumu ister, bu yüzden TXT içerik için
    .txt uzantısı kullanılır; adlar yine de içerikle ilgisizdir.
    """
    names = [
        "scan001.txt",
        "document.txt",
        "IMG_2381.txt",
        "certificate.txt",
        "mehmet_1.txt",
        "untitled_004.txt",
        "DOC_2024.txt",
        "fwd_scan.txt",
    ]
    return names[index % len(names)]


def make_crew_payload(
    first: str,
    last: str,
    passport: str | None = None,
    seaman_book: str | None = None,
    email: str | None = None,
) -> dict:
    payload = {
        "first_name": first,
        "last_name": last,
        "position": "Captain",
        "nationality": "Turkish",
    }
    if passport:
        payload["passport_number"] = passport
    if seaman_book:
        payload["seaman_book_number"] = seaman_book
    if email:
        payload["email"] = email
    return payload
