"""Audit-fix regression tests:
- BUG-001: crew rolü yönetim API'lerine erişemez (okuma dahil) + belge IDOR engelli
- BUG-004: admin başka admin silemez
- BUG-006: login rate limiting
"""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.models.crew_member import CrewMember
from app.models.document import Document
from app.models.ship import Ship
from app.models.user import User
from tests.conftest import _create_user, _login_token


def _make_crew_user(db, role="crew", email="crew@test.example") -> User:
    crew = CrewMember(first_name="Crew", last_name="Test", position="Kaptan", status="active")
    db.add(crew)
    db.commit()
    db.refresh(crew)
    user = _create_user(db, email, "crew-pass-123", role, full_name="Crew User")
    user.crew_member_id = crew.id
    db.commit()
    db.refresh(user)
    return user


def _make_doc(db, crew_id):
    ts = datetime.now(UTC).timestamp()
    doc = Document(
        original_filename=f"audit_fix_{ts}.pdf",
        stored_filename=f"audit_fix_{ts}.pdf",
        storage_path=f"test/audit_fix_{ts}.pdf",
        checksum=f"audit-fix-{ts}",
        file_size=10,
        mime_type="application/pdf",
        document_type="other",
        match_status="matched",
        crew_member_id=crew_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _crew_client(db):
    """Crew rolünde oturum açmış TestClient döndürür."""
    user = _make_crew_user(db)
    from app.db.database import get_db
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        token = _login_token(tc, user.email, "crew-pass-123")
        tc.headers["Authorization"] = f"Bearer {token}"
        yield tc
    app.dependency_overrides.clear()


# ── BUG-001: crew okuma izolasyonu ────────────────────────────────────────


def test_crew_cannot_read_management_apis(client, db_session):
    crew_user = _make_crew_user(db_session)
    _make_doc(db_session, crew_user.crew_member_id)
    _make_ship = Ship(name="Test Ship", status="active")
    db_session.add(_make_ship)
    db_session.commit()
    db_session.refresh(_make_ship)

    from app.db.database import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        token = _login_token(tc, crew_user.email, "crew-pass-123")
        headers = {"Authorization": f"Bearer {token}"}
        blocked = [
            ("/api/crew/", 403),
            ("/api/crew/1", 403),
            ("/api/crew/eligible?position=Kaptan", 403),
            ("/api/crew/export", 403),
            ("/api/documents/", 403),
            ("/api/documents/review", 403),
            ("/api/ships/", 403),
            ("/api/ships/1", 403),
            ("/api/ships/1/staffing", 403),
            ("/api/assignments/", 403),
            ("/api/contracts/", 403),
            ("/api/dashboard/summary", 403),
            ("/api/notifications/", 403),
            ("/api/expiration/summary", 403),
            ("/api/audit-logs/", 403),
        ]
        for path, expected in blocked:
            resp = tc.get(path, headers=headers)
            assert resp.status_code == expected, f"{path} -> {resp.status_code} (beklenen {expected})"

        # IDOR: crew başka belgenin dosyasını indirememeli
        resp = tc.get("/api/documents/1/file", headers=headers)
        assert resp.status_code == 403

        # Portal ise kendi verisini görebilmeli
        me = tc.get("/api/portal/me", headers=headers)
        assert me.status_code == 200, me.text
    app.dependency_overrides.clear()


def test_viewer_can_read_but_crew_cannot(client, viewer_client, db_session):
    # Viewer okuma yapabilir
    assert viewer_client.get("/api/crew/").status_code == 200
    assert viewer_client.get("/api/documents/").status_code == 200
    # Ama yazamaz
    assert viewer_client.post("/api/crew/", json={"first_name": "X", "last_name": "Y", "position": "K"}).status_code == 403


def test_crew_cannot_write_even_with_manual_token(client, db_session):
    crew_user = _make_crew_user(db_session)
    from app.db.database import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        token = _login_token(tc, crew_user.email, "crew-pass-123")
        headers = {"Authorization": f"Bearer {token}"}
        assert tc.post("/api/crew/", headers=headers, json={"first_name": "X", "last_name": "Y", "position": "K"}).status_code == 403
    app.dependency_overrides.clear()


# ── BUG-004: admin başka admin silemez ────────────────────────────────────


def test_admin_cannot_delete_another_admin(client, db_session):
    other_admin = _create_user(db_session, "other.admin@test.example", "admin-pass-123", "admin", "Other Admin")
    resp = client.delete(f"/api/auth/users/{other_admin.id}")
    assert resp.status_code == 400
    assert "Admin" in resp.json()["detail"]


def test_admin_can_delete_viewer(client, db_session):
    viewer = _create_user(db_session, "del.viewer@test.example", "viewer-pass-123", "viewer", "Del Viewer")
    resp = client.delete(f"/api/auth/users/{viewer.id}")
    assert resp.status_code == 204


# ── BUG-006: login rate limiting ──────────────────────────────────────────


def test_login_rate_limited_after_many_failures(client):
    for _ in range(10):
        client.post("/api/auth/login", json={"email": "nurten@kilic.com", "password": "wrong-pass"})
    resp = client.post("/api/auth/login", json={"email": "nurten@kilic.com", "password": "wrong-pass"})
    assert resp.status_code == 429
