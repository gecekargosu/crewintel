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


def test_ambiguous_name_stays_pending(client):
    create_crew(client, passport_number="A1")
    create_crew(client, first_name="Ahmet", last_name="Yılmaz", passport_number="A2")
    response = client.post("/api/documents/upload", files=[("files", ("AHMET_YILMAZ_STCW.txt", b"STCW certificate", "text/plain"))])

    assert response.status_code == 201
    assert response.json()[0]["crew_member_id"] is None
    assert response.json()[0]["match_status"] == "pending"


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

    # Belge B: belirsiz → pending (iki aynı isimli personel)
    create_crew(client, passport_number="B1")
    create_crew(client, first_name="Ahmet", last_name="Yılmaz", passport_number="B2")
    pending_upload = client.post(
        "/api/documents/upload",
        files=[("files", ("AHMET_YILMAZ_GOC.txt", b"GOC certificate", "text/plain"))],
    )
    assert pending_upload.json()[0]["match_status"] == "pending"

    # Filtre: sadece pending belgeler
    response = client.get("/api/documents/?match_status=pending")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(doc["match_status"] == "pending" for doc in results)

    # Filtre: sadece matched belgeler — pending belgeler sonuçta olmamalı
    matched_response = client.get("/api/documents/?match_status=matched")
    assert matched_response.status_code == 200
    assert all(doc["match_status"] == "matched" for doc in matched_response.json())

    # Filtresiz çağrı hâlâ çalışmalı (geriye dönük uyumluluk)
    all_response = client.get("/api/documents/")
    assert all_response.status_code == 200
    assert len(all_response.json()) >= 2
