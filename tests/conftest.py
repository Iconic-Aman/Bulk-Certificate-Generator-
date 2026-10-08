import os
import sys

# Ensure app package is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app_dir = os.path.join(root_dir, "app")
for path in (root_dir, app_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["API_KEY"] = "test-api-key"
os.environ["API_PREFIX"] = "/api"
os.environ["JOB_STATUS_URL_BASE"] = "/api/jobs"
os.environ["STORAGE_DIR"] = "test-storage"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine)


from app import database as app_db
import app.services.job_processor as jp

app_db.SessionLocal = TestingSessionLocal
app_db.engine = test_engine
jp.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def override_db():
    def _get_test_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app, headers={"X-API-Key": "test-api-key"})


@pytest.fixture(autouse=True)
def mock_storage(monkeypatch):
    storage_store = {}

    def mock_upload(key, data, content_type="application/pdf"):
        storage_store[key] = data
        return key

    def mock_get(key):
        return storage_store.get(key, b"%PDF-mock-bytes")

    def mock_presigned(key, filename="", expires_in=3600):
        return f"https://mock-r2.test/{key}"

    monkeypatch.setattr("app.services.storage.upload_bytes", mock_upload)
    monkeypatch.setattr("app.services.storage.get_bytes", mock_get)
    monkeypatch.setattr("app.services.storage.get_presigned_url", mock_presigned)
    return storage_store
