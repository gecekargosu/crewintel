from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.assignments import router as assignment_router
from app.api.routes.audit_logs import router as audit_log_router
from app.api.routes.auth import router as auth_router
from app.api.routes.contracts import router as contract_router
from app.api.routes.crew import router as crew_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.devices import router as devices_router
from app.api.routes.documents import router as document_router
from app.api.routes.expiration import router as expiration_router
from app.api.routes.messages import router as messages_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.portal import router as portal_router
from app.api.routes.jobs import (
    router as jobs_router,
    templates_router,
    webhook_router,
    whatsapp_router,
)
from app.api.routes.settings import router as settings_router
from app.api.routes.ships import router as ship_router
from app.api.routes.ai import router as ai_router
from app.api.routes.social_downloader import router as social_router
from app.core.config import get_settings
from app.db.database import engine

settings = get_settings()

app = FastAPI(
    title="CREWINTEL",
    description="Gemi personeli ve insan kaynaklari yonetim sistemi",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(crew_router)
app.include_router(ship_router)
app.include_router(assignment_router)
app.include_router(contract_router)
app.include_router(document_router)
app.include_router(expiration_router)
app.include_router(audit_log_router)
app.include_router(notifications_router)
app.include_router(dashboard_router)
app.include_router(portal_router)
app.include_router(messages_router)
app.include_router(devices_router)
app.include_router(settings_router)
app.include_router(jobs_router)
app.include_router(templates_router)
app.include_router(whatsapp_router)
app.include_router(webhook_router)
app.include_router(ai_router)
app.include_router(social_router)


@app.get("/")
def root():
    return {
        "system": "CREWINTEL",
        "status": "online",
        "message": "CREWINTEL backend calisiyor.",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": settings.app_environment,
    }


@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from error

    return {"status": "healthy", "database": "connected"}
