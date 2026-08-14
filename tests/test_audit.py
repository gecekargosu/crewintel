"""
Audit log sistemi testleri.

Şunları doğrular:
- Crew CRUD işlemleri audit log oluşturuyor
- Ship oluşturma audit log oluşturuyor
- Assignment oluşturma audit log oluşturuyor
- Contract oluşturma audit log oluşturuyor
- Document upload audit log oluşturuyor
- CV'den personel oluşturma audit log oluşturuyor
- GET /api/audit-logs/ endpoint'i çalışıyor ve filtrelenebiliyor
"""
from datetime import date


# ── Yardımcı fonksiyonlar ────────────────────────────────────────────────────

def create_crew(client, **overrides):
    payload = {
        "first_name": "Test",
        "last_name": "Personel",
        "position": "Captain",
        "nationality": "Turkish",
        "status": "active",
    }
    payload.update(overrides)
    r = client.post("/api/crew/", json=payload)
    assert r.status_code == 201
    return r.json()


def create_ship(client, **overrides):
    payload = {
        "name": "MV Test",
        "imo_number": "9876543",
        "flag": "Turkey",
        "ship_type": "Tanker",
        "company": "Test Co",
        "status": "active",
    }
    payload.update(overrides)
    r = client.post("/api/ships/", json=payload)
    assert r.status_code == 201
    return r.json()


def get_audit_logs(client, **filters):
    return client.get("/api/audit-logs/", params=filters).json()


# ── Crew audit testleri ───────────────────────────────────────────────────────

def test_crew_create_generates_audit_log(client):
    crew = create_crew(client)
    logs = get_audit_logs(client, action="crew_created", entity="crew_member", entity_id=crew["id"])
    assert len(logs) == 1
    assert logs[0]["action"] == "crew_created"
    assert logs[0]["entity_id"] == crew["id"]


def test_crew_update_generates_audit_log(client):
    crew = create_crew(client)
    client.put(f"/api/crew/{crew['id']}", json={"rank": "Master"})
    logs = get_audit_logs(client, action="crew_updated", entity_id=crew["id"])
    assert len(logs) == 1
    assert logs[0]["action"] == "crew_updated"


def test_crew_delete_generates_audit_log(client):
    crew = create_crew(client)
    crew_id = crew["id"]
    client.delete(f"/api/crew/{crew_id}")
    logs = get_audit_logs(client, action="crew_deleted", entity_id=crew_id)
    assert len(logs) == 1
    assert logs[0]["action"] == "crew_deleted"


# ── Ship audit testi ──────────────────────────────────────────────────────────

def test_ship_create_generates_audit_log(client):
    ship = create_ship(client)
    logs = get_audit_logs(client, action="ship_created", entity_id=ship["id"])
    assert len(logs) == 1
    assert logs[0]["entity"] == "ship"


# ── Assignment audit testi ────────────────────────────────────────────────────

def test_assignment_create_generates_audit_log(client):
    ship = create_ship(client, imo_number="1111111")
    crew = create_crew(client)
    payload = {
        "ship_id": ship["id"],
        "crew_member_id": crew["id"],
        "position": "Captain",
        "start_date": str(date(2026, 1, 1)),
        "status": "active",
    }
    r = client.post("/api/assignments/", json=payload)
    assert r.status_code == 201
    logs = get_audit_logs(client, action="assignment_created", entity_id=r.json()["id"])
    assert len(logs) == 1


# ── Contract audit testi ──────────────────────────────────────────────────────

def test_contract_create_generates_audit_log(client):
    ship = create_ship(client, imo_number="2222222")
    crew = create_crew(client)
    payload = {
        "ship_id": ship["id"],
        "crew_member_id": crew["id"],
        "contract_number": "CNT-AUDIT-001",
        "contract_type": "Employment",
        "start_date": "2026-01-01",
        "status": "active",
    }
    r = client.post("/api/contracts/", json=payload)
    assert r.status_code == 201
    logs = get_audit_logs(client, action="contract_created", entity_id=r.json()["id"])
    assert len(logs) == 1


# ── Document audit testleri ───────────────────────────────────────────────────

def test_document_upload_generates_audit_log(client):
    content = b"Name: Ali Demir\nSTCW certificate"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("ali_stcw.txt", content, "text/plain"))],
    )
    assert r.status_code == 201
    doc_id = r.json()[0]["id"]
    logs = get_audit_logs(client, action="document_uploaded", entity_id=doc_id)
    assert len(logs) == 1
    assert logs[0]["entity"] == "document"


def test_cv_upload_generates_crew_created_from_cv_audit_log(client):
    content = b"Curriculum Vitae\nName: Hasan Yildiz\nhasan@example.com"
    r = client.post(
        "/api/documents/upload",
        files=[("files", ("HASAN_YILDIZ_CV.txt", content, "text/plain"))],
    )
    assert r.status_code == 201
    # CV'den personel oluşturuldu mu?
    crew_list = client.get("/api/crew/?name=Hasan").json()
    assert len(crew_list) == 1
    crew_id = crew_list[0]["id"]
    logs = get_audit_logs(client, action="crew_created_from_cv", entity_id=crew_id)
    assert len(logs) == 1


# ── Audit log API filtreleme testleri ────────────────────────────────────────

def test_audit_log_list_endpoint_returns_all(client):
    create_crew(client)
    create_crew(client, first_name="İkinci", last_name="Kişi")
    logs = get_audit_logs(client)
    assert len(logs) >= 2


def test_audit_log_filter_by_action(client):
    create_crew(client)
    ship = create_ship(client, imo_number="3333333")
    crew_logs = get_audit_logs(client, action="crew_created")
    ship_logs = get_audit_logs(client, action="ship_created")
    assert all(log["action"] == "crew_created" for log in crew_logs)
    assert all(log["action"] == "ship_created" for log in ship_logs)
    assert len(ship_logs) >= 1


def test_audit_log_filter_by_entity(client):
    create_ship(client, imo_number="4444444")
    logs = get_audit_logs(client, entity="ship")
    assert all(log["entity"] == "ship" for log in logs)
    assert len(logs) >= 1


# ── Tarih aralığı filtresi testleri ─────────────────────────────────────────

def test_audit_log_date_from_filter_returns_logs_on_or_after(client):
    """date_from: today → oluşturulan loglar görünmeli."""
    from datetime import date
    create_crew(client)
    today_str = str(date.today())
    logs = get_audit_logs(client, date_from=today_str)
    assert len(logs) >= 1
    # Tüm dönen loglar date_from tarihinde veya sonrasında olmalı
    for log in logs:
        log_date = log["created_at"][:10]  # "YYYY-MM-DD" prefix
        assert log_date >= today_str


def test_audit_log_date_to_filter_excludes_future(client):
    """date_to: today → bugün veya öncesindeki loglar döner, yarın filtresi geçerli."""
    from datetime import date, timedelta
    create_crew(client)
    today_str = str(date.today())
    yesterday_str = str(date.today() - timedelta(days=1))
    # date_to=today → bugün oluşturulan loglar dahil
    logs_today = get_audit_logs(client, date_to=today_str)
    assert len(logs_today) >= 1
    # date_to=yesterday → bugün oluşturulan loglar GÖRÜNMEMELI
    logs_yesterday = get_audit_logs(client, date_to=yesterday_str)
    for log in logs_yesterday:
        log_date = log["created_at"][:10]
        assert log_date <= yesterday_str


def test_audit_log_date_range_combined(client):
    """date_from + date_to birlikte → yalnızca aralıktaki loglar döner."""
    from datetime import date, timedelta
    create_crew(client)
    today_str = str(date.today())
    tomorrow_str = str(date.today() + timedelta(days=1))
    logs = get_audit_logs(client, date_from=today_str, date_to=tomorrow_str)
    assert len(logs) >= 1
    for log in logs:
        log_date = log["created_at"][:10]
        assert today_str <= log_date <= tomorrow_str
