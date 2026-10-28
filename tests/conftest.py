import os
import tempfile
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("STORAGE_PATH", str(Path(tempfile.gettempdir()) / "crewintel-test-uploads"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User


test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

ADMIN_EMAIL = "admin@test.example"
ADMIN_PASSWORD = "admin-pass-123"
HR_EMAIL = "hr@test.example"
HR_PASSWORD = "hr-pass-123"
VIEWER_EMAIL = "viewer@test.example"
VIEWER_PASSWORD = "viewer-pass-123"


def _create_user(db, email: str, password: str, role: str, full_name: str = "Test User") -> User:
    user = User(
        email=email,
        full_name=full_name,
        role=role,
        is_active=True,
        password_hash=hash_password(password, rounds=4),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login_token(test_client: TestClient, email: str, password: str) -> str:
    response = test_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def database_fixture():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        _create_user(db, ADMIN_EMAIL, ADMIN_PASSWORD, "admin", "Admin User")
        _create_user(db, HR_EMAIL, HR_PASSWORD, "hr", "HR User")
        _create_user(db, VIEWER_EMAIL, VIEWER_PASSWORD, "viewer", "Viewer User")
    finally:
        db.close()
    from app.api.routes.auth import reset_login_attempts, reset_register_attempts

    reset_login_attempts()
    reset_register_attempts()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """Doğrudan ORM erişimi (dry-run testleri vb.)."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_client(role: str):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        if role == "admin":
            token = _login_token(test_client, ADMIN_EMAIL, ADMIN_PASSWORD)
        elif role == "hr":
            token = _login_token(test_client, HR_EMAIL, HR_PASSWORD)
        elif role == "viewer":
            token = _login_token(test_client, VIEWER_EMAIL, VIEWER_PASSWORD)
        else:
            token = None
        if token:
            test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    """Authenticated admin client — default for all existing tests."""
    yield from _make_client("admin")


@pytest.fixture()
def hr_client():
    yield from _make_client("hr")


@pytest.fixture()
def viewer_client():
    yield from _make_client("viewer")


@pytest.fixture()
def no_auth_client():
    yield from _make_client("none")
