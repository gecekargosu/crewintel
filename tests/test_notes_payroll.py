"""Notlar, maaş/ödeme ve (yapılandırılmamış) AI uçlarının testleri."""


def create_crew(client, **overrides):
    payload = {
        "first_name": "Ayşe",
        "last_name": "Yılmaz",
        "position": "Second Officer",
        "nationality": "Turkish",
        "status": "active",
    }
    payload.update(overrides)
    response = client.post("/api/crew/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ── Notlar ───────────────────────────────────────────────────────────────────


def test_notes_crud(client):
    created = client.post(
        "/api/notes/",
        json={"title": "STCW yenile", "body": "Mehmet için", "priority": "high"},
    )
    assert created.status_code == 201, created.text
    note = created.json()
    assert note["title"] == "STCW yenile"
    assert note["done"] is False

    listed = client.get("/api/notes/")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [note["id"]]

    updated = client.put(f"/api/notes/{note['id']}", json={"done": True})
    assert updated.status_code == 200
    assert updated.json()["done"] is True

    deleted = client.delete(f"/api/notes/{note['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/notes/").json() == []


def test_notes_are_scoped_to_owner(hr_client, client):
    created = hr_client.post("/api/notes/", json={"title": "HR notu"})
    assert created.status_code == 201
    note_id = created.json()["id"]

    # HR kullanıcısı kendi notunu görür…
    assert [item["id"] for item in hr_client.get("/api/notes/").json()] == [note_id]
    # …admin (başka kullanıcı) göremez ve değiştiremez.
    assert client.get("/api/notes/").json() == []
    assert client.put(f"/api/notes/{note_id}", json={"done": True}).status_code == 404
    assert client.delete(f"/api/notes/{note_id}").status_code == 404


def test_notes_reject_invalid_priority(client):
    response = client.post("/api/notes/", json={"title": "x", "priority": "acil-ish"})
    assert response.status_code == 422


def test_notes_require_authentication(no_auth_client):
    assert no_auth_client.get("/api/notes/").status_code == 401


# ── Maaş / ödemeler ──────────────────────────────────────────────────────────


def test_payment_flow(client):
    crew = create_crew(client)

    created = client.post(
        "/api/salary/",
        json={
            "crew_member_id": crew["id"],
            "amount": 1850.5,
            "currency": "usd",
            "payment_type": "salary",
            "description": "Ocak maaşı",
            "payment_date": "2026-01-31",
        },
    )
    assert created.status_code == 201, created.text
    payment = created.json()
    assert payment["amount"] == 1850.5
    assert payment["currency"] == "USD"

    listed = client.get("/api/salary/", params={"crew_member_id": crew["id"]})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    summary = client.get("/api/salary/summary")
    assert summary.status_code == 200
    assert summary.json()["totals_by_currency"]["USD"] == 1850.5

    updated = client.put(f"/api/salary/{payment['id']}", json={"amount": 1900})
    assert updated.status_code == 200
    assert updated.json()["amount"] == 1900

    assert client.delete(f"/api/salary/{payment['id']}").status_code == 204
    assert client.get("/api/salary/").json() == []


def test_payment_requires_existing_crew(client):
    response = client.post("/api/salary/", json={"crew_member_id": 9999, "amount": 10})
    assert response.status_code == 404


def test_payment_rejects_invalid_type_and_amount(client):
    crew = create_crew(client)
    bad_type = client.post(
        "/api/salary/",
        json={"crew_member_id": crew["id"], "amount": 10, "payment_type": "bribe"},
    )
    assert bad_type.status_code == 422

    bad_amount = client.post(
        "/api/salary/",
        json={"crew_member_id": crew["id"], "amount": -5},
    )
    assert bad_amount.status_code == 422


def test_payment_writes_audit_log(client):
    crew = create_crew(client)
    client.post("/api/salary/", json={"crew_member_id": crew["id"], "amount": 100})

    logs = client.get("/api/audit-logs/", params={"limit": 50})
    assert logs.status_code == 200
    assert any(entry["action"] == "payment_created" for entry in logs.json())


# ── AI (yapılandırılmadığında) ───────────────────────────────────────────────


def test_ai_health_reports_not_configured(client, monkeypatch):
    from app.core.config import get_settings  # noqa: PLC0415

    settings = get_settings()
    monkeypatch.setattr(settings, "ai_api_key", None, raising=False)

    response = client.get("/api/ai/health")
    assert response.status_code == 200
    assert response.json()["status"] == "not_configured"


def test_ai_analyze_returns_503_without_key(client, monkeypatch):
    from app.core.config import get_settings  # noqa: PLC0415

    monkeypatch.setattr(get_settings(), "ai_api_key", None, raising=False)

    response = client.post("/api/ai/analyze", json={"text": "Ahmet Yılmaz passport"})
    assert response.status_code == 503
