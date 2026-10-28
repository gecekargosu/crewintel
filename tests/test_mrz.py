"""MRZ (pasaport altı iki satır) çözümleme testleri.

Bu alan dil bağımsızdır: Arapça/Rusça taranmış pasaportlarda etiketli tarih
alanları OCR'da kaybolsa bile son geçerlilik tarihi ve numara MRZ'den okunur.
"""

from datetime import date

from app.services.document_processing import extract_metadata
from app.services.mrz import check_digit, parse_mrz


def _td3(*, number: str = "U12345678", nationality: str = "TUR",
         birth: str = "800101", sex: str = "M", expiry: str = "270801") -> str:
    line1 = "P<TUR" + "KILMAZ<<AHMET<<<<<<<<<<<<<<<<<<<<<<<<"
    line1 = line1[:44].ljust(44, "<")
    number_field = number.ljust(9, "<")
    personal = "<" * 14
    line2 = (
        f"{number_field}{check_digit(number_field)}"
        f"{nationality}"
        f"{birth}{check_digit(birth)}"
        f"{sex}"
        f"{expiry}{check_digit(expiry)}"
        f"{personal}{check_digit(personal)}"
    )
    line2 += check_digit(line2)
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return f"{line1}\n{line2}"


def test_parse_td3_reads_names_dates_and_number():
    mrz = parse_mrz(f"REPUBLIC OF TURKIYE\n{_td3()}")
    assert mrz is not None
    assert mrz.document_number == "U12345678"
    assert mrz.surname == "Kilmaz"
    assert mrz.given_names == "Ahmet"
    assert mrz.nationality == "TUR"
    assert mrz.date_of_birth == date(1980, 1, 1)
    assert mrz.expiry_date == date(2027, 8, 1)
    assert mrz.sex == "M"


def test_parse_rejects_broken_check_digit():
    text = _td3().replace("U123456784", "U123456785")
    mrz = parse_mrz(text)
    # Kontrol basamağı bozuk alan kullanılmaz; isim yine okunur.
    assert mrz is not None
    assert mrz.document_number is None
    assert mrz.surname == "Kilmaz"


def test_extract_metadata_fills_expiry_from_mrz_when_labels_missing():
    # Etiketli tarih yok; yalnızca MRZ var (taranmış yabancı pasaport senaryosu).
    metadata = extract_metadata("pasaport_tarama.pdf", f"PASSPORT\n{_td3()}")
    assert metadata["document_type"] == "passport"
    assert metadata["passport_number"] == "U12345678"
    assert metadata["expiry_date"] == date(2027, 8, 1)
    assert metadata["date_of_birth"] == date(1980, 1, 1)
    assert metadata["nationality"] == "TUR"


def test_labelled_date_still_wins_over_mrz():
    text = f"Passport No: U12345678\nDate of expiry: 05.05.2030\n{_td3()}"
    metadata = extract_metadata("pasaport.pdf", text)
    assert metadata["expiry_date"] == date(2030, 5, 5)


def test_plain_text_is_not_treated_as_mrz():
    assert parse_mrz("Bu bir pasaport taramasidir ve MRZ satiri yoktur.") is None
