import os

# Test-only values; production secrets must come from the environment.
TEST_JWT_SECRET_KEY = "pytest-only-jwt-secret-key-at-least-32-bytes"

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = TEST_JWT_SECRET_KEY
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.database as db_module
from app.core.database import Base
from app.models import Endpoint, Finding, Scan, User  # noqa: F401
from app.main import app

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

db_module.engine = TEST_ENGINE
db_module.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def setup_database() -> None:
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
