from app.services.document_processing import extract_name


def test_extract_name_from_label():
    first, last = extract_name(
        "document.pdf",
        "Name: John Smith"
    )
    assert first == "John"
    assert last == "Smith"


def test_extract_name_from_turkish_label():
    first, last = extract_name(
        "document.pdf",
        "Adı Soyadı: Ahmet Yılmaz"
    )
    assert first == "Ahmet"
    assert last == "Yılmaz"


def test_extract_name_from_filename():
    first, last = extract_name(
        "Ahmet_Yilmaz_CV.pdf",
        ""
    )
    assert first == "Ahmet"
    assert last == "Yilmaz"


def test_extract_name_returns_none_when_not_found():
    first, last = extract_name(
        "passport.pdf",
        "Passport document"
    )
    assert first is None
    assert last is None
