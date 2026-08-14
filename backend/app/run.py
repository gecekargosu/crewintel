import uvicorn

from app.core.config import get_settings


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
    )


if __name__ == "__main__":
    run()
