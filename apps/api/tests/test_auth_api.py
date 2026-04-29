from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.deps import get_db
from vaultix_api.main import app
from vaultix_api.models.core import EmailVerification, User


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        with maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        test_client = TestClient(app)
        test_client.app.state.test_sessionmaker = maker
        yield test_client
    finally:
        app.dependency_overrides.clear()


def test_signup_creates_user_and_email_verification_token(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "User@Example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["user"] == {
        "id": 1,
        "email": "User@Example.com",
        "email_verified": False,
    }

    with client.app.state.test_sessionmaker() as session:
        user = session.query(User).filter(User.email_lower == "user@example.com").one()
        token = session.query(EmailVerification).filter(EmailVerification.user_id == user.id).one()
        assert user.password_hash is not None
        assert user.password_hash != "password1"
        assert len(token.token) >= 48


def test_signup_rejects_duplicate_email(client: TestClient):
    payload = {
        "email": "user@example.com",
        "password": "password1",
        "display_name": "박지원",
        "locale": "ko",
        "turnstile_token": "dev-token",
    }

    assert client.post("/api/v1/auth/signup", json=payload).status_code == 201
    response = client.post("/api/v1/auth/signup", json={**payload, "email": "USER@example.com"})

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_signup_rejects_password_without_number(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
