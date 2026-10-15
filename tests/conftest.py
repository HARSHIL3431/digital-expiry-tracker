"""
Shared pytest fixtures for the Digital Expiry Tracker test suite.

Every fixture that touches the database uses an isolated in-memory SQLite
engine so tests never interact with the production/development database file.
"""

import pytest
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.utils.database import Base, get_db
from app import models
from app.core.security import hash_password


# ---------------------------------------------------------------------------
# Engine / session fixtures (isolated in-memory SQLite per test)
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_engine(tmp_path):
    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def test_session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db(test_session_factory):
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# TestClient with dependency override
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(test_session_factory):
    """FastAPI TestClient backed by the isolated test database."""

    def override_get_db():
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper: create a user + subscription directly in the test DB
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_user(db):
    """Insert a free-plan user into the isolated test DB and return the ORM object."""
    user = models.User(
        name="Test User",
        email="testuser@example.com",
        password_hash=hash_password("password123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    sub = models.Subscription(
        user_id=user.id,
        plan_type="free",
        expiry_date=date.today() + timedelta(days=365),
    )
    db.add(sub)
    db.commit()

    return user


# ---------------------------------------------------------------------------
# Helper: register + log in via the API, return Authorization headers
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_headers(client):
    """Register a fresh user via the API and return bearer auth headers."""
    email = "apiuser@example.com"
    password = "securepass99"

    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "API User", "email": email, "password": password},
    )
    assert reg.status_code == 200, f"Registration failed: {reg.text}"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, f"Login failed: {login.text}"

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
