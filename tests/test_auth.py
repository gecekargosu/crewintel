"""Authentication, JWT and role-based authorization tests."""

import jwt as pyjwt
import pytest

from app.core.config import get_settings
from tests.conftest import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    HR_EMAIL,
    HR_PASSWORD,
    VIEWER_EMAIL,
    VIEWER_PASSWORD,
)


def _login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ── Login ────────────────────────────────────────────────────────────────────


def test_login_success(client):
    response = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == ADMIN_EMAIL
    assert body["user"]["role"] == "admin"


def test_login_wrong_password(client):
    response = _login(client, ADMIN_EMAIL, "wrong-password")
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = _login(client, "ghost@test.example", "whatever123")
    assert response.status_code == 401


def test_login_inactive_user(client):
    # Deactivate the HR user via admin API, then HR login must fail.
    response = client.get("/api/auth/users")
    users = response.json()
    hr_id = next(u["id"] for u in users if u["email"] == HR_EMAIL)
    client.patch(f"/api/auth/users/{hr_id}", json={"is_active": False})
    assert client.patch(f"/api/auth/users/{hr_id}", json={"is_active": False}).status_code == 200

    response = _login(client, HR_EMAIL, HR_PASSWORD)
    assert response.status_code == 403


def test_me_requires_token(no_auth_client):
    response = no_auth_client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_valid_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == ADMIN_EMAIL


def test_invalid_token_rejected(client):
    client.headers["Authorization"] = "Bearer not-a-real-token"
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/crew/").status_code == 401


def test_expired_token_rejected(client):
    settings = get_settings()
    expired = pyjwt.encode(
        {"sub": ADMIN_EMAIL, "iat": 0, "exp": 0},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    client.headers["Authorization"] = f"Bearer {expired}"
    assert client.get("/api/auth/me").status_code == 401


# ── Public endpoints stay public ─────────────────────────────────────────────


def test_health_public(no_auth_client):
    assert no_auth_client.get("/health").status_code == 200
    assert no_auth_client.get("/health/database").status_code == 200


def test_login_is_public(no_auth_client):
    response = _login(no_auth_client, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert response.status_code == 200


# ── Role-based authorization ─────────────────────────────────────────────────


def test_viewer_cannot_create_crew(viewer_client):
    payload = {"first_name": "V", "last_name": "Blocked", "position": "Captain"}
    response = viewer_client.post("/api/crew/", json=payload)
    assert response.status_code == 403


def test_viewer_cannot_update_crew(viewer_client, client):
    created = client.post("/api/crew/", json={"first_name": "A", "last_name": "B", "position": "Able"})
    crew_id = created.json()["id"]
    response = viewer_client.put(f"/api/crew/{crew_id}", json={"position": "Hacked"})
    assert response.status_code == 403


def test_viewer_cannot_delete_crew(viewer_client, client):
    created = client.post("/api/crew/", json={"first_name": "A", "last_name": "B", "position": "Able"})
    crew_id = created.json()["id"]
    assert viewer_client.delete(f"/api/crew/{crew_id}").status_code == 403
    # Record still exists for admin.
    assert client.get(f"/api/crew/{crew_id}").status_code == 200


def test_viewer_cannot_write_any_entity(viewer_client):
    ship = {"name": "V-Ship", "imo_number": "1111111"}
    assert viewer_client.post("/api/ships/", json=ship).status_code == 403
    assert viewer_client.post("/api/contracts/", json={}).status_code in (403, 422)
    assert viewer_client.post("/api/assignments/", json={}).status_code in (403, 422)
    assert viewer_client.post("/api/documents/upload", files=[]).status_code in (403, 422)


def test_viewer_can_read(viewer_client, client):
    client.post("/api/crew/", json={"first_name": "A", "last_name": "B", "position": "Able"})
    assert viewer_client.get("/api/crew/").status_code == 200
    assert viewer_client.get("/api/ships/").status_code == 200
    assert viewer_client.get("/api/documents/").status_code == 200
    assert viewer_client.get("/api/expiration/summary").status_code == 200


def test_viewer_cannot_view_audit_logs(viewer_client):
    assert viewer_client.get("/api/audit-logs/").status_code == 403


def test_hr_cannot_manage_users(hr_client):
    assert hr_client.get("/api/auth/users").status_code == 403
    assert hr_client.post("/api/auth/users", json={
        "email": "new@test.example",
        "password": "password123",
        "full_name": "New User",
        "role": "viewer",
    }).status_code == 403


def test_hr_can_write_operational_data(hr_client, client):
    client.post("/api/crew/", json={"first_name": "A", "last_name": "B", "position": "Able"})
    crew_payload = {"first_name": "HR", "last_name": "Writer", "position": "Officer"}
    response = hr_client.post("/api/crew/", json=crew_payload)
    assert response.status_code == 201


def test_admin_full_access(client):
    crew_payload = {"first_name": "Admin", "last_name": "Power", "position": "Captain"}
    created = client.post("/api/crew/", json=crew_payload)
    assert created.status_code == 201
    crew_id = created.json()["id"]
    assert client.put(f"/api/crew/{crew_id}", json={"position": "Chief"}).status_code == 200
    assert client.get("/api/audit-logs/").status_code == 200
    assert client.delete(f"/api/crew/{crew_id}").status_code == 204


# ── User management (admin) ──────────────────────────────────────────────────


def test_admin_create_user_and_roles(client):
    response = client.post("/api/auth/users", json={
        "email": "NEWUSER@test.example",
        "password": "password123",
        "full_name": "New User",
        "role": "hr",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@test.example"
    assert body["role"] == "hr"
    assert "password_hash" not in body


def test_admin_create_duplicate_user_conflict(client):
    client.post("/api/auth/users", json={
        "email": "dup@test.example",
        "password": "password123",
        "full_name": "Dup",
        "role": "viewer",
    })
    response = client.post("/api/auth/users", json={
        "email": "dup@test.example",
        "password": "password123",
        "full_name": "Dup",
        "role": "viewer",
    })
    assert response.status_code == 409


def test_admin_cannot_delete_self(client):
    users = client.get("/api/auth/users").json()
    admin_id = next(u["id"] for u in users if u["email"] == ADMIN_EMAIL)
    assert client.delete(f"/api/auth/users/{admin_id}").status_code == 400


def test_user_management_audit_trail(client):
    client.post("/api/auth/users", json={
        "email": "audited@test.example",
        "password": "password123",
        "full_name": "Audited",
        "role": "viewer",
    })
    logs = client.get("/api/audit-logs/?action=user_created").json()
    assert len(logs) == 1
    assert logs[0]["user_email"] == ADMIN_EMAIL


# ── Audit identity ───────────────────────────────────────────────────────────


def test_audit_log_records_actor_identity(client):
    client.post("/api/crew/", json={"first_name": "Audit", "last_name": "Actor", "position": "Officer"})
    logs = client.get("/api/audit-logs/?action=crew_created").json()
    assert len(logs) == 1
    assert logs[0]["user_email"] == ADMIN_EMAIL


def test_hr_audit_identity(hr_client, client):
    hr_client.post("/api/crew/", json={"first_name": "HR", "last_name": "Audit", "position": "Officer"})
    # hr cannot view the audit trail itself.
    assert hr_client.get("/api/audit-logs/?action=crew_created").status_code == 403
    # Admin sees the actor identity on HR's action.
    logs = client.get("/api/audit-logs/?action=crew_created").json()
    assert len(logs) == 1
    assert logs[0]["user_email"] == HR_EMAIL


def test_rate_limit_only_failed_attempts(client):
    """Rate limiter sadece hatalı denemeleri saymalı; başarılı giriş sayacı sıfırlamalı."""
    # 10 hatalı deneme (limit 10)
    for i in range(10):
        r = _login(client, ADMIN_EMAIL, "yanlis-sifre-%d" % i)
        assert r.status_code == 401
    # 11. hatalı deneme -> 429
    r = _login(client, ADMIN_EMAIL, "yanlis-sifre-son")
    assert r.status_code == 429
    # Başarılı giriş sayaçı sıfırlar -> tekrar hatalı deneme 401 olmalı (429 değil)
    r = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert r.status_code == 200
    r = _login(client, ADMIN_EMAIL, "yanlis-sifre-yeni")
    assert r.status_code == 401
