from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User


def ensure_admin_user(db: Session) -> None:
    """Create the initial admin user from ADMIN_EMAIL / ADMIN_PASSWORD env vars.

    Only runs when both variables are set AND the users table has no active
    admin yet. Never overwrites existing credentials.
    """
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return

    email = settings.admin_email.strip().lower()
    existing_admin = (
        db.query(User)
        .filter(User.role == "admin")
        .first()
    )
    if existing_admin is not None:
        return

    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        existing.role = "admin"
        existing.is_active = True
        if not existing.password_hash:
            existing.password_hash = hash_password(settings.admin_password)
        db.commit()
        print(f"CREWINTEL: promoted existing user {email} to admin.")
        return

    db.add(User(
        email=email,
        full_name="System Administrator",
        role="admin",
        is_active=True,
        password_hash=hash_password(settings.admin_password),
    ))
    db.commit()
    print(f"CREWINTEL: admin user created: {email}")
