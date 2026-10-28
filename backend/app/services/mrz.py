"""ICAO 9303 makine okunabilir bölge (MRZ) çözümleyicisi.

Pasaport ve gemiadamı cüzdanlarının altındaki iki satırlık MRZ alanı, belgenin
dilinden bağımsız olarak şu bilgileri taşır:

    P<TURKILMAZ<<AHMET<<<<<<<<<<<<<<<<<<<<<<<<
    U12345678TUR8001014M2708019<<<<<<<<<<<<<<04

OCR ile okunan belgelerde etiketli alanlar ("Date of expiry", "Дата выдачи")
diller/çeviriler yüzünden kaybolabilir; MRZ satırı ise Latin harfli ve sabit
konumludur. Bu yüzden etiketli alan bulunamadığında tarih/number alanları
MRZ'den tamamlanır.

Yalnızca TD3 (pasaport, 2×44 karakter) ve TD2 (kimlik, 2×36) biçimleri
desteklenir; bozuk/eksik satırlar sessizce yok sayılır.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

# OCR sık karıştırılan karakterleri MRZ alfabesine yaklaştırır.
_OCR_FIXES = str.maketrans({"«": "<", "‹": "<", "|": "<", "€": "E", " ": ""})


@dataclass
class MRZData:
    document_number: str | None = None
    surname: str | None = None
    given_names: str | None = None
    nationality: str | None = None
    date_of_birth: date | None = None
    sex: str | None = None
    expiry_date: date | None = None
    full_name: str | None = None


def _mrz_date(value: str, *, future: bool) -> date | None:
    """YYMMDD → tarih. YY iki haneli olduğu için yüzyıl bağlama göre seçilir."""
    if not re.fullmatch(r"\d{6}", value or ""):
        return None
    year, month, day = int(value[:2]), int(value[2:4]), int(value[4:6])
    today = date.today()
    if future:
        candidate = date(2000 + year, 1, 1) if 2000 + year >= today.year - 20 else date(1900 + year, 1, 1)
    else:
        candidate = date(1900 + year, 1, 1) if year > (today.year % 100) else date(2000 + year, 1, 1)
    try:
        return date(candidate.year, month, day)
    except ValueError:
        return None


def _clean_name(value: str) -> str:
    return value.replace("<", " ").strip().title()


_WEIGHTS = (7, 3, 1)


def check_digit(value: str) -> str:
    """ICAO 9303 kontrol basamağı (0-9 veya '<' → 0)."""
    total = 0
    for index, char in enumerate(value):
        if char.isdigit():
            number = int(char)
        elif char == "<":
            number = 0
        else:
            number = ord(char) - 55
        total += number * _WEIGHTS[index % 3]
    return str(total % 10)


def _field_ok(value: str, digit: str) -> bool:
    """Kontrol basamağı tutmuyorsa OCR hatası kabul edilir."""
    if not re.fullmatch(r"\d", digit or ""):
        return False
    return check_digit(value) == digit


def _lines(text: str) -> list[str]:
    """MRZ adayı satırları döndürür (boşluklar temiz, büyük harf)."""
    candidates: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip().upper().translate(_OCR_FIXES)
        if len(line) < 28:
            continue
        if not re.fullmatch(r"[A-Z0-9<]{28,44}", line):
            continue
        # En az bir '<' ve makul oranda rakam/harf karışımı arayalım; düz metin
        # satırlarını (ör. uzun bir cümle) MRZ sanmayalım.
        if "<" not in line:
            continue
        candidates.append(line)
    return candidates


def parse_mrz(text: str) -> MRZData | None:
    """Metindeki MRZ satırlarını çözer; bulunamazsa None döner."""
    lines = _lines(text)
    if len(lines) < 2:
        return None

    for index in range(len(lines) - 1):
        first, second = lines[index], lines[index + 1]
        # TD3: 44 karakter, ilk satır P< ile başlar.
        if len(first) == 44 and len(second) == 44 and first.startswith("P"):
            return _parse_td3(first, second)
        # TD2: 36 karakter, ilk satır I< / A< / C< ile başlar.
        if len(first) == 36 and len(second) == 36 and first[:2] in {"I<", "A<", "C<"}:
            return _parse_td2(first, second)
    return None


def _parse_td3(first: str, second: str) -> MRZData:
    name_part = first[5:44]
    surname, _, given = name_part.partition("<<")
    # Numara/tarih alanları yalnızca kontrol basamağı tutuyorsa kabul edilir.
    doc_number = second[0:9]
    doc_number = doc_number.replace("<", "") or None if _field_ok(doc_number, second[9]) else None
    birth_ok = _field_ok(second[13:19], second[19])
    expiry_ok = _field_ok(second[21:27], second[27])
    return MRZData(
        document_number=doc_number,
        surname=_clean_name(surname) or None,
        given_names=_clean_name(given) or None,
        nationality=second[10:13].replace("<", "") or None,
        date_of_birth=_mrz_date(second[13:19], future=False) if birth_ok else None,
        sex={"M": "M", "F": "F"}.get(second[20]),
        expiry_date=_mrz_date(second[21:27], future=True) if expiry_ok else None,
        full_name=" ".join(filter(None, [_clean_name(given), _clean_name(surname)])) or None,
    )


def _parse_td2(first: str, second: str) -> MRZData:
    name_part = first[5:36]
    surname, _, given = name_part.partition("<<")
    doc_number = second[0:9]
    doc_number = doc_number.replace("<", "") or None if _field_ok(doc_number, second[9]) else None
    birth_ok = _field_ok(second[13:19], second[19])
    expiry_ok = _field_ok(second[21:27], second[27])
    return MRZData(
        document_number=doc_number,
        surname=_clean_name(surname) or None,
        given_names=_clean_name(given) or None,
        nationality=second[10:13].replace("<", "") or None,
        date_of_birth=_mrz_date(second[13:19], future=False) if birth_ok else None,
        sex={"M": "M", "F": "F"}.get(second[20]),
        expiry_date=_mrz_date(second[21:27], future=True) if expiry_ok else None,
        full_name=" ".join(filter(None, [_clean_name(given), _clean_name(surname)])) or None,
    )
