import os

# Set DATABASE_URL before any app imports (pydantic-settings requires it)
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("STORAGE_PATH", os.path.join(os.path.dirname(__file__), "..", "storage"))

# Test user credentials (used by test_auth.py and other tests)
ADMIN_EMAIL = "admin@test.example"
ADMIN_PASSWORD = "admin-pass-123"
HR_EMAIL = "hr@test.example"
HR_PASSWORD = "hr-pass-123"
VIEWER_EMAIL = "viewer@test.example"
VIEWER_PASSWORD = "viewer-pass-123"


def _create_user(db, email: str, password: str, role: str, full_name: str = "Test User"):
    """Create a user in the test database."""
    from app.core.security import hash_password
    from app.models.user import User

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


def _login_token(test_client, email: str, password: str) -> str:
    """Login and return the access token."""
    response = test_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
