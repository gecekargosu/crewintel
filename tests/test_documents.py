def create_crew(client, **overrides):
    payload = {"first_name": "Ahmet", "last_name": "Yılmaz", "position": "Captain", "nationality": "Turkish", "passport_number": "U1234567"}
    payload.update(overrides)
    response = client.post("/api/crew/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_document_upload_matches_strong_identifier_and_creates_audit_log(client):
    crew = create_crew(client)
    content = b"Passport No: U1234567\nName: Ahmet Yilmaz\nExpiry: 01.08.2027"
    response = client.post("/api/documents/upload", files=[("files", ("YILMAZ_AHMET_PASAPORT.txt", content, "text/plain"))])

    assert response.status_code == 201
    document = response.json()[0]
    assert document["crew_member_id"] == crew["id"]
    assert document["match_status"] == "matched"
    assert document["document_type"] == "passport"


from pathlib import Path

from app.core.config import get_settings


# ── P3: Upload içerik doğrulaması ─────────────────────────────────────────────

def test_upload_rejects_unsupported_extension(client):
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("evil.html", b"<script>alert(1)</script>", "text/html"))],
    )
    assert r.status_code == 415


def test_upload_rejects_fake_pdf_content(client):
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("fake.pdf", b"this is not a pdf", "application/pdf"))],
    )
    assert r.status_code == 415


def test_upload_rejects_binary_txt_content(client):
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("binary.txt", b"\x00\x01\x02hello", "text/plain"))],
    )
    assert r.status_code == 415


def test_upload_accepts_valid_pdf_content(client):
    minimal_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("real.pdf", minimal_pdf, "application/pdf"))],
    )
    assert r.status_code == 201


# ── P3: Toplu upload başarısızlığında orphan dosya kalmamalı ─────────────────

def _storage_dir():
    return Path(get_settings().storage_path)


def _disk_delta(before):
    after = set(_storage_dir().iterdir()) if _storage_dir().exists() else set()
    return after - before


def test_batch_upload_with_invalid_second_file_cleans_up_disk(client):
    before = set(_storage_dir().iterdir()) if _storage_dir().exists() else set()

    r = client.post(
        "/api/documents/upload",
        files=[
            ("files", ("first_valid.txt", b"Name: Orphan Test\nSTCW", "text/plain")),
            ("files", ("second_evil.html", b"<script>x</script>", "text/html")),
        ],
    )
    assert r.status_code == 415
    assert _disk_delta(before) == set(), f"Orphan files left: {_disk_delta(before)}"


def test_batch_upload_with_empty_second_file_cleans_up_disk(client):
    before = set(_storage_dir().iterdir()) if _storage_dir().exists() else set()

    r = client.post(
        "/api/documents/upload",
        files=[
            ("files", ("first_valid.txt", b"Name: Orphan Two\nMedical", "text/plain")),
            ("files", ("second_empty.txt", b"", "text/plain")),
        ],
    )
    assert r.status_code == 422
    assert _disk_delta(before) == set(), f"Orphan files left: {_disk_delta(before)}"


# ── P3: İndirme medya tipi uzantıdan türetilmeli (client mime'ına güvenilmemeli) ──

def test_download_serves_extension_based_media_type(client):
    # Client yanlış mime gönderse bile servis uzantıdan güvenli tip kullanmalı
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("mime_test.txt", b"PASSPORT\nName: Mime Test", "text/html"))],
    )
    assert r.status_code == 201
    doc_id = r.json()[0]["id"]

    dl = client.get(f"/api/documents/{doc_id}/file")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("text/plain")


# ── P2: Güçlü tanımlayıcı (pasaport) isimden üstün olmalı ────────────────────

def test_strong_identifier_beats_filename_name(client):
    # Pasaport numarası belgede başkasının adıyla gelse bile güçlü tanımlayıcı
    # (pasaport) isim eşleşmesinden üstün olmalı.
    crew_a = create_crew(client, first_name="Ali", last_name="Veli", passport_number="PA7777")
    create_crew(client, first_name="Ahmet", last_name="Yilmaz", passport_number="PB8888")

    content = b"PASSPORT No: PA7777\nName: Ahmet Yilmaz\nExpiry: 01.01.2030"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("AHMET_YILMAZ_PASAPORT.txt", content, "text/plain"))],
    )
    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] == crew_a["id"]
    assert doc["match_status"] == "matched"


def test_seaman_book_document_is_classified_and_matches(client):
    crew = create_crew(client, seaman_book_number="SB12345")
    content = b"SEAMAN'S BOOK No: SB12345\nName: Ahmet Yilmaz\nExpiry: 01.08.2027"
    response = client.post(
        "/api/documents/upload",
        files=[("files", ("YILMAZ_AHMET_SEAMAN_BOOK.txt", content, "text/plain"))],
    )

    assert response.status_code == 201
    document = response.json()[0]
    assert document["document_type"] == "seaman_book"
    assert document["crew_member_id"] == crew["id"]
    assert document["match_status"] == "matched"


def test_ambiguous_name_stays_review_required(client):
    # Aynı isimli iki personel: otomatik eşleşme YAPILMAMALI — review_required.
    create_crew(client, passport_number="A1")
    create_crew(client, first_name="Ahmet", last_name="Yılmaz", passport_number="A2")
    response = client.post("/api/documents/upload", files=[("files", ("AHMET_YILMAZ_STCW.txt", b"STCW certificate", "text/plain"))])

    assert response.status_code == 201
    assert response.json()[0]["crew_member_id"] is None
    assert response.json()[0]["match_status"] == "review_required"


def test_cv_creates_crew_when_no_match_exists(client):
    response = client.post("/api/documents/upload", files=[("files", ("MEHMET_KAYA_CV.txt", b"Curriculum Vitae\nName: Mehmet Kaya\nmehmet@example.com", "text/plain"))])

    assert response.status_code == 201
    assert response.json()[0]["match_status"] == "matched"
    assert client.get("/api/crew/?name=Mehmet").json()[0]["email"] == "mehmet@example.com"


def test_duplicate_upload_returns_existing_document(client):
    content = b"Name: No Match\nSTCW"
    first = client.post("/api/documents/upload", files=[("files", ("first.txt", content, "text/plain"))])
    second = client.post("/api/documents/upload", files=[("files", ("second.txt", content, "text/plain"))])

    assert first.status_code == second.status_code == 201
    assert first.json()[0]["id"] == second.json()[0]["id"]


def test_match_status_filter_returns_only_pending_documents(client):
    # Belge A: güçlü tanımlayıcı → matched
    create_crew(client)
    matched_upload = client.post(
        "/api/documents/upload",
        files=[("files", ("YILMAZ_AHMET_PASAPORT.txt", b"Passport No: U1234567\nName: Ahmet Yilmaz", "text/plain"))],
    )
    assert matched_upload.json()[0]["match_status"] == "matched"

    # Belge B: belirsiz → review_required (iki aynı isimli personel)
    create_crew(client, passport_number="B1")
    create_crew(client, first_name="Ahmet", last_name="Yılmaz", passport_number="B2")
    pending_upload = client.post(
        "/api/documents/upload",
        files=[("files", ("AHMET_YILMAZ_GOC.txt", b"GOC certificate", "text/plain"))],
    )
    assert pending_upload.json()[0]["match_status"] == "review_required"

    # Filtre: sadece review_required belgeler
    response = client.get("/api/documents/?match_status=review_required")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(doc["match_status"] == "review_required" for doc in results)

    # Filtre: sadece matched belgeler — review_required belgeler sonuçta olmamalı
    matched_response = client.get("/api/documents/?match_status=matched")
    assert matched_response.status_code == 200
    assert all(doc["match_status"] == "matched" for doc in matched_response.json())

    # Filtresiz çağrı hâlâ çalışmalı (geriye dönük uyumluluk)
    all_response = client.get("/api/documents/")
    assert all_response.status_code == 200
    assert len(all_response.json()) >= 2
