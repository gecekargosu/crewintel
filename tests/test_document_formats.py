"""Belge hattı: format desteği, çok dilli tarih/isim ve yükleme doğrulaması."""

import io
from datetime import date

import pytest
from fastapi import HTTPException

from app.services.document_processing import (
    classify_document_type,
    convert_to_pdf,
    extract_metadata,
    extract_name,
    extract_text,
    parse_date,
)
from app.services.document_service import validate_upload


# ── Tarih ayrıştırma (çok dilli) ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("12.03.2024", date(2024, 3, 12)),
        ("12 Mart 2024", date(2024, 3, 12)),
        ("12 марта 2024", date(2024, 3, 12)),        # Rusça
        ("12. März 2024", date(2024, 3, 12)),        # Almanca
        ("12 août 2020", date(2020, 8, 12)),         # Fransızca
        ("12 Ocak 2019", date(2019, 1, 12)),         # Türkçe
        ("31/12/2025", date(2025, 12, 31)),
    ],
)
def test_parse_date_multilingual(raw, expected):
    assert parse_date(raw) == expected


def test_metadata_reads_russian_passport_dates():
    text = (
        "PASSPORT / ПАСПОРТ\n"
        "Surname: IVANOV\n"
        "Given Names: IVAN\n"
        "Date of birth: 05.07.1985\n"
        "Date of issue: 12 марта 2020\n"
        "Date of expiry: 12.03.2030\n"
        "Passport No: 51 2345678\n"
    )
    metadata = extract_metadata("passport_ivanov.pdf", text)

    assert metadata["document_type"] == "passport"
    assert metadata["date_of_birth"] == date(1985, 7, 5)
    assert metadata["issue_date"] == date(2020, 3, 12)
    assert metadata["expiry_date"] == date(2030, 3, 12)
    assert metadata["passport_number"] == "512345678"


def test_metadata_does_not_invent_missing_fields():
    metadata = extract_metadata("belge.pdf", "Bu belgede tarih yok.")
    assert metadata["issue_date"] is None
    assert metadata["expiry_date"] is None
    assert metadata["passport_number"] is None


# ── İsim çıkarma (çok dilli) ─────────────────────────────────────────────────


def test_name_turkish_combined_label():
    assert extract_name("belge.pdf", "Adı Soyadı: Mehmet Kaya") == ("Mehmet", "Kaya")


def test_name_turkish_separate_lines():
    first, last = extract_name("belge.pdf", "Adı: Ayşe\nSoyadı: Çelik")
    assert (first, last) == ("Ayşe", "Çelik")


def test_name_russian_surname_given_names():
    text = "Surname: IVANOV\nGiven Names: IVAN"
    assert extract_name("passport.pdf", text) == ("Ivan", "Ivanov")


def test_name_from_multiword_filename():
    first, last = extract_name("AHMED SABRY KAMAL ELHENAWY passport.pdf", "")
    assert first == "Ahmed Sabry Kamal"
    assert last == "Elhenawy"


def test_filename_noise_is_ignored():
    first, last = extract_name("stcw_certificate_ali_veli.pdf", "")
    assert (first, last) == ("Ali", "Veli")


# ── Belge tipi sınıflandırma ─────────────────────────────────────────────────


def test_medical_document_mentioning_passport_is_medical():
    text = (
        "MEDICAL FITNESS CERTIFICATE\n"
        "Passport No: AB1234567\n"
        "This is to certify that the seafarer is fit for duty.\n"
    )
    assert classify_document_type("medical_report.pdf", text) == "medical"


def test_ocr_concatenated_keywords_and_dot_separator():
    # Gerçek OCR çıktısı: kelimeler birleşik, etiketten sonra nokta var.
    text = (
        "MEDICAL FITNESSCERTIFICATE\n"
        "Name: Mehmet Kaya\n"
        "Date of Expiry. 17/08/2026\n"
    )
    assert classify_document_type("mehmet_saglik.jpg", text) == "medical"
    assert extract_metadata("mehmet_saglik.jpg", text)["expiry_date"] == date(2026, 8, 17)


def test_cv_with_contract_mention_is_cv():
    text = "CURRICULUM VITAE\nExperienced chief officer. Previous contract: 6 months."
    assert classify_document_type("mehmet_kaya_cv.pdf", text) == "cv"


# ── Format desteği ───────────────────────────────────────────────────────────


def _docx_bytes(text: str) -> bytes:
    from docx import Document

    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_text_from_docx():
    content = _docx_bytes("Adı Soyadı: Mehmet Kaya\nSTCW Certificate")
    extracted = extract_text("cv.docx", content)
    assert "Mehmet Kaya" in extracted


def test_convert_image_to_pdf():
    from PIL import Image

    image = Image.new("RGB", (400, 200), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    pdf, error = convert_to_pdf("passport.jpg", buffer.getvalue())
    assert error == ""
    assert pdf is not None and pdf.startswith(b"%PDF")


def test_validate_upload_accepts_docx_and_rejects_unknown():
    content = _docx_bytes("merhaba")
    assert validate_upload("cv.docx", content) == "cv.docx"

    with pytest.raises(HTTPException) as error:
        validate_upload("virus.exe", b"MZ\x90\x00")
    assert error.value.status_code == 415


def test_validate_upload_corrects_misnamed_valid_file():
    from PIL import Image

    image = Image.new("RGB", (50, 50), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    # JPEG içeriği .pdf adıyla gelmiş (arşivde görülen gerçek durum).
    assert validate_upload("passport.pdf", buffer.getvalue()) == "passport.jpg"


def test_validate_upload_rejects_fake_pdf():
    with pytest.raises(HTTPException) as error:
        validate_upload("sahte.pdf", b"<html>merhaba</html>")
    assert error.value.status_code == 415
