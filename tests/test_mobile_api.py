"""M1 Mobile — backend API testleri.

Kapsam: self-registration + admin onayı, portal genişletmeleri (me/full,
preferences, contracts/me, vessel/me, documents, file, applications,
recommended), mesajlaşma, cihaz kaydı, deaktivasyon, RBAC/IDOR.
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD

CREW_EMAIL = "crew.mobile@test.example"
CREW_PASSWORD = "crew-pass-123"


# ── Yardımcılar ─────────────────────────────────────────────────────────────


def _make_crew(admin_client, email=CREW_EMAIL, password=CREW_PASSWORD,
               first="Crew", last="Mobile", position="Aday"):
    """Admin API ile gerçek (aktif) bir crew hesabı + CrewMember oluşturur."""
    response = admin_client.post("/api/crew/", json={
        "first_name": first, "last_name": last, "position": position,
    })
    assert response.status_code == 201, response.text
    crew_id = response.json()["id"]
    response = admin_client.post("/api/auth/users", json={
        "email": email, "password": password, "full_name": f"{first} {last}",
        "role": "crew", "crew_member_id": crew_id,
    })
    assert response.status_code == 201, response.text
    user_id = response.json()["id"]
    return crew_id, user_id


def _crew_client(admin_client, email=CREW_EMAIL, password=CREW_PASSWORD):
    """Login edilmiş crew TestClient'ı döndürür (conftest override aktifken)."""
    response = admin_client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    test_client = TestClient(app)
    test_client.headers["Authorization"] = f"Bearer {token}"
    return test_client


def _register(admin_client, email="new.crew@test.example"):
    return admin_client.post("/api/auth/register", json={
        "first_name": "Yeni", "last_name": "Personel", "email": email,
        "phone": "+90 555 111 22 33", "password": "password123",
        "nationality": "Türkiye", "date_of_birth": "1990-01-01",
    })


# ── Kayıt + onay akışı ──────────────────────────────────────────────────────


def test_register_creates_pending_account(no_auth_client):
    response = _register(no_auth_client)
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "pending_review"


def test_register_duplicate_email_conflict(no_auth_client):
    assert _register(no_auth_client).status_code == 201
    assert _register(no_auth_client).status_code == 409


def test_register_pending_user_cannot_login(no_auth_client):
    _register(no_auth_client, email="pending@test.example")
    response = no_auth_client.post("/api/auth/login", json={
        "email": "pending@test.example", "password": "password123",
    })
    assert response.status_code == 403  # is_active=False


def test_admin_approve_activates_account(no_auth_client, client):
    _register(no_auth_client, email="approve@test.example")
    users = client.get("/api/auth/users").json()
    user_id = next(u["id"] for u in users if u["email"] == "approve@test.example")
    assert user_id is not None

    response = client.patch(f"/api/auth/users/{user_id}/approve")
    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is True

    # Onay sonrası giriş açılır
    login = no_auth_client.post("/api/auth/login", json={
        "email": "approve@test.example", "password": "password123",
    })
    assert login.status_code == 200


def test_approve_requires_admin(viewer_client, no_auth_client, client):
    _register(no_auth_client, email="approve2@test.example")
    users = client.get("/api/auth/users").json()
    user_id = next(u["id"] for u in users if u["email"] == "approve2@test.example")
    assert viewer_client.patch(f"/api/auth/users/{user_id}/approve").status_code == 403


def test_crew_cannot_manage_users(client):
    crew_id, _ = _make_crew(client)
    crew = _crew_client(client)
    assert crew.get("/api/auth/users").status_code == 403
    assert crew.get("/api/audit-logs/").status_code == 403
    assert crew.post("/api/auth/users", json={
        "email": "x@test.example", "password": "password123",
        "full_name": "X", "role": "viewer",
    }).status_code == 403


# ── Portal genişletmeleri ───────────────────────────────────────────────────


def test_crew_full_profile(client):
    crew_id, _ = _make_crew(client)
    crew = _crew_client(client)
    response = crew.get("/api/portal/me/full")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["profile"]["first_name"] == "Crew"
    assert body["profile"]["position"] == "Aday"
    assert body["eligibility"]["score"] >= 0
    assert body["contract"] is None
    assert body["vessel"] is None


def test_crew_preferences_update(client):
    _make_crew(client)
    crew = _crew_client(client)
    response = crew.put("/api/portal/preferences", json={
        "job_preferences": {"positions": ["Kaptan", "2. Kaptan"], "region": "Worldwide"},
        "available_from": "2026-10-01",
        "vessel_types_experience": "container, bulk",
        "expected_salary_min": 3000,
        "expected_salary_max": 4000,
        "expected_salary_currency": "USD",
        "expected_salary_period": "monthly",
    })
    assert response.status_code == 200, response.text

    body = crew.get("/api/portal/me/full").json()
    profile = body["profile"]
    assert profile["job_preferences"]["positions"] == ["Kaptan", "2. Kaptan"]
    assert profile["available_from"] == "2026-10-01"
    assert profile["expected_salary_min"] == 3000
    assert profile["expected_salary_max"] == 4000
    assert profile["expected_salary_currency"] == "USD"


def test_crew_contracts_and_vessel(client):
    crew_id, _ = _make_crew(client)
    ship = client.post("/api/ships/", json={"name": "MV Test", "imo_number": "9998887"})
    assert ship.status_code == 201, ship.text
    ship_id = ship.json()["id"]

    today = date.today()
    end = today + timedelta(days=45)
    contract = client.post("/api/contracts/", json={
        "crew_member_id": crew_id, "ship_id": ship_id,
        "contract_number": "MOB-2026-0001", "contract_type": "Aylık",
        "start_date": today.isoformat(), "end_date": end.isoformat(),
    })
    assert contract.status_code == 201, contract.text
    assignment = client.post("/api/assignments/", json={
        "ship_id": ship_id, "crew_member_id": crew_id, "position": "Gemici",
        "start_date": today.isoformat(), "end_date": end.isoformat(),
    })
    assert assignment.status_code == 201, assignment.text

    crew = _crew_client(client)
    contracts = crew.get("/api/portal/contracts/me").json()
    assert len(contracts) == 1
    assert contracts[0]["days_remaining"] == 45
    assert contracts[0]["ship_name"] == "MV Test"

    vessel = crew.get("/api/portal/vessel/me").json()
    assert vessel is not None
    assert vessel["name"] == "MV Test"
    assert vessel["position"] == "Gemici"

    full = crew.get("/api/portal/me/full").json()
    assert full["contract"]["days_remaining"] == 45
    assert full["vessel"]["name"] == "MV Test"


def test_crew_documents_list_and_download_own(client):
    _make_crew(client)
    crew = _crew_client(client)
    upload = crew.post(
        "/api/portal/documents",
        files={"file": ("cengiz_cv.txt", b"CV icerik - Cengiz Kilic", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["id"]
    assert upload.json()["status"] == "pending_approval"

    docs = crew.get("/api/portal/documents").json()
    assert len(docs) == 1
    assert docs[0]["document_type"] == "cv"
    assert docs[0]["status"] == "pending_approval"

    download = crew.get(f"/api/portal/documents/{document_id}/file")
    assert download.status_code == 200
    assert b"CV icerik" in download.content


def test_crew_cannot_download_other_crew_document(client):
    _make_crew(client, email="crew.a@test.example")
    crew_a = _crew_client(client, email="crew.a@test.example")
    upload = crew_a.post(
        "/api/portal/documents",
        files={"file": ("a.txt", b"belge a", "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    _make_crew(client, email="crew.b@test.example")
    crew_b = _crew_client(client, email="crew.b@test.example")
    # Başkasının belgesine erişim: 404 (IDOR koruması)
    assert crew_b.get(f"/api/portal/documents/{document_id}/file").status_code == 404


def test_crew_apply_with_match_score_and_applications(client):
    crew_id, _ = _make_crew(client, position="Kaptan")
    posting = client.post("/api/jobs/", json={"title": "Kaptan Aranıyor", "position": "Kaptan"})
    assert posting.status_code == 201, posting.text
    posting_id = posting.json()["id"]

    crew = _crew_client(client)
    response = crew.post(f"/api/portal/jobs/{posting_id}/apply", json={})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "applied"
    assert isinstance(response.json()["match_score"], int)

    apps = crew.get("/api/portal/applications").json()
    assert len(apps) == 1
    assert apps[0]["title"] == "Kaptan Aranıyor"
    assert apps[0]["match_score"] is not None

    # Duplicate başvuru 409
    assert crew.post(f"/api/portal/jobs/{posting_id}/apply", json={}).status_code == 409


def test_crew_recommended_jobs(client):
    _make_crew(client, position="Başmühendis")
    client.post("/api/jobs/", json={"title": "Başmüh", "position": "Başmühendis"})
    client.post("/api/jobs/", json={"title": "Aşçı", "position": "Aşçı"})

    crew = _crew_client(client)
    crew.patch("/api/portal/job-seeking", json={"job_seeking": True})
    recommended = crew.get("/api/portal/jobs/recommended").json()
    assert len(recommended) >= 1
    # Pozisyonuyla eşleşen ilan ilk sırada ve daha yüksek skorda
    assert recommended[0]["position"] == "Başmühendis"
    assert recommended[0]["match_score"] >= recommended[-1]["match_score"]


# ── Mesajlaşma ──────────────────────────────────────────────────────────────


def test_messages_conversation_flow(client):
    crew_id, crew_user_id = _make_crew(client)
    crew = _crew_client(client)

    # Admin konuşma başlatır
    created = client.post("/api/messages/conversations", json={"crew_user_id": crew_user_id})
    assert created.status_code == 201, created.text
    conversation_id = created.json()["id"]

    # Crew cevap yazar
    reply = crew.post(f"/api/messages/conversations/{conversation_id}", json={"body": "Merhaba, belgeleri yüklüyorum."})
    assert reply.status_code == 201, reply.text

    # Crew konuşma listesi + okunmamış sayısı
    conversations = crew.get("/api/messages/conversations").json()
    assert len(conversations) == 1
    assert conversations[0]["last_message"] == "Merhaba, belgeleri yüklüyorum."

    # Admin konuşmayı açınca crew'ün mesajı okundu olur
    detail = client.get(f"/api/messages/conversations/{conversation_id}").json()
    assert len(detail["messages"]) == 1
    assert detail["messages"][0]["read"] is True


def test_messages_other_crew_cannot_access(client):
    _, crew_user_id = _make_crew(client, email="crew.a@test.example")
    created = client.post("/api/messages/conversations", json={"crew_user_id": crew_user_id})
    conversation_id = created.json()["id"]

    _make_crew(client, email="crew.b@test.example")
    crew_b = _crew_client(client, email="crew.b@test.example")
    assert crew_b.get(f"/api/messages/conversations/{conversation_id}").status_code == 403
    assert crew_b.post(f"/api/messages/conversations/{conversation_id}", json={"body": "x"}).status_code == 403


def test_messages_crew_cannot_create_conversation(client):
    _make_crew(client)
    crew = _crew_client(client)
    assert crew.post("/api/messages/conversations", json={"crew_user_id": 1}).status_code == 403


# ── Cihaz kaydı (push) ──────────────────────────────────────────────────────


def test_devices_register_and_delete(client):
    _make_crew(client)
    crew = _crew_client(client)

    response = crew.post("/api/devices", json={
        "platform": "android", "push_token": "ExponentPushToken[test-abc-123]",
        "device_name": "Xiaomi",
    })
    assert response.status_code == 201, response.text

    # Aynı token tekrar → upsert, duplicate yok
    again = crew.post("/api/devices", json={
        "platform": "android", "push_token": "ExponentPushToken[test-abc-123]",
    })
    assert again.status_code == 201
    assert again.json()["updated"] is True

    deleted = crew.delete("/api/devices/ExponentPushToken%5Btest-abc-123%5D")
    assert deleted.status_code == 204


def test_devices_require_auth(no_auth_client):
    assert no_auth_client.post("/api/devices", json={"push_token": "x"}).status_code == 401


# ── Deaktivasyon ────────────────────────────────────────────────────────────


def test_deactivate_me_blocks_login(client, no_auth_client):
    _make_crew(client)
    crew = _crew_client(client)
    assert crew.patch("/api/auth/me/deactivate").status_code == 204
    login = no_auth_client.post("/api/auth/login", json={
        "email": CREW_EMAIL, "password": CREW_PASSWORD,
    })
    assert login.status_code == 403
