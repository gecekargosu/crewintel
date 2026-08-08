from fastapi import FastAPI

app = FastAPI(
    title="CREWINTEL",
    description="Gemi personeli ve insan kaynakları yönetim sistemi",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "system": "CREWINTEL",
        "status": "online",
        "message": "CREWINTEL backend çalışıyor."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }