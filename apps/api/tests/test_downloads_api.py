from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.deps import CurrentUser, get_db, require_verified_user
from vaultix_api.main import app
from vaultix_api.models.core import Asset, Category, Session as UserSession, User
from vaultix_api.services.download_tokens import download_rate_limiter, download_token_store


def test_download_intent_requires_a_verified_user(client: TestClient):
    response = client.post("/api/v1/downloads/1")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


def test_download_intent_accepts_authjs_session_cookie(client: TestClient):
    client.cookies.set("__Secure-vaultix.session", "verified-session-token")

    response = client.post("/api/v1/downloads/1")

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["download_url"].startswith("/dl/1/")


def test_download_intent_rejects_unverified_session_cookie(client: TestClient):
    client.cookies.set("__Secure-vaultix.session", "unverified-session-token")

    response = client.post("/api/v1/downloads/1")

    assert response.status_code == 403
    assert response.json()["code"] == "email_not_verified"


def test_download_intent_rejects_expired_session_cookie(client: TestClient):
    client.cookies.set("__Secure-vaultix.session", "expired-session-token")

    response = client.post("/api/v1/downloads/1")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


def test_download_intent_issues_single_use_link_and_download_consumes(client: TestClient):
    app.dependency_overrides[require_verified_user] = lambda: CurrentUser(
        id=7,
        email_lower="verified@example.com",
        email_verified_at=datetime.now(UTC),
    )

    intent_response = client.post("/api/v1/downloads/1")

    assert intent_response.status_code == 201
    intent_payload = intent_response.json()["data"]
    assert intent_payload["download_url"].startswith("/dl/1/")
    assert intent_payload["expires_in_seconds"] == 300

    download_response = client.get(intent_payload["download_url"])

    assert download_response.status_code == 204
    assert download_response.headers["x-accel-redirect"] == "/cdn/original/business-meeting.png"

    replay_response = client.get(intent_payload["download_url"])

    assert replay_response.status_code == 410
    assert replay_response.json()["code"] == "download_link_invalid"


def test_download_intent_returns_404_for_missing_or_unpublished_asset(client: TestClient):
    app.dependency_overrides[require_verified_user] = lambda: CurrentUser(
        id=7,
        email_lower="verified@example.com",
        email_verified_at=datetime.now(UTC),
    )

    response = client.post("/api/v1/downloads/999")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_download_intent_blocks_the_31st_hourly_request(client: TestClient):
    app.dependency_overrides[require_verified_user] = lambda: CurrentUser(
        id=7,
        email_lower="verified@example.com",
        email_verified_at=datetime.now(UTC),
    )

    for _ in range(30):
        assert client.post("/api/v1/downloads/1").status_code == 201

    response = client.post("/api/v1/downloads/1")

    assert response.status_code == 429
    assert response.headers["X-RateLimit-Limit"] == "30"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.json()["code"] == "rate_limit_exceeded"


def test_download_link_returns_410_for_invalid_nonce(client: TestClient):
    response = client.get("/dl/1/not-a-real-nonce")

    assert response.status_code == 410
    assert response.json()["code"] == "download_link_invalid"


def seed_catalog(session: Session) -> None:
    now = datetime.now(UTC)
    verified = User(
        id=7,
        email="verified@example.com",
        email_lower="verified@example.com",
        email_verified_at=now,
        status="active",
    )
    unverified = User(
        id=8,
        email="unverified@example.com",
        email_lower="unverified@example.com",
        email_verified_at=None,
        status="active",
    )
    category = Category(id=1, slug="business", name_ko="비즈니스", sort_order=1)
    asset = Asset(
        id=1,
        slug="business-meeting-illustration",
        asset_type="image",
        category_id=1,
        status="published",
        title_ko="비즈니스 미팅 일러스트",
        description_ko="보고서와 발표자료에 쓰기 좋은 회의 장면 이미지입니다.",
        alt_text_ko="회의실에서 사람들이 발표 자료를 보는 장면",
        thumbnail_path="/cdn/thumb/business-meeting.webp",
        preview_path="/cdn/preview/business-meeting.webp",
        file_path="/cdn/original/business-meeting.png",
        mime_type="image/png",
        checksum="abc123",
        download_count=42,
    )
    session.add_all(
        [
            verified,
            unverified,
            UserSession(
                id=1,
                session_token="verified-session-token",
                user_id=7,
                expires=now + timedelta(hours=1),
            ),
            UserSession(
                id=2,
                session_token="unverified-session-token",
                user_id=8,
                expires=now + timedelta(hours=1),
            ),
            UserSession(
                id=3,
                session_token="expired-session-token",
                user_id=7,
                expires=now - timedelta(minutes=1),
            ),
            category,
            asset,
        ]
    )
    session.commit()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with maker() as session:
        seed_catalog(session)

    def override_get_db() -> Iterator[Session]:
        with maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    download_token_store.clear()
    download_rate_limiter.clear()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        download_token_store.clear()
        download_rate_limiter.clear()
