"""Phase 4B — Uygunluk motoru, kadro planı, bildirim, CSV, onay kuyruğu, portal."""

from datetime import UTC, date, datetime, timedelta

from app.models.crew_member import CrewMember
from app.models.document import Document
from app.models.ship import Ship
from tests.conftest import _create_user


_doc_counter = 0

def _make_crew(db, first_name="Ahmet", last_name="Yılmaz", position="Kaptan", **kw):
    crew = CrewMember(
        first_name=first_name,
        last_name=last_name,
        position=position,
        nationality=kw.pop("nationality", "Türk"),
        availability=kw.pop("availability", "available"),
        experience_years=kw.pop("experience_years", 8),
        status="active",
        **kw,
    )
    db.add(crew)
    db.commit()
    db.refresh(crew)
    return crew


def _make_ship(db, name="MV Test 1"):
    ship = Ship(name=name, imo_number="IMO1234567", flag="TR", status="active")
    db.add(ship)
    db.commit()
    db.refresh(ship)
    return ship


def _make_doc(db, crew_id, document_type="passport", match_status="matched", expiry=None):
    global _doc_counter
    _doc_counter += 1
    unique = f"{int(datetime.now(UTC).timestamp())}-{_doc_counter}"
    doc = Document(
        original_filename=f"{document_type}_{crew_id}.pdf",
        stored_filename=f"{document_type}_{crew_id}_{unique}.pdf",
        storage_path=f"test/{document_type}_{crew_id}.pdf",
        checksum=f"hash-{document_type}-{crew_id}-{unique}",
        file_size=100,
        mime_type="application/pdf",
        document_type=document_type,
        match_status=match_status,
        crew_member_id=crew_id,
        expiry_date=expiry,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _crew_user(db, crew_id, role="crew", email="crew@test.example"):
    user = _create_user(db, email, "crew-pass-123", role, full_name="Crew User")
    user.crew_member_id = crew_id
    db.commit()
    db.refresh(user)
    return user


# ── 1. UYGUNLUK MOTORU ──────────────────────────────────────────────────────


def test_eligibility_returns_scored_candidates(client, db_session):
    _make_crew(db_session, position="Kaptan", experience_years=10)
    _make_crew(db_session, position="Kaptan", experience_years=2)
    response = client.get("/api/crew/eligible", params={"position": "Kaptan", "min_score": 0})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert all("score" in r and "documents_status" in r and "breakdown" in r for r in results)
    assert results[0]["score"] >= results[1]["score"]


def test_eligibility_missing_docs_lowers_score(client, db_session):
    crew = _make_crew(db_session, position="Elektrikçi")
    _make_doc(db_session, crew.id, "passport")
    response = client.get("/api/crew/eligible", params={"position": "Elektrikçi", "min_score": 0})
    results = response.json()
    crew_row = next(r for r in results if r["crew_id"] == crew.id)
    # Eksik zorunlu belgeler skoru düşürmeli ama yine de dönmeli.
    assert 0 < crew_row["score"] < 100
    assert crew_row["documents_status"].get("seaman_book") in ("missing", None)


def test_eligible_respects_availability(client, db_session):
    _make_crew(db_session, position="Kaptan", availability="not_available")
    response = client.get("/api/crew/eligible", params={"position": "Kaptan", "min_score": 0})
    assert all(r["availability"] != "not_available" for r in response.json())


# ── 2. GEMİ KADRO PLANI ─────────────────────────────────────────────────────


def test_ship_staffing_add_and_delete_position(client, db_session):
    ship = _make_ship(db_session)
    # Boş kadro
    response = client.get(f"/api/ships/{ship.id}/staffing")
    assert response.status_code == 200 and response.json() == []

    # Pozisyon ekle
    response = client.post(f"/api/ships/{ship.id}/positions", json={"position": "Kaptan", "required_count": 2})
    assert response.status_code == 201
    pos_id = response.json()["id"]

    staffing = client.get(f"/api/ships/{ship.id}/staffing").json()
    assert len(staffing) == 1
    assert staffing[0]["position"] == "Kaptan"
    assert staffing[0]["required"] == 2 and staffing[0]["filled"] == 0 and staffing[0]["open"] == 2

    # Sil
    response = client.delete(f"/api/ships/positions/{pos_id}")
    assert response.status_code == 204
    assert client.get(f"/api/ships/{ship.id}/staffing").json() == []


def test_staffing_position_upsert(client, db_session):
    ship = _make_ship(db_session)
    client.post(f"/api/ships/{ship.id}/positions", json={"position": "Aşçı", "required_count": 1})
    response = client.post(f"/api/ships/{ship.id}/positions", json={"position": "Aşçı", "required_count": 3})
    assert response.status_code == 201  # upsert: duplicate → günceller
    staffing = client.get(f"/api/ships/{ship.id}/staffing").json()
    assert len(staffing) == 1 and staffing[0]["required"] == 3


def test_viewer_cannot_modify_staffing(viewer_client, db_session):
    ship = _make_ship(db_session)
    response = viewer_client.post(f"/api/ships/{ship.id}/positions", json={"position": "Kaptan", "required_count": 1})
    assert response.status_code in (401, 403)


# ── 3. BİLDİRİMLER ──────────────────────────────────────────────────────────


def test_notifications_generate_list_read(client, db_session):
    crew = _make_crew(db_session)
    _make_doc(db_session, crew.id, "medical", expiry=date.today() + timedelta(days=10))
    _make_doc(db_session, crew.id, "stcw", "pending_approval")

    response = client.post("/api/notifications/generate")
    assert response.status_code == 200
    assert response.json()["created"] >= 1  # belge bitişi + onay bekleme bildirimi

    items = client.get("/api/notifications/").json()
    assert len(items) >= 1
    nid = items[0]["id"]
    assert client.post(f"/api/notifications/{nid}/read").status_code in (200, 204)
    refreshed = client.get("/api/notifications/").json()
    assert next(n for n in refreshed if n["id"] == nid)["read"] is True


# ── 4. CSV DIŞA / İÇE AKTARMA ───────────────────────────────────────────────


def test_csv_export(client, db_session):
    _make_crew(db_session, first_name="Export", last_name="Kişi")
    response = client.get("/api/crew/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Export" in response.text


def test_csv_import_preview_and_confirm(client, db_session):
    _make_crew(db_session, first_name="Mevcut", last_name="Kayıt", email="mevcut@example.com")
    content = (
        "first_name,last_name,position,rank,nationality,email,experience_years\n"
        "Yeni,Biri,Kaptan,Kaptan,Türk,yeni@example.com,5\n"
        "Mevcut,Kayıt,Kaptan,Kaptan,Türk,mevcut@example.com,5\n"
    )
    preview = client.post("/api/crew/import/preview", json={"content": content})
    assert preview.status_code == 200
    body = preview.json()
    assert body["total"] == 2
    assert body["new_count"] == 1
    assert body["existing_count"] == 1
    assert body["conflict_count"] == 0

    confirmed = client.post("/api/crew/import/confirm", json={"rows": body["rows"]})
    assert confirmed.status_code == 200
    assert confirmed.json()["created"] == 1


def test_viewer_cannot_import(viewer_client):
    response = viewer_client.post("/api/crew/import/confirm", json={"rows": []})
    assert response.status_code in (401, 403)


def test_csv_import_rejects_invalid_email(client, db_session):
    """Geçersiz e-posta içeren CSV satırları önizlemede hatalı sayılmalı,
    confirm'da DB'ye yazılmamalı (önceki davranış: "5" gibi değerler
    email sütununa giriyor ve /api/crew/ listesini 500'e düşürüyordu)."""
    content = (
        "first_name,last_name,position,rank,nationality,email,experience_years\n"
        "Hatali,Satir,Kaptan,Kaptan,Türk,5,3\n"
        "Gecerli,Kisi,Kaptan,Kaptan,Türk,gecerli@example.com,3\n"
    )
    preview = client.post("/api/crew/import/preview", json={"content": content})
    assert preview.status_code == 200
    body = preview.json()
    assert body["error_count"] == 1
    assert body["new_count"] == 1
    assert all(row["first_name"] != "Hatali" for row in body["rows"])

    confirmed = client.post("/api/crew/import/confirm", json={"rows": body["rows"]})
    assert confirmed.status_code == 200
    assert confirmed.json()["created"] == 1

    # Geçersiz email DB'ye girmedi ve personel listesi 500 vermiyor
    crew = db_session.query(CrewMember).filter(CrewMember.first_name == "Gecerli").one()
    assert crew.email == "gecerli@example.com"
    assert db_session.query(CrewMember).filter(CrewMember.first_name == "Hatali").count() == 0
    listing = client.get("/api/crew/")
    assert listing.status_code == 200


# ── 6. PHASE 6 — AYARLAR / MASKELEME / KULLANICI-PERSONEL / E-POSTA ────────


def test_settings_crud_and_validation(client, viewer_client):
    # Admin: kaydet ve oku
    response = client.put("/api/settings", json={"values": {"whatsapp_admin_number": "+90 555 111 22 33"}})
    assert response.status_code == 200
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert response.json()["values"]["whatsapp_admin_number"] == "+90 555 111 22 33"
    # Geçersiz numara reddedilir
    response = client.put("/api/settings", json={"values": {"whatsapp_admin_number": "abc"}})
    assert response.status_code == 400
    # Viewer erişemez
    assert viewer_client.get("/api/settings").status_code == 403


def test_crew_masking_for_viewer(client, viewer_client, db_session):
    crew = _make_crew(db_session, first_name="Mask", last_name="Kişi", passport_number="U6012234", seaman_book_number="TR-SB-10023146")
    full = client.get(f"/api/crew/{crew.id}")
    assert full.status_code == 200
    assert full.json()["passport_number"] == "U6012234"
    masked = viewer_client.get(f"/api/crew/{crew.id}")
    assert masked.status_code == 200
    assert masked.json()["passport_number"] == "U6****34"
    assert masked.json()["seaman_book_number"] == "TR**********46"
    listing = viewer_client.get("/api/crew/")
    assert any(m["passport_number"] == "U6****34" for m in listing.json())


def test_crew_user_requires_crew_link(client, db_session):
    crew = _make_crew(db_session, first_name="Emre", last_name="Kaya")
    bad = client.post("/api/auth/users", json={
        "email": "bad.crew@test.example", "password": "Password123!", "full_name": "Bad", "role": "crew"})
    assert bad.status_code == 400
    good = client.post("/api/auth/users", json={
        "email": "good.crew@test.example", "password": "Password123!", "full_name": "Good",
        "role": "crew", "crew_member_id": crew.id})
    assert good.status_code == 201
    assert good.json()["crew_member_id"] == crew.id
    # Bağlantı güncellenebilir / temizlenebilir
    updated = client.patch(f"/api/auth/users/{good.json()['id']}", json={"crew_member_id": None})
    assert updated.status_code == 200
    assert updated.json()["crew_member_id"] is None


def test_bulk_email_queued_without_smtp(client, viewer_client, db_session):
    for i in range(2):
        _make_crew(db_session, first_name=f"Mail{i}", last_name="Kişi", email=f"mail{i}@test.example")
    response = client.post("/api/notifications/send-bulk", json={
        "crew_ids": [1, 2], "subject": "Test konu", "body": "Merhaba"})
    assert response.status_code == 200
    body = response.json()
    assert body["recipients"] == 2
    assert body["pending"] == 2  # SMTP yok -> kuyrukta
    assert body["smtp_configured"] is False
    # Viewer yapamaz
    assert viewer_client.post("/api/notifications/send-bulk", json={
        "crew_ids": [1], "subject": "x", "body": "y"}).status_code == 403


def test_document_response_includes_archived(client, db_session):
    """DocumentResponse API'de archived bayrağı görünmeli (arşiv/versiyonlama kontrolü)."""
    crew = _make_crew(db_session)
    old = _make_doc(db_session, crew.id, "passport", "matched")
    old.archived_at = datetime.now(UTC).replace(tzinfo=None)
    _make_doc(db_session, crew.id, "medical", "matched")  # aktif belge
    db_session.commit()
    docs = client.get(f"/api/documents/?crew_member_id={crew.id}")
    assert docs.status_code == 200
    assert any(d.get("archived") is True for d in docs.json())
    assert any(d.get("archived") is False for d in docs.json())


# ── 5. BELGE ONAY KUYRUĞU ───────────────────────────────────────────────────


def test_approve_document_archives_old(client, db_session):
    crew = _make_crew(db_session)
    old = _make_doc(db_session, crew.id, "passport", "matched")
    new = _make_doc(db_session, crew.id, "passport", "pending_approval")
    assert new.archived_at is None

    response = client.post(f"/api/documents/{new.id}/approve")
    assert response.status_code == 200
    assert response.json()["match_status"] == "matched"

    db_session.refresh(old)
    db_session.refresh(new)
    assert old.archived_at is not None  # eski belge arşive
    assert new.archived_at is None


def test_reject_document_unmatches(client, db_session):
    crew = _make_crew(db_session)
    doc = _make_doc(db_session, crew.id, "medical", "pending_approval")
    response = client.post(f"/api/documents/{doc.id}/reject")
    assert response.status_code == 200
    body = response.json()
    assert body["match_status"] == "unmatched"
    assert body["crew_member_id"] is None


def test_review_queue_includes_pending_approval(client, db_session):
    crew = _make_crew(db_session)
    _make_doc(db_session, crew.id, "stcw", "pending_approval")
    queue = client.get("/api/documents/review").json()
    assert any(d["match_status"] == "pending_approval" for d in queue)


def test_viewer_cannot_approve(viewer_client, db_session):
    crew = _make_crew(db_session)
    doc = _make_doc(db_session, crew.id, "passport", "pending_approval")
    response = viewer_client.post(f"/api/documents/{doc.id}/approve")
    assert response.status_code in (401, 403)


# ── 6. PERSONEL PORTALI (crew rolü) ─────────────────────────────────────────


def test_portal_me_and_contact_update(db_session):
    from fastapi.testclient import TestClient
    from app.db.database import get_db
    from app.main import app

    crew = _make_crew(db_session, email="crew-p@example.com", phone="+905551234567")
    user = _crew_user(db_session, crew.id, email="crew-p@example.com")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/auth/login", json={"email": "crew-p@example.com", "password": "crew-pass-123"}
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = test_client.get("/api/portal/me", headers=headers)
        assert me.status_code == 200, me.text
        assert me.json()["profile"]["first_name"] == "Ahmet"
        assert me.json()["profile"]["email"] == "crew-p@example.com"

        updated = test_client.put(
            "/api/portal/contact",
            headers=headers,
            json={"phone": "+901112223344", "email": "yeni-mail@example.com"},
        )
        assert updated.status_code == 200, updated.text
    app.dependency_overrides.clear()

    db_session.refresh(crew)
    assert crew.phone == "+901112223344"
    assert crew.email == "yeni-mail@example.com"


def test_admin_cannot_use_portal(client):
    response = client.get("/api/portal/me")
    assert response.status_code in (400, 403)


# ── 7. DASHBOARD ÖZETİ ──────────────────────────────────────────────────────


def test_dashboard_summary_counts(client, db_session):
    crew = _make_crew(db_session, position="Kaptan")
    ship = _make_ship(db_session)
    client.post(f"/api/ships/{ship.id}/positions", json={"position": "Kaptan", "required_count": 1})
    _make_doc(
        db_session, crew.id, "passport",
        expiry=date.today() - timedelta(days=5),
    )
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["documents"]["expired"] >= 1
    assert body["ships"]["open_positions_total"] >= 1
    assert any(t["type"] == "staffing" for t in body["tasks"])
    assert any(t["type"] == "document" for t in body["tasks"])


# ── 8. PHASE 7 — İŞ İLANLARI / BAŞVURU / İLETİŞİM / FİLTRE ──────────────────


def test_crew_availability_filter(client, db_session):
    _make_crew(db_session, first_name="Müsait", availability="available")
    _make_crew(db_session, first_name="İzinli", availability="on_leave")
    _make_crew(db_session, first_name="Değil", availability="not_available")
    response = client.get("/api/crew/?availability=available")
    assert response.status_code == 200
    names = [c["first_name"] for c in response.json()]
    assert "Müsait" in names
    assert "İzinli" not in names
    assert "Değil" not in names


def test_jobs_full_flow(client, db_session):
    ship = _make_ship(db_session)
    crew = _make_crew(db_session)
    created = client.post("/api/jobs/", json={"title": "Elektrikçi", "position": "Elektrikçi", "ship_id": ship.id})
    assert created.status_code == 201, created.text
    jid = created.json()["id"]
    assert created.json()["ship_name"] == ship.name

    listing = client.get("/api/jobs/")
    assert listing.status_code == 200
    assert any(j["id"] == jid for j in listing.json())

    applied = client.post(f"/api/jobs/{jid}/apply", json={"crew_member_id": crew.id})
    assert applied.status_code == 201, applied.text
    aid = applied.json()["id"]
    assert applied.json()["status"] == "applied"

    dup = client.post(f"/api/jobs/{jid}/apply", json={"crew_member_id": crew.id})
    assert dup.status_code == 409

    apps = client.get("/api/jobs/applications/all")
    assert apps.status_code == 200
    assert any(a["id"] == aid for a in apps.json())

    patched = client.patch(f"/api/jobs/applications/{aid}", json={"status": "accepted"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "accepted"

    closed = client.patch(f"/api/jobs/{jid}", json={"status": "closed"})
    assert closed.status_code == 200
    blocked = client.post(f"/api/jobs/{jid}/apply", json={"crew_member_id": crew.id})
    assert blocked.status_code == 400

    deleted = client.delete(f"/api/jobs/{jid}")
    assert deleted.status_code == 204


def test_jobs_viewer_and_hr_roles(viewer_client, hr_client, db_session):
    ship = _make_ship(db_session)
    denied = viewer_client.post("/api/jobs/", json={"title": "x", "position": "Kaptan", "ship_id": ship.id})
    assert denied.status_code == 403
    ok = hr_client.post("/api/jobs/", json={"title": "x", "position": "Kaptan", "ship_id": ship.id})
    assert ok.status_code == 201, ok.text
    listing = viewer_client.get("/api/jobs/")
    assert listing.status_code == 200


def test_contact_endpoint(client, viewer_client):
    updated = client.put("/api/settings", json={"values": {"whatsapp_admin_number": "+905323276121"}})
    assert updated.status_code == 200, updated.text
    contact = viewer_client.get("/api/settings/contact")
    assert contact.status_code == 200
    assert contact.json()["whatsapp_admin_number"] == "+905323276121"


# ── 9. PHASE 8 — WHATSAPP BUSINESS API ALTYAPISI + İLAN YAYINI ──────────────


def test_whatsapp_webhook_verify(client, db_session):
    """Meta webhook doğrulaması: doğru token challenge döner, yanlış token 403."""
    client.put("/api/settings", json={"values": {"whatsapp_webhook_verify_token": "test-verify-123"}})
    ok = client.get("/api/webhooks/whatsapp",
                    params={"hub.mode": "subscribe", "hub.verify_token": "test-verify-123", "hub.challenge": "ch-42"})
    assert ok.status_code == 200
    assert ok.json() == "ch-42"
    bad = client.get("/api/webhooks/whatsapp",
                     params={"hub.mode": "subscribe", "hub.verify_token": "yanlis", "hub.challenge": "ch-42"})
    assert bad.status_code == 403


def test_whatsapp_webhook_receive(client, db_session):
    """Webhook mesaj alımı: doğrulama olmadan bile loglanır, 200 döner."""
    payload = {
        "entry": [{"changes": [{"value": {
            "contacts": [{"wa_id": "905323276121"}],
            "messages": [{"id": "wamid-1"}],
        }}]}]
    }
    response = client.post("/api/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json()["received"] == 1


def test_whatsapp_queue_requires_config(client, db_session):
    """Token yoksa sahte başarı üretilmez: mesajlar pending kalır, publication 'queued'."""
    ship = _make_ship(db_session)
    crew = _make_crew(db_session, first_name="Wa", last_name="Kişi", phone="+90 532 327 61 21")
    created = client.post("/api/jobs/", json={"title": "Kaptan", "position": "Kaptan", "ship_id": ship.id})
    jid = created.json()["id"]
    client.patch(f"/api/jobs/{jid}", json={"status": "open"})

    published = client.post(f"/api/jobs/{jid}/publish",
                            json={"channels": ["whatsapp"], "crew_ids": [crew.id]})
    assert published.status_code == 201, published.text
    results = {r["channel"]: r for r in published.json()["results"]}
    assert results["whatsapp"]["status"] == "queued"  # token yok → kuyrukta

    messages = client.get(f"/api/jobs/{jid}/whatsapp-messages").json()
    assert len(messages) == 1
    assert messages[0]["status"] == "pending"
    assert messages[0]["phone"] == "905323276121"
    assert "yapılandırılmadı" in messages[0]["last_error"]  # sahte başarı yok

    # Aynı ilana tekrar publish → duplicate koruması (yeni satır oluşmaz)
    client.post(f"/api/jobs/{jid}/publish", json={"channels": ["whatsapp"], "crew_ids": [crew.id]})
    messages = client.get(f"/api/jobs/{jid}/whatsapp-messages").json()
    assert len(messages) == 1


def test_publish_crew_portal_and_templates(client, db_session):
    ship = _make_ship(db_session)
    tpl = client.post("/api/job-templates", json={
        "name": "Varsayılan", "body": "{{position}} — {{vessel}} — {{salary}} {{currency}}",
        "is_default": True})
    assert tpl.status_code == 201, tpl.text

    created = client.post("/api/jobs/", json={
        "title": "Elektrikçi", "position": "Elektrikçi", "ship_id": ship.id,
        "salary": "2500", "currency": "USD"})
    jid = created.json()["id"]
    client.patch(f"/api/jobs/{jid}", json={"status": "open"})

    published = client.post(f"/api/jobs/{jid}/publish",
                            json={"channels": ["crew_portal", "instagram"], "template_id": tpl.json()["id"]})
    assert published.status_code == 201, published.text
    results = {r["channel"]: r for r in published.json()["results"]}
    assert results["crew_portal"]["status"] == "sent"
    # Instagram credential yok → CONFIGURATION REQUIRED (skipped), sahte başarı yok
    assert results["instagram"]["status"] == "skipped"

    pubs = client.get(f"/api/jobs/{jid}/publications").json()
    assert len(pubs) == 2


def test_crew_job_seeking_and_portal_apply(client, db_session):
    from fastapi.testclient import TestClient
    from app.db.database import get_db
    from app.main import app

    ship = _make_ship(db_session)
    crew = _make_crew(db_session, first_name="Arayan", last_name="Personel")
    _crew_user(db_session, crew.id, email="arayan@test.example")

    # Admin ilan oluşturup yayınlıyor (client fixture override'ı bozulmadan)
    created = client.post("/api/jobs/", json={"title": "Kaptan", "position": "Kaptan", "ship_id": ship.id})
    jid = created.json()["id"]
    client.patch(f"/api/jobs/{jid}", json={"status": "open"})
    client.post(f"/api/jobs/{jid}/publish", json={"channels": ["crew_portal"]})

    # Crew portal akışı — get_db override ile aynı in-memory DB
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        login = test_client.post("/api/auth/login", json={"email": "arayan@test.example", "password": "crew-pass-123"})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        seeking = test_client.patch("/api/portal/job-seeking", headers=headers, json={"job_seeking": True})
        assert seeking.status_code == 200, seeking.text
        assert seeking.json()["job_seeking"] is True

        me = test_client.get("/api/portal/me", headers=headers)
        assert me.json()["profile"]["job_seeking"] is True

        jobs = test_client.get("/api/portal/jobs", headers=headers)
        assert jobs.status_code == 200, jobs.text
        assert any(j["id"] == jid for j in jobs.json())
        applied = test_client.post(f"/api/portal/jobs/{jid}/apply", headers=headers)
        assert applied.status_code in (200, 201), applied.text
        assert applied.json()["status"] == "applied"
    app.dependency_overrides.clear()


def test_viewer_cannot_publish_or_template(client, viewer_client, db_session):
    ship = _make_ship(db_session)
    created = client.post("/api/jobs/", json={"title": "Kaptan", "position": "Kaptan", "ship_id": ship.id})
    jid = created.json()["id"]
    client.patch(f"/api/jobs/{jid}", json={"status": "open"})
    denied = viewer_client.post(f"/api/jobs/{jid}/publish", json={"channels": ["crew_portal"], "crew_ids": []})
    assert denied.status_code == 403
    denied_tpl = viewer_client.post("/api/job-templates", json={"name": "x", "body": "y"})
    assert denied_tpl.status_code == 403
    # Viewer ilanları görebilir
    assert viewer_client.get("/api/jobs/").status_code == 200
