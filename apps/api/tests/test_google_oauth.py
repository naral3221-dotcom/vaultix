from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.deps import get_db
from vaultix_api.main import app
from vaultix_api.models.core import Session as UserSession, User
from vaultix_api.services.google_oauth import build_google_authorize_url, sign_oauth_state, verify_oauth_state
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


def test_oauth_state_roundtrip_rejects_tampering():
    state = sign_oauth_state("secret", "https://vaultix.example.com/explore")

    assert verify_oauth_state("secret", state) == "https://vaultix.example.com/explore"
    assert verify_oauth_state("secret", f"{state}x") is None


def test_build_google_authorize_url_contains_required_openid_parameters():
    url = build_google_authorize_url(
        client_id="client-id",
        redirect_uri="https://vaultix.example.com/api/v1/auth/google/callback",
        state="signed-state",
    )

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=client-id" in url
    assert "response_type=code" in url
    assert "scope=openid+email+profile" in url
    assert "state=signed-state" in url


def test_google_start_redirects_to_google_authorize(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://vaultix.example.com")
    get_settings.cache_clear()

    response = client.get("/api/v1/auth/google/start", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=client-id" in response.headers["location"]


def test_google_callback_creates_user_session_and_promotes_admin(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://vaultix.example.com")
    monkeypatch.setenv("ADMIN_EMAILS", "naral3221@gmail.com")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "vaultix_api.routers.auth.exchange_google_code",
        lambda **_kwargs: {
            "email": "naral3221@gmail.com",
            "email_verified": True,
            "name": "Naral",
        },
    )
    state = sign_oauth_state(get_settings().auth_secret, "/admin")

    response = client.get(
        f"/api/v1/auth/google/callback?code=valid-code&state={state}",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "/admin"
    assert "vaultix.session=" in response.headers["set-cookie"]
    with client.app.state.test_sessionmaker() as session:
        user = session.query(User).filter(User.email_lower == "naral3221@gmail.com").one()
        assert user.email_verified_at is not None
        assert user.display_name == "Naral"
        assert user.role == "admin"
        assert session.query(UserSession).filter(UserSession.user_id == user.id).count() == 1


def test_google_callback_rejects_invalid_state(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    get_settings.cache_clear()

    response = client.get("/api/v1/auth/google/callback?code=valid-code&state=bad")

    assert response.status_code == 400
    assert response.json()["code"] == "oauth_state_invalid"
