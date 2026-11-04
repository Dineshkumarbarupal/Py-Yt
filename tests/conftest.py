import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-that-is-long-enough-for-tests")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:////tmp/pyyt-tests.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")
os.environ.setdefault("APP_ENV", "test")

from db.base import Base
import db.models  # noqa: F401
from db.session import engine
from main import app

@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
