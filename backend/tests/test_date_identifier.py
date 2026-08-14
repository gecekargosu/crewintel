"""Date-format and identifier-extraction tests for the document engine."""

from datetime import date

import pytest

from app.services.document_processing import (
    extract_metadata,
    normalize,
    normalize_identifier,
    parse_date,
)


# ── Date parsing ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("raw,expected", [
    ("15.03.2027", date(2027, 3, 15)),
    ("15/03/2027", date(2027, 3, 15)),
    ("15-03-2027", date(2027, 3, 15)),
    ("2027-03-15", date(2027, 3, 15)),
    ("2027/03/15", date(2027, 3, 15)),
    ("15 Mar 2027", date(2027, 3, 15)),
    ("Mar 15 2027", date(2027, 3, 15)),
    ("15 March 2027", date(2027, 3, 15)),
    ("March 15, 2027", date(2027, 3, 15)),
    ("15 Mart 2027", date(2027, 3, 15)),
    ("Mart 15 2027", date(2027, 3, 15)),
    ("15 Ocak 2027", date(2027, 1, 15)),
    ("15 Şubat 2027", date(2027, 2, 15)),
    ("15 Ağustos 2027", date(2027, 8, 15)),
    ("15 Aralık 2027", date(2027, 12, 15)),
])
def test_parse_date_formats(raw, expected):
    assert parse_date(raw) == expected


def test_parse_date_invalid():
    assert parse_date("not-a-date") is None
    assert parse_date("32.13.2027") is None
    assert parse_date("") is None
    assert parse_date(None) is None


# ── Labeled dates (expiry vs issue vs birth) ────────────────────────────────


def test_expiry_label_numeric():
    metadata = extract_metadata(
        "passport.pdf",
        "Expiry Date: 2027-08-20\nPassport No: AB123456",
    )
    assert metadata["expiry_date"] == date(2027, 8, 20)


def test_expiry_label_turkish():
    metadata = extract_metadata(
        "passport.pdf",
        "Son Geçerlilik Tarihi: 20 Ağustos 2027\nPasaport No: AB123456",
    )
    assert metadata["expiry_date"] == date(2027, 8, 20)


def test_valid_until_label():
    metadata = extract_metadata(
        "stcw.pdf",
        "Valid Until: 12.05.2028",
    )
    assert metadata["expiry_date"] == date(2028, 5, 12)


def test_validity_label_turkish():
    metadata = extract_metadata(
        "medical.pdf",
        "Geçerlilik: 01/01/2029",
    )
    assert metadata["expiry_date"] == date(2029, 1, 1)


def test_birth_and_issue_not_taken_as_expiry():
    metadata = extract_metadata(
        "passport.pdf",
        "Date of Birth: 12.03.1985\n"
        "Issue Date: 01.06.2020\n"
        "Expiry Date: 01.06.2030\n"
        "Passport No: AB123456",
    )
    assert metadata["date_of_birth"] == date(1985, 3, 12)
    assert metadata["issue_date"] == date(2020, 6, 1)
    assert metadata["expiry_date"] == date(2030, 6, 1)


def test_multiple_dates_picks_labeled_one():
    # Document with several dates but only one labelled as expiry.
    metadata = extract_metadata(
        "certificate.pdf",
        "Training completed: 05.05.2021\nExpiry: 05.05.2026",
    )
    assert metadata["expiry_date"] == date(2026, 5, 5)


# ── Identifier extraction (passport / seaman book) ──────────────────────────


@pytest.mark.parametrize("raw,expected", [
    ("Passport No: AB-123456", "AB123456"),
    ("Passport No: AB123456", "AB123456"),
    ("Passport No: A12-345678", "A12345678"),
    ("Passport No: P1234567", "P1234567"),
    ("Passport No: ab-123456", "AB123456"),
    ("Pasaport No: X-234567", "X234567"),
])
def test_passport_extraction_formats(raw, expected):
    metadata = extract_metadata("passport.pdf", raw)
    assert metadata["passport_number"] == expected


def test_passport_spaced():
    metadata = extract_metadata("passport.pdf", "Passport Number: AB12 3456")
    assert metadata["passport_number"] == "AB123456"


def test_passport_not_extracted_from_random_string():
    metadata = extract_metadata("passport.pdf", "REF 1234567890 some random numbers 987654321")
    assert metadata["passport_number"] is None


def test_seaman_book_hyphenated():
    metadata = extract_metadata(
        "seaman_book.pdf",
        "Seaman's Book No: SB-987654",
    )
    assert metadata["seaman_book_number"] == "SB987654"


def test_same_identifier_different_spelling_normalizes_equal():
    assert normalize_identifier("AB-123456") == normalize_identifier("AB123456")
    assert normalize_identifier("A12-345678") == normalize_identifier("A12345678")
    assert normalize_identifier("AB12 3456") == normalize_identifier("AB123456")
    assert normalize_identifier("ab-123456") == normalize_identifier("AB123456")
