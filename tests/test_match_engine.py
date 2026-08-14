"""Match Engine — 20 kabul senaryosu (kullanıcı talebi 24).

Unit + integration karışımı: engine davranışını DB yazmadan (dry_run) ve
upload üzerinden (gerçek) doğrular.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from app.services.match_engine import (
    AUTO_MATCH,
    CONFLICT,
    REVIEW,
    UNMATCHED,
    MatchEngine,
)

from tests.fixtures.doc_dataset import (
    DocSpec,
    confusing_filename,
    make_crew_payload,
    render_doc,
)


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _make_doc(db, filename: str, text: str) -> object:
    from app.models.document import Document
    from app.services.document_processing import (
        extract_metadata,
        serialize_metadata_for_json,
    )

    metadata = extract_metadata(filename, text)
    doc = Document(
        original_filename=filename,
        stored_filename="test-" + filename,
        storage_path="/tmp/" + filename,
        mime_type="text/plain",
        file_size=len(text.encode()),
        checksum="sha-test-" + filename,
        document_type=metadata["document_type"],
        match_status="pending",
        extracted_text=text,
        extracted_metadata=serialize_metadata_for_json(metadata),
    )
    db.add(doc)
    db.flush()
    return doc


def _upload(client, filename: str, text: str):
    return client.post(
        "/api/documents/upload",
        files=[("files", (filename, text.encode(), "text/plain"))],
    )


def _engine(db, doc) -> object:
    return MatchEngine(db, actor_email="test@example.com").process(
        doc, text=doc.extracted_text, dry_run=True
    )


# ── 1) Passport exact match ───────────────────────────────────────────────────

def test_1_passport_exact_match(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"),
    ).json()

    text = render_doc(DocSpec("passport", "Cengiz", "Kılıç", passport="U1234567"))
    r = _upload(client, confusing_filename(0), text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] == crew["id"]
    assert doc["match_status"] == "matched"
    assert doc["match_confidence"] >= 90


# ── 2) Seaman book exact match ────────────────────────────────────────────────

def test_2_seaman_book_exact_match(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Mehmet", "Çetin", seaman_book="SB-10001"),
    ).json()

    text = render_doc(DocSpec("seaman_book", "Mehmet", "Çetin", seaman_book="SB-10001"))
    r = _upload(client, "scan003.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] == crew["id"]
    assert doc["match_status"] == "matched"


# ── 3) Name exact match ───────────────────────────────────────────────────────

def test_3_name_exact_match(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Elif", "Yıldız"),
    ).json()

    text = render_doc(DocSpec("cv", "Elif", "Yıldız", email="elif@example.com"))
    r = _upload(client, confusing_filename(2), text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] == crew["id"]
    assert doc["match_status"] == "matched"


# ── 4) Turkish character normalized match ─────────────────────────────────────

def test_4_turkish_normalized_match(db_session, client):
    # DB'de Türkçe karakterli isim, içerikte ASCII yazım.
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Ayşe", "Öztürk"),
    ).json()

    text = render_doc(DocSpec("medical", "Ayse", "Ozturk", email="ayse@example.com"))
    r = _upload(client, "IMG_2381.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] == crew["id"]
    assert doc["match_status"] == "matched"


# ── 5) Fuzzy name match (benzer ama farklı isim) ─────────────────────────────

def test_5_fuzzy_name_goes_to_review_not_auto(db_session, client):
    # "Mehmet Çetin" DB'de; belge "Mehmet Çetiner" — yanlış eşleşme OLMAMALI.
    client.post("/api/crew/", json=make_crew_payload("Mehmet", "Çetin"))

    text = render_doc(DocSpec("certificate", "Mehmet", "Çetiner"))
    r = _upload(client, "certificate.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    # fuzzy isim tek başına auto-match etmez; review veya unmatched.
    assert doc["match_status"] in ("review_required", "unmatched")


# ── 6) Same-name crew conflict ────────────────────────────────────────────────

def test_6_same_name_two_crew_never_auto(db_session, client):
    client.post("/api/crew/", json=make_crew_payload("Ahmet", "Yılmaz", passport="PA1"))
    client.post("/api/crew/", json=make_crew_payload("Ahmet", "Yılmaz", passport="PA2"))

    text = render_doc(DocSpec("stcw", "Ahmet", "Yılmaz"))
    r = _upload(client, "AHMET_YILMAZ_STCW.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] is None
    assert doc["match_status"] == "review_required"


# ── 7) Wrong filename but correct content ─────────────────────────────────────

def test_7_wrong_filename_correct_content(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Rıza", "Yıldırım", seaman_book="SB-70007"),
    ).json()

    # Dosya adı "certificate.txt" — içerik seaman book + güçlü identifier.
    text = render_doc(DocSpec("seaman_book", "Rıza", "Yıldırım", seaman_book="SB-70007"))
    r = _upload(client, "certificate.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] == crew["id"]
    assert doc["match_status"] == "matched"


# ── 8) No identifiable person ─────────────────────────────────────────────────

def test_8_no_identifiable_person_unmatched(db_session, client):
    client.post("/api/crew/", json=make_crew_payload("Cengiz", "Kılıç"))

    text = render_doc(DocSpec("other", extra_text="Bir belge parçası."))
    r = _upload(client, "document.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["match_status"] in ("unmatched", "review_required")


# ── 9) Duplicate document ─────────────────────────────────────────────────────

def test_9_duplicate_document(db_session, client):
    text = render_doc(DocSpec("cv", "Zeynep", "Şahin", email="zeynep@example.com"))
    first = _upload(client, "scan001.txt", text)
    second = _upload(client, "IMG_2381.txt", text)

    assert first.json()[0]["id"] == second.json()[0]["id"]
    assert second.json()[0]["duplicate"] is True


# ── 10) Conflicting passport number (aynı pasaport iki personelde) ───────────

def test_10_conflicting_passport_never_auto(db_session, client):
    # Aynı pasaport numarası iki farklı personelde kayıtlı → belirsiz.
    client.post("/api/crew/", json=make_crew_payload("Furkan", "Aydın", passport="B7654321"))
    client.post("/api/crew/", json=make_crew_payload("Zeynep", "Şahin", passport="B7654321"))

    # İçerikte isim yok — yalnızca pasaport numarası (iki kişide kayıtlı).
    text = render_doc(DocSpec("passport", passport="B7654321"))
    r = _upload(client, "ZEYNEP_PASAPORT.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    # Aynı pasaport iki kişide: otomatik eşleşme YAPILMAMALI.
    assert doc["crew_member_id"] is None
    assert doc["match_status"] in ("conflict", "review_required")


# ── 11) Multiple candidates → review ──────────────────────────────────────────

def test_11_multiple_candidates_review(db_session, client):
    client.post("/api/crew/", json=make_crew_payload("Elif", "Yıldız", passport="PA11"))
    client.post("/api/crew/", json=make_crew_payload("Elif", "Yıldız", passport="PA22"))

    text = render_doc(DocSpec("cv", "Elif", "Yıldız", email="elif.y@example.com"))
    r = _upload(client, "scan001.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["crew_member_id"] is None
    assert doc["match_status"] == "review_required"


# ── 12) Manual override ───────────────────────────────────────────────────────

def test_12_manual_override_links_and_logs(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"),
    ).json()

    text = render_doc(DocSpec("cv", "Belirsiz", "Kişi", email="unknown@example.com"))
    r = _upload(client, "scan001.txt", text)
    doc_id = r.json()[0]["id"]

    # Manuel bağla.
    mr = client.put(f"/api/documents/{doc_id}/match", json={"crew_member_id": crew["id"]})
    assert mr.status_code == 200
    assert mr.json()["crew_member_id"] == crew["id"]
    assert mr.json()["match_status"] == "matched"

    # Match geçmişi MATCH_OVERRIDE içermeli.
    history = client.get(f"/api/documents/{doc_id}/matches").json()
    assert any(row["decision"] == "MATCH_OVERRIDE" for row in history)


# ── 13) Bulk 100 documents (staged, senkron işlenir) ──────────────────────────

def test_13_bulk_100_documents(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"),
    ).json()

    files = []
    for i in range(100):
        spec = DocSpec("passport", "Cengiz", "Kılıç", passport="U1234567")
        files.append((f"files", (f"doc_{i}.txt", render_doc(spec).encode(), "text/plain")))

    r = client.post("/api/documents/upload", files=files)
    assert r.status_code == 201
    docs = r.json()
    assert len(docs) == 100
    # Tümü aynı checksum → ilk 1 kaydedildi, 99 duplicate.
    assert all(doc["crew_member_id"] == crew["id"] for doc in docs)
    assert all(doc["match_status"] == "matched" for doc in docs)


# ── 14) Failed PDF (bozuk içerik) ─────────────────────────────────────────────

def test_14_failed_pdf_handled_gracefully(db_session, client):
    client.post("/api/crew/", json=make_crew_payload("Cengiz", "Kılıç"))

    # %PDF başlığı var ama pypdf ayrıştıramaz → boş metin → unmatched/review.
    bad_pdf = b"%PDF-1.4\nthis is not a real pdf body that pypdf cannot parse"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("corrupt.pdf", bad_pdf, "application/pdf"))],
    )
    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["match_status"] in ("unmatched", "review_required")


# ── 15) Scanned PDF (boş metin) → review, asla auto değil ────────────────────

def test_15_scanned_pdf_no_auto_match(db_session, client):
    client.post("/api/crew/", json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"))

    # İçerik çıkarılamayan (tarama) PDF: %PDF geçerli ama metin yok.
    minimal_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("scan.pdf", minimal_pdf, "application/pdf"))],
    )
    assert r.status_code == 201
    doc = r.json()[0]
    # OCR yok → metin boş → otomatik eşleşme yok.
    assert doc["crew_member_id"] is None
    assert doc["match_status"] in ("unmatched", "review_required")


# ── 16) OCR failure → review_required (aynı davranış, scanned) ───────────────

def test_16_ocr_failure_review_not_failed(db_session, client):
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("ocr_fail.pdf", b"%PDF-1.4\n%%EOF", "application/pdf"))],
    )
    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["match_status"] != "failed"


# ── 17) Existing matched document not corrupted ───────────────────────────────

def test_17_existing_matched_not_corrupted(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"),
    ).json()

    text = render_doc(DocSpec("passport", "Cengiz", "Kılıç", passport="U1234567"))
    r = _upload(client, "scan001.txt", text)
    doc = r.json()[0]
    assert doc["match_status"] == "matched"

    # Aynı belgeyi tekrar sorgula — durumu korunmalı.
    again = client.get(f"/api/documents/{doc['id']}")
    assert again.json()["match_status"] == "matched"
    assert again.json()["crew_member_id"] == crew["id"]


# ── 18) Viewer cannot modify matching ─────────────────────────────────────────

def test_18_viewer_cannot_override(db_session, viewer_client):
    text = render_doc(DocSpec("cv", "Cengiz", "Kılıç"))
    r = _upload(viewer_client, "scan001.txt", text)
    assert r.status_code == 403

    crew = viewer_client.post("/api/crew/", json=make_crew_payload("Cengiz", "Kılıç"))
    assert crew.status_code == 403


# ── 19) Admin/HR can review and match ─────────────────────────────────────────

def test_19_hr_can_match(db_session, hr_client):
    crew = hr_client.post(
        "/api/crew/",
        json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"),
    ).json()

    text = render_doc(DocSpec("passport", "Cengiz", "Kılıç", passport="U1234567"))
    r = _upload(hr_client, "scan001.txt", text)

    assert r.status_code == 201
    doc = r.json()[0]
    assert doc["match_status"] == "matched"
    assert doc["crew_member_id"] == crew["id"]


# ── 20) Audit log written for auto match ──────────────────────────────────────

def test_20_auto_match_writes_document_match(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"),
    ).json()

    text = render_doc(DocSpec("passport", "Cengiz", "Kılıç", passport="U1234567"))
    r = _upload(client, "scan001.txt", text)
    doc_id = r.json()[0]["id"]

    history = client.get(f"/api/documents/{doc_id}/matches").json()
    assert len(history) >= 1
    auto = next(row for row in history if row["decision"] == "AUTO_MATCH")
    assert auto["final_crew_id"] == crew["id"]
    assert auto["score"] >= 90
    assert "passport_exact" in (auto["signals"] or {})


# ── Dry-run: DB'ye yazmaz ─────────────────────────────────────────────────────

def test_dry_run_does_not_write(db_session, client):
    crew = client.post(
        "/api/crew/",
        json=make_crew_payload("Cengiz", "Kılıç", passport="U1234567"),
    ).json()

    # Dry-run engine: belgeyi geçici modelde işler, crew_id değişmez.
    from app.models.document import Document

    text = render_doc(DocSpec("passport", "Cengiz", "Kılıç", passport="U1234567"))
    doc = _make_doc(db_session, "scan001.txt", text)
    db_session.commit()
    doc_id = doc.id

    engine = MatchEngine(db_session, actor_email="dry@example.com")
    result = engine.process(doc, text=text, dry_run=True)

    assert result.decision == AUTO_MATCH
    assert result.best_candidate.crew_id == crew["id"]

    # Dry-run DB'ye yazmamalı: match kaydı yok, durum değişmedi.
    db_session.expire_all()
    doc = db_session.get(Document, doc_id)
    assert doc.crew_member_id is None
    assert doc.match_status == "pending"
    from app.models.document_match import DocumentMatch

    matches = db_session.query(DocumentMatch).filter(DocumentMatch.document_id == doc_id).count()
    assert matches == 0
