import os

# Set DATABASE_URL before any app imports (pydantic-settings requires it)
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("STORAGE_PATH", os.path.join(os.path.dirname(__file__), "..", "storage"))
