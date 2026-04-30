from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.deps import get_db
from vaultix_api.main import app
from vaultix_api.models.core import EmailVerification, PasswordReset, Session as UserSession, User
from vaultix_api.services.passwords import verify_password
from vaultix_api.settings import get_settings


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
        get_settings.cache_clear()


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


def test_signup_rejects_disposable_email_domain(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@mailinator.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "disposable_email_blocked"


def test_signup_rejects_failed_turnstile(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "secret")
    get_settings.cache_clear()
    monkeypatch.setattr("vaultix_api.routers.auth.verify_turnstile", lambda *_args, **_kwargs: False)

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "bad-token",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "turnstile_failed"


def test_verify_email_marks_user_verified_and_consumes_token(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )
    with client.app.state.test_sessionmaker() as session:
        token = session.query(EmailVerification).one().token

    response = client.post("/api/v1/auth/verify-email", json={"token": token})

    assert response.status_code == 200
    assert response.json()["data"] == {"verified": True, "user_id": 1}

    with client.app.state.test_sessionmaker() as session:
        user = session.query(User).filter(User.id == 1).one()
        verification = session.query(EmailVerification).filter(EmailVerification.token == token).one()
        assert user.email_verified_at is not None
        assert verification.used_at is not None

    replay_response = client.post("/api/v1/auth/verify-email", json={"token": token})

    assert replay_response.status_code == 410
    assert replay_response.json()["code"] == "verification_token_invalid"


def test_signup_sends_verification_email_when_resend_is_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    sent: list[dict[str, str]] = []
    monkeypatch.setenv("RESEND_API_KEY", "resend-key")
    monkeypatch.setenv("MAIL_FROM", "Vaultix <no-reply@vaultix.example.com>")
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://vaultix.example.com")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "vaultix_api.routers.auth.send_transactional_email",
        lambda **kwargs: sent.append(kwargs),
    )

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
    assert sent[0]["to"] == "User@Example.com"
    assert sent[0]["subject"] == "Vaultix 이메일 인증"
    assert "https://vaultix.example.com/auth/verify?token=" in sent[0]["html"]


def test_verify_email_rejects_missing_token(client: TestClient):
    response = client.post("/api/v1/auth/verify-email", json={"token": "missing-token"})

    assert response.status_code == 410
    assert response.json()["code"] == "verification_token_invalid"


def test_login_creates_session_and_sets_cookie(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "USER@example.com", "password": "password1"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["user"] == {
        "id": 1,
        "email": "user@example.com",
        "email_verified": False,
    }
    assert "vaultix.session=" in response.headers["set-cookie"]


def test_login_rejects_wrong_password(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password1"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


def test_logout_deletes_current_session_and_clears_cookie(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password1"},
    )
    assert login_response.status_code == 200

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["data"] == {"logged_out": True}
    assert "vaultix.session=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
    with client.app.state.test_sessionmaker() as session:
        assert session.query(UserSession).count() == 0


def test_forgot_password_creates_reset_token_without_disclosing_account(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )

    response = client.post("/api/v1/auth/forgot-password", json={"email": "USER@example.com"})
    missing_response = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})

    assert response.status_code == 200
    assert missing_response.status_code == 200
    assert response.json()["data"]["sent"] is True
    with client.app.state.test_sessionmaker() as session:
        reset = session.query(PasswordReset).one()
        assert reset.token_hash.startswith("sha256$")


def test_forgot_password_sends_reset_email_when_resend_is_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    sent: list[dict[str, str]] = []
    monkeypatch.setenv("RESEND_API_KEY", "resend-key")
    monkeypatch.setenv("MAIL_FROM", "Vaultix <no-reply@vaultix.example.com>")
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://vaultix.example.com")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "vaultix_api.routers.auth.send_transactional_email",
        lambda **kwargs: sent.append(kwargs),
    )
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )
    sent.clear()

    response = client.post("/api/v1/auth/forgot-password", json={"email": "USER@example.com"})

    assert response.status_code == 200
    assert response.json()["data"]["sent"] is True
    assert sent[0]["to"] == "user@example.com"
    assert sent[0]["subject"] == "Vaultix 비밀번호 재설정"
    assert "https://vaultix.example.com/auth/reset-password?token=" in sent[0]["html"]


def test_reset_password_updates_password_and_consumes_token(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password1",
            "display_name": "박지원",
            "locale": "ko",
            "turnstile_token": "dev-token",
        },
    )
    forgot_response = client.post("/api/v1/auth/forgot-password", json={"email": "user@example.com"})
    raw_token = forgot_response.json()["data"]["reset_token"]

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "password": "newpass1"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"reset": True}
    with client.app.state.test_sessionmaker() as session:
        user = session.query(User).filter(User.email_lower == "user@example.com").one()
        reset = session.query(PasswordReset).one()
        assert verify_password("newpass1", user.password_hash)
        assert reset.used_at is not None

    replay_response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "password": "againpass1"},
    )

    assert replay_response.status_code == 410
    assert replay_response.json()["code"] == "reset_token_invalid"
