from datetime import date


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
    assert response.status_code == 201
    return response.json()


def create_ship(client, **overrides):
    payload = {
        "name": "MV Horizon",
        "imo_number": "1234567",
        "flag": "Turkey",
        "ship_type": "Bulk Carrier",
        "company": "CrewIntel Shipping",
        "status": "active",
    }
    payload.update(overrides)
    response = client.post("/api/ships/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_crew_list_endpoint(client):
    response = client.get("/api/crew/")

    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_crew_member(client):
    created = create_crew(client, email="ayse@example.com")

    assert created["first_name"] == "Ayşe"
    assert created["position"] == "Second Officer"
    assert created["status"] == "active"

    listed_crew = client.get("/api/crew/?position=Officer&limit=10")
    assert listed_crew.status_code == 200
    assert len(listed_crew.json()) == 1


def test_update_and_delete_crew_member(client):
    crew_member = create_crew(client)

    updated = client.put(
        f"/api/crew/{crew_member['id']}",
        json={"rank": "2/O", "status": "on_leave", "email": "ayse@example.com"},
    )
    assert updated.status_code == 200
    assert updated.json()["rank"] == "2/O"
    assert updated.json()["status"] == "on_leave"

    deleted = client.delete(f"/api/crew/{crew_member['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/crew/{crew_member['id']}").status_code == 404


def test_create_and_list_ship(client):
    ship = create_ship(client)

    assert ship["imo_number"] == "1234567"
    listed = client.get("/api/ships/")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_create_and_list_assignment(client):
    ship = create_ship(client)
    crew_member = create_crew(client)
    assignment_payload = {
        "ship_id": ship["id"],
        "crew_member_id": crew_member["id"],
        "position": "Second Officer",
        "start_date": str(date(2026, 8, 9)),
        "status": "active",
    }

    response = client.post("/api/assignments/", json=assignment_payload)
    assert response.status_code == 201
    assert response.json()["ship_id"] == ship["id"]

    listed = client.get("/api/assignments/")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    crew_for_ship = client.get(f"/api/crew/?ship_id={ship['id']}")
    assert len(crew_for_ship.json()) == 1


def test_create_and_list_contract(client):
    ship = create_ship(client)
    crew_member = create_crew(client)
    contract_payload = {
        "ship_id": ship["id"],
        "crew_member_id": crew_member["id"],
        "contract_number": "CNT-2026-001",
        "contract_type": "Employment",
        "start_date": "2026-08-09",
        "end_date": "2027-02-09",
        "status": "active",
    }

    response = client.post("/api/contracts/", json=contract_payload)
    assert response.status_code == 201
    assert response.json()["contract_number"] == "CNT-2026-001"

    listed = client.get("/api/contracts/")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_not_found_for_unknown_ids(client):
    assert client.get("/api/ships/999").status_code == 404
    assert client.get("/api/crew/999").status_code == 404
    assert client.get("/api/assignments/999").status_code == 404
    assert client.get("/api/contracts/999").status_code == 404


def test_validation_errors(client):
    invalid_ship = client.post("/api/ships/", json={"name": "", "imo_number": "IMO-1"})
    assert invalid_ship.status_code == 422

    invalid_crew = client.post(
        "/api/crew/",
        json={"first_name": "Ayşe", "last_name": "Yılmaz", "position": "Officer", "email": "not-an-email"},
    )
    assert invalid_crew.status_code == 422

    invalid_dates = client.post(
        "/api/contracts/",
        json={
            "ship_id": 1,
            "crew_member_id": 1,
            "contract_number": "CNT-invalid",
            "contract_type": "Employment",
            "start_date": "2026-08-10",
            "end_date": "2026-08-09",
        },
    )
    assert invalid_dates.status_code == 422


def test_foreign_key_references_must_exist(client):
    assignment = client.post(
        "/api/assignments/",
        json={
            "ship_id": 999,
            "crew_member_id": 999,
            "position": "Officer",
            "start_date": "2026-08-09",
        },
    )
    assert assignment.status_code == 404

    contract = client.post(
        "/api/contracts/",
        json={
            "ship_id": 999,
            "crew_member_id": 999,
            "contract_number": "CNT-404",
            "contract_type": "Employment",
            "start_date": "2026-08-09",
        },
    )
    assert contract.status_code == 404
