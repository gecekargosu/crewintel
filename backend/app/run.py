import uvicorn

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.seed import ensure_admin_user


def run() -> None:
    settings = get_settings()
    # Create the initial admin user from ADMIN_EMAIL / ADMIN_PASSWORD (no-op if unset).
    db = SessionLocal()
    try:
        ensure_admin_user(db)
    finally:
        db.close()
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
    )


if __name__ == "__main__":
    run()
