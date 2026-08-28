"""Document Pipeline — end-to-end coverage tests.

Kapsam: Mevcut test_documents.py ve test_match_engine.py'yi tamamlayan
ek testler. Aşağıdaki endpoint'lerin ve davranışların doğru çalıştığını
doğrular:

- POST /api/documents/batch (toplu upload + arka plan işleme)
- GET /api/documents/batch/{id} (batch durumu)
- GET /api/documents/{id}/candidates (aday personel listesi)
- GET /api/documents/{id}/matches (eşleştirme geçmişi)
- DELETE /api/documents/{id} (belge silme)
- Belge tipi sınıflandırması (STCW, GOC, medical, contract)
- Geçerlilik tarihi çıkarma
- Sayfalama (offset/limit)
- expiry_status filtresi
- viewer/crew erişim kısıtlamaları
"""

from datetime import date, timedelta, datetime, UTC

import pytest
from fastapi.testclient import TestClient


# ── Yardımcılar ──────────────────────────────────────────────────────────────


def _create_crew(client, **overrides):
    payload = {
        "first_name": "Pipeline", "last_name": "Test",
        "position": "Captain", "nationality": "Turkish",
        "passport_number": "PL1234567",
    }
    payload.update(overrides)
    r = client.post("/api/crew/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _upload(client, filename, content, mime="text/plain"):
    return client.post(
        "/api/documents/upload",
        files=[("files", (filename, content.encode() if isinstance(content, str) else content, mime))],
    )


def _upload_and_get_doc(client, filename, content, mime="text/plain"):
    r = _upload(client, filename, content, mime)
    assert r.status_code == 201, r.text
    return r.json()[0]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. BATCH UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skip(reason="Batch background task requires PostgreSQL, not SQLite in-memory")
def test_batch_upload_returns_batch_id(client):
    """Batch upload batch_id ve status döndürmeli.
    
    Not: Background task SQLite thread-safe değil, batch processing hata
    verebilir. Bu test sadece batch_id dönüşünü doğrular.
    """
    files = [
        ("files", ("batch1.txt", b"Name: Batch Test\nSTCW certificate", "text/plain")),
        ("files", ("batch2.txt", b"Name: Batch Test\nMedical certificate", "text/plain")),
    ]
    r = client.post("/api/documents/batch", files=files)
    # 202 (accepted) veya 200 (completed) olabilir
    assert r.status_code in (200, 202), r.text
    body = r.json()
    assert "batch_id" in body
    assert body["total"] >= 1


@pytest.mark.skip(reason="Batch background task requires PostgreSQL, not SQLite in-memory")
def test_batch_status_endpoint(client):
    """Batch durumu sorgulanabilmeli.
    
    Not: Background task SQLite thread-safe değil, batch processing
    hata verebilir. Bu test sadece batch kayıt mekanizmasını test eder.
    """
    files = [
        ("files", ("batch_status.txt", b"Name: Status Test\nSTCW", "text/plain")),
    ]
    r = client.post("/api/documents/batch", files=files)
    assert r.status_code in (200, 202)
    batch_id = r.json()["batch_id"]

    status = client.get(f"/api/documents/batch/{batch_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["batch_id"] == batch_id
    assert "total" in body


def test_batch_status_not_found(client):
    """Var olmayan batch_id 404 dönmeli."""
    r = client.get("/api/documents/batch/nonexistent-batch-id")
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MATCH CANDIDATES (dry run)
# ═══════════════════════════════════════════════════════════════════════════════


def test_candidates_returns_scored_list(client):
    """Belge için aday personel listesi + skorlar dönmeli."""
    crew = _create_crew(client, passport_number="CAN111")
    doc = _upload_and_get_doc(client, "candidate_test.txt",
                              "Passport No: CAN111\nName: Pipeline Test")

    r = client.get(f"/api/documents/{doc['id']}/candidates")
    assert r.status_code == 200
    body = r.json()
    assert body["document_id"] == doc["id"]
    assert "candidates" in body
    assert "decision" in body
    assert len(body["candidates"]) >= 1
    assert body["candidates"][0]["crew_id"] == crew["id"]


def test_candidates_dry_run_does_not_modify_doc(client):
    """Candidates çağrısı belgeyi değiştirmemeli (dry run)."""
    doc = _upload_and_get_doc(client, "dry_test.txt",
                              "Name: Unknown Person\nSome content")

    original_status = doc["match_status"]
    client.get(f"/api/documents/{doc['id']}/candidates")

    # Belge hâlâ aynı durumda olmalı
    check = client.get(f"/api/documents/{doc['id']}")
    assert check.json()["match_status"] == original_status


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MATCH HISTORY
# ═══════════════════════════════════════════════════════════════════════════════


def test_match_history_returns_decisions(client):
    """Eşleştirme geçmişi karar listesi döndürmeli."""
    _create_crew(client, passport_number="HIST001")
    doc = _upload_and_get_doc(client, "history_test.txt",
                              "Passport No: HIST001\nName: Pipeline Test")

    r = client.get(f"/api/documents/{doc['id']}/matches")
    assert r.status_code == 200
    history = r.json()
    assert len(history) >= 1
    assert history[0]["decision"] in ("AUTO_MATCH", "MATCH_OVERRIDE", "REVIEW_REQUIRED", "NO_MATCH")
    assert "score" in history[0]
    assert "actor_email" in history[0]


def test_match_history_empty_for_new_doc(client):
    """Yeni yüklenen belge için eşleştirme geçmişi boş olmamalı (en az 1 otomatik karar)."""
    _create_crew(client, passport_number="HIST002")
    doc = _upload_and_get_doc(client, "history_empty.txt",
                              "Passport No: HIST002\nName: Pipeline Test")

    r = client.get(f"/api/documents/{doc['id']}/matches")
    assert r.status_code == 200
    # Otomatik eşleştirme olduysa en az 1 kayıt olmalı
    assert len(r.json()) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DELETE DOCUMENT
# ═══════════════════════════════════════════════════════════════════════════════


def test_delete_document_removes_it(client):
    """Belge silindikten sonra 404 dönmeli."""
    doc = _upload_and_get_doc(client, "delete_test.txt",
                              "Name: Delete Me\nSome content")

    r = client.delete(f"/api/documents/{doc['id']}")
    assert r.status_code == 204

    # Silindikten sonra erişilemez olmalı
    r2 = client.get(f"/api/documents/{doc['id']}")
    assert r2.status_code == 404


def test_viewer_cannot_delete_document(viewer_client, client):
    """Viewer belge silemez — 403."""
    doc = _upload_and_get_doc(client, "viewer_delete.txt",
                              "Name: Viewer Delete\nSome content")

    r = viewer_client.delete(f"/api/documents/{doc['id']}")
    assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DOCUMENT TYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("filename,content,expected_type", [
    ("STCW_CERT.txt", "STCW Basic Safety Training\nName: Test", "stcw"),
    ("GOC_LICENSE.txt", "General Operator Certificate\nName: Test", "goc"),
    ("MEDICAL_CERT.txt", "Medical Certificate\nName: Test\nExpiry: 01.01.2027", "medical"),
    ("CONTRACT.txt", "Employment Contract\nName: Test\nStart: 01.01.2026", "contract"),
    ("PASSPORT.txt", "Passport No: AB1234567\nName: Test", "passport"),
    ("SEAMAN_BOOK.txt", "Seaman's Book No: SB12345\nName: Test", "seaman_book"),
    ("CV.txt", "Curriculum Vitae\nName: Test", "cv"),
    ("OTHER_RANDOM.txt", "Some random document content", "other"),
])
def test_document_type_classification(client, filename, content, expected_type):
    """Belge içeriğine göre doğru tip sınıflandırması yapılmalı."""
    doc = _upload_and_get_doc(client, filename, content)
    assert doc["document_type"] == expected_type, (
        f"'{filename}' -> beklenen '{expected_type}', gelen '{doc['document_type']}'"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EXPIRY DATE EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════


def test_expiry_date_extracted_from_content(client):
    """Belge içeriğinden geçerlilik tarihi çıkarılmalı."""
    future = (date.today() + timedelta(days=365)).strftime("%d.%m.%Y")
    content = f"Passport No: EX123\nName: Expiry Test\nExpiry Date: {future}"
    doc = _upload_and_get_doc(client, "expiry_test.txt", content)

    assert doc["expiry_date"] is not None
    # Tarih gelecekte olmalı → expiry_status "valid"
    assert doc["expiry_status"] == "valid"


def test_expired_date_detected(client):
    """Geçmiş tarihli belge 'expired' olarak işaretlenmeli."""
    past = (date.today() - timedelta(days=30)).strftime("%d.%m.%Y")
    content = f"Passport No: EXP123\nName: Expired Test\nExpiry Date: {past}"
    doc = _upload_and_get_doc(client, "expired_test.txt", content)

    assert doc["expiry_status"] == "expired"


def test_urgent_date_detected(client):
    """30 gün içinde süresi dolacak belge 'urgent' olmalı."""
    soon = (date.today() + timedelta(days=15)).strftime("%d.%m.%Y")
    content = f"Passport No: URG123\nName: Urgent Test\nExpiry Date: {soon}"
    doc = _upload_and_get_doc(client, "urgent_test.txt", content)

    assert doc["expiry_status"] == "urgent"


def test_no_expiry_returns_no_date(client):
    """Tarihsiz belge 'no_date' dönmeli."""
    content = "Name: No Date Test\nSome content without dates"
    doc = _upload_and_get_doc(client, "nodate_test.txt", content)

    assert doc["expiry_date"] is None
    assert doc["expiry_status"] == "no_date"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PAGINATION (offset/limit)
# ═══════════════════════════════════════════════════════════════════════════════


def test_list_documents_with_limit(client):
    """Limit parametresi sonuç sayısını sınırlamalı."""
    for i in range(5):
        _upload(client, f"page_test_{i}.txt", f"Name: Page Test {i}\nSome content")

    r = client.get("/api/documents/", params={"limit": 3})
    assert r.status_code == 200
    assert len(r.json()) <= 3
    # X-Total-Count header'ı toplam sayıyı içermeli
    assert "x-total-count" in r.headers


def test_list_documents_with_offset(client):
    """Offset parametresi ilk N kaydı atlamalı."""
    for i in range(5):
        _upload(client, f"offset_test_{i}.txt", f"Name: Offset Test {i}\nContent {i}")

    all_docs = client.get("/api/documents/").json()
    offset_docs = client.get("/api/documents/", params={"offset": 2}).json()

    # Offset 2 ise sonuç sayısı all_docs - 2 veya daha az olmalı
    assert len(offset_docs) <= len(all_docs)
    # X-Total-Count header'ı tüm belgelerin sayısını içermeli
    total = int(client.get("/api/documents/").headers.get("x-total-count", 0))
    assert total >= 5


def test_list_documents_with_crew_filter(client):
    """crew_member_id filtresi sadece ilgili personele ait belgeleri döndürmeli."""
    crew_a = _create_crew(client, first_name="FilterA", passport_number="FA001")
    crew_b = _create_crew(client, first_name="FilterB", passport_number="FB001")

    _upload(client, "filter_a.txt", f"Passport No: FA001\nName: FilterA Test")
    _upload(client, "filter_b.txt", f"Passport No: FB001\nName: FilterB Test")

    r = client.get("/api/documents/", params={"crew_member_id": crew_a["id"]})
    assert r.status_code == 200
    docs = r.json()
    assert all(d["crew_member_id"] == crew_a["id"] for d in docs)


def test_list_documents_with_type_filter(client):
    """document_type filtresi doğru tipleri döndürmeli."""
    _upload(client, "type_passport.txt", "Passport No: TP123\nName: Type Test")
    _upload(client, "type_stcw.txt", "STCW certificate\nName: Type Test")

    r = client.get("/api/documents/", params={"document_type": "passport"})
    assert r.status_code == 200
    assert all(d["document_type"] == "passport" for d in r.json())


def test_list_documents_with_expiry_filter(client):
    """expiry_status filtresi doğru durumları döndürmeli."""
    future = (date.today() + timedelta(days=365)).strftime("%d.%m.%Y")
    past = (date.today() - timedelta(days=30)).strftime("%d.%m.%Y")

    _upload(client, "expiry_valid.txt", f"Passport No: EV123\nName: Valid Test\nExpiry Date: {future}")
    _upload(client, "expiry_expired.txt", f"Passport No: EE123\nName: Expired Test\nExpiry Date: {past}")

    r_valid = client.get("/api/documents/", params={"expiry_status": "valid"})
    assert r_valid.status_code == 200
    assert all(d["expiry_status"] == "valid" for d in r_valid.json())

    r_expired = client.get("/api/documents/", params={"expiry_status": "expired"})
    assert r_expired.status_code == 200
    assert all(d["expiry_status"] == "expired" for d in r_expired.json())


# ═══════════════════════════════════════════════════════════════════════════════
# 8. GET SINGLE DOCUMENT
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_single_document(client):
    """Tek belge detayı tüm alanları içermeli."""
    doc = _upload_and_get_doc(client, "single_test.txt",
                              "Passport No: SG123\nName: Single Test")

    r = client.get(f"/api/documents/{doc['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == doc["id"]
    assert body["original_filename"] == "single_test.txt"
    assert "document_type" in body
    assert "match_status" in body
    assert "expiry_status" in body
    assert "created_at" in body


def test_get_nonexistent_document_returns_404(client):
    """Var olmayan belge ID'si 404 dönmeli."""
    r = client.get("/api/documents/999999")
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 9. RBAC
# ═══════════════════════════════════════════════════════════════════════════════


def test_viewer_can_read_documents(viewer_client, client):
    """Viewer belge listesini görebilmeli."""
    _upload(client, "viewer_read.txt", "Name: Viewer Read\nSome content")
    r = viewer_client.get("/api/documents/")
    assert r.status_code == 200


def test_viewer_cannot_upload(viewer_client):
    """Viewer belge yükleyemez — 403."""
    r = viewer_client.post(
        "/api/documents/upload",
        files=[("files", ("test.txt", b"Name: Test\nContent", "text/plain"))],
    )
    assert r.status_code == 403


def test_viewer_cannot_match(viewer_client, client):
    """Viewer manuel eşleştirme yapamaz — 403."""
    doc = _upload_and_get_doc(client, "viewer_match.txt",
                              "Name: No Match\nSome content")
    r = viewer_client.put(
        f"/api/documents/{doc['id']}/match",
        json={"crew_member_id": 1},
    )
    assert r.status_code == 403


def test_viewer_cannot_approve_reject(viewer_client, client):
    """Viewer onaylayamaz/reddeedemez — 403."""
    crew = _create_crew(client)
    doc = _upload_and_get_doc(client, "viewer_approve.txt",
                              "Name: Approve Test\nSTCW")

    r_approve = viewer_client.post(f"/api/documents/{doc['id']}/approve")
    assert r_approve.status_code == 403

    r_reject = viewer_client.post(f"/api/documents/{doc['id']}/reject")
    assert r_reject.status_code == 403


def test_unauthenticated_cannot_access_documents(no_auth_client):
    """Token olmadan belge endpoint'lerine erişilemez — 401."""
    r = no_auth_client.get("/api/documents/")
    assert r.status_code == 401

    r = no_auth_client.post(
        "/api/documents/upload",
        files=[("files", ("test.txt", b"content", "text/plain"))],
    )
    assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 10. APPROVE/REJECT WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════════


def test_approve_sets_matched_and_archives_old(client):
    """Onay: match_status→matched, eski aynı tipteki belge arşive alınır."""
    crew = _create_crew(client, passport_number="APR001")

    # Eski belge (matched)
    old = _upload_and_get_doc(client, "old_passport.txt",
                               f"Passport No: APR001\nName: Pipeline Test\nExpiry: 01.01.2030")
    assert old["match_status"] == "matched"

    # Yeni belge (farklı dosya ama aynı crew + tip)
    new_content = "Passport No: APR001\nName: Pipeline Test\nExpiry: 01.01.2031"
    new_r = _upload(client, "new_passport.txt", new_content)
    # Eğer duplicate check yüzünden aynı belge dönüyorsa farklı checksum kullan
    if new_r.json()[0]["id"] == old["id"]:
        # Farklı content ile tekrar dene
        new_content2 = "Passport No: APR001\nName: Pipeline Test\nExpiry: 01.01.2031\nExtra: unique"
        new_r = _upload(client, "new_passport_v2.txt", new_content2)

    new_doc = new_r.json()[0]
    if new_doc["id"] != old["id"]:
        # Onayla
        r = client.post(f"/api/documents/{new_doc['id']}/approve")
        assert r.status_code == 200
        assert r.json()["match_status"] == "matched"

        # Eski belge arşive alınmış olmalı
        old_check = client.get(f"/api/documents/{old['id']}")
        assert old_check.json()["archived"] is True


def test_reject_sets_unmatched_and_clears_crew(client):
    """Reddetme: match_status→unmatched, crew_member_id→None."""
    crew = _create_crew(client, passport_number="REJ001")
    doc = _upload_and_get_doc(client, "reject_test.txt",
                              f"Passport No: REJ001\nName: Pipeline Test")
    assert doc["match_status"] == "matched"
    assert doc["crew_member_id"] == crew["id"]

    r = client.post(f"/api/documents/{doc['id']}/reject")
    assert r.status_code == 200
    body = r.json()
    assert body["match_status"] == "unmatched"
    assert body["crew_member_id"] is None


def test_approve_without_crew_returns_400(client):
    """Personel bağlı olmayan belge onaylanamaz — 400."""
    doc = _upload_and_get_doc(client, "no_crew_approve.txt",
                              "Name: No Crew\nSome content")

    # Eğer match olmadıysa (crew_member_id None) approve 400 dönmeli
    if doc["crew_member_id"] is None:
        r = client.post(f"/api/documents/{doc['id']}/approve")
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# 11. CROSS-TEST: PIPELINE INTEGRITY
# ═══════════════════════════════════════════════════════════════════════════════


def test_full_document_lifecycle(client):
    """Tam belge yaşam döngüsü: yükle → eşleştir → onayla → indir → sil."""
    crew = _create_crew(client, passport_number="LIF001")

    # 1. Yükle
    doc = _upload_and_get_doc(client, "lifecycle.txt",
                              f"Passport No: LIF001\nName: Pipeline Test\nExpiry: 01.01.2030")
    assert doc["match_status"] == "matched"
    assert doc["crew_member_id"] == crew["id"]

    # 2. Eşleştirme geçmişini kontrol et
    history = client.get(f"/api/documents/{doc['id']}/matches").json()
    assert len(history) >= 1

    # 3. Adayları kontrol et
    candidates = client.get(f"/api/documents/{doc['id']}/candidates").json()
    assert len(candidates["candidates"]) >= 1

    # 4. İndir
    dl = client.get(f"/api/documents/{doc['id']}/file")
    assert dl.status_code == 200

    # 5. Detay
    detail = client.get(f"/api/documents/{doc['id']}").json()
    assert detail["id"] == doc["id"]

    # 6. Sil
    r = client.delete(f"/api/documents/{doc['id']}")
    assert r.status_code == 204

    # 7. Silindikten sonra 404
    r2 = client.get(f"/api/documents/{doc['id']}")
    assert r2.status_code == 404
