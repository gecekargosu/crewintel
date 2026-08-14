from app.services.document_processing import normalize


def test_normalize_case_and_turkish_characters():
    assert normalize("ÇĞİÖŞÜ") == "cgiosu"


def test_normalize_preserves_word_separation():
    assert normalize("John Smith") == "john smith"
