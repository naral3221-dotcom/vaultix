from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.deps import get_db
from vaultix_api.main import app
from vaultix_api.models.core import (
    Asset,
    AssetTag,
    Category,
    AssetGenerationRequest,
    AssetReport,
    AuditLog,
    Session as UserSession,
    Tag,
    User,
)
from vaultix_api.services.passwords import hash_password


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
    with maker() as session:
        seed_admin_fixture(session)

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


def seed_admin_fixture(session: Session) -> None:
    now = datetime.now(UTC)
    admin = User(
        id=1,
        email="admin@example.com",
        email_lower="admin@example.com",
        password_hash=hash_password("password1"),
        role="admin",
        status="active",
        email_verified_at=now,
    )
    member = User(
        id=2,
        email="member@example.com",
        email_lower="member@example.com",
        password_hash=hash_password("password1"),
        role="member",
        status="active",
        email_verified_at=now,
    )
    asset = Asset(
        id=101,
        slug="pending-asset",
        asset_type="image",
        status="inbox",
        title_ko="검수 대기 에셋",
        description_ko="관리자 검수 대기",
        alt_text_ko="검수 대기",
        download_count=0,
    )
    session.add_all([admin, member, asset])
    session.flush()
    session.add_all(
        [
            UserSession(
                id=1,
                session_token="admin-session",
                user_id=1,
                expires=now + timedelta(days=1),
            ),
            UserSession(
                id=2,
                session_token="member-session",
                user_id=2,
                expires=now + timedelta(days=1),
            ),
        ]
    )
    session.commit()


def test_admin_assets_require_admin_session(client: TestClient):
    client.cookies.set("vaultix.session", "member-session")

    response = client.get("/api/v1/admin/assets")

    assert response.status_code == 403
    assert response.json()["code"] == "admin_required"


def test_admin_can_list_inbox_assets(client: TestClient):
    client.cookies.set("vaultix.session", "admin-session")

    response = client.get("/api/v1/admin/assets?status=inbox")

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "id": 101,
            "slug": "pending-asset",
            "title": "검수 대기 에셋",
            "description": "관리자 검수 대기",
            "alt_text": "검수 대기",
            "status": "inbox",
            "asset_type": "image",
            "download_count": 0,
        }
    ]


def test_admin_can_change_asset_status_and_writes_audit_log(client: TestClient):
    client.cookies.set("vaultix.session", "admin-session")

    response = client.patch(
        "/api/v1/admin/assets/101/status",
        json={"status": "published", "reason": "검수 완료"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "published"
    with client.app.state.test_sessionmaker() as session:
        asset = session.get(Asset, 101)
        audit = session.query(AuditLog).one()
        assert asset.status == "published"
        assert audit.actor_user_id == 1
        assert audit.action == "asset.status_changed"
        assert audit.target_type == "asset"
        assert audit.target_id == 101
        assert audit.metadata_json == '{"from":"inbox","reason":"검수 완료","to":"published"}'


def test_admin_can_edit_asset_metadata_and_writes_audit_log(client: TestClient):
    client.cookies.set("vaultix.session", "admin-session")

    response = client.patch(
        "/api/v1/admin/assets/101",
        json={
            "slug": "minimal-dashboard-reference",
            "title": "미니멀 대시보드 레퍼런스",
            "description": "SaaS 관리자 화면에 쓰기 좋은 이미지",
            "alt_text": "밝은 배경의 미니멀 대시보드 이미지",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": 101,
        "slug": "minimal-dashboard-reference",
        "title": "미니멀 대시보드 레퍼런스",
        "description": "SaaS 관리자 화면에 쓰기 좋은 이미지",
        "alt_text": "밝은 배경의 미니멀 대시보드 이미지",
        "status": "inbox",
        "asset_type": "image",
        "download_count": 0,
    }
    with client.app.state.test_sessionmaker() as session:
        asset = session.get(Asset, 101)
        audit = session.query(AuditLog).filter(AuditLog.action == "asset.metadata_updated").one()
        assert asset.slug == "minimal-dashboard-reference"
        assert asset.title_ko == "미니멀 대시보드 레퍼런스"
        assert asset.description_ko == "SaaS 관리자 화면에 쓰기 좋은 이미지"
        assert asset.alt_text_ko == "밝은 배경의 미니멀 대시보드 이미지"
        assert audit.actor_user_id == 1
        assert audit.target_type == "asset"
        assert audit.target_id == 101
        assert audit.metadata_json == '{"changed":["alt_text","description","slug","title"]}'


def test_admin_can_bulk_import_image_assets_with_categories_and_tags(client: TestClient):
    client.cookies.set("vaultix.session", "admin-session")

    response = client.post(
        "/api/v1/admin/assets/import",
        json={
            "items": [
                {
                    "slug": "dashboard-hero-reference",
                    "title": "대시보드 히어로 레퍼런스",
                    "description": "SaaS 랜딩 페이지에 쓰기 좋은 히어로 이미지",
                    "alt_text": "밝은 배경의 SaaS 대시보드 히어로 이미지",
                    "file_path": "/cdn/original/dashboard-hero.png",
                    "thumbnail_path": "/cdn/thumb/dashboard-hero.webp",
                    "preview_path": "/cdn/preview/dashboard-hero.webp",
                    "mime_type": "image/png",
                    "category": {"slug": "saas", "name": "SaaS"},
                    "tags": [{"slug": "hero", "name": "히어로"}, {"slug": "dashboard", "name": "대시보드"}],
                },
                {
                    "slug": "newsletter-card-reference",
                    "title": "뉴스레터 카드 레퍼런스",
                    "description": "업무 생산성 뉴스레터에 어울리는 카드 이미지",
                    "alt_text": "뉴스레터 카드형 레퍼런스 이미지",
                    "file_path": "/cdn/original/newsletter-card.png",
                    "category": {"slug": "marketing", "name": "마케팅"},
                    "tags": [{"slug": "newsletter", "name": "뉴스레터"}],
                },
            ]
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["created_count"] == 2
    assert [asset["slug"] for asset in response.json()["data"]["assets"]] == [
        "dashboard-hero-reference",
        "newsletter-card-reference",
    ]
    with client.app.state.test_sessionmaker() as session:
        dashboard = session.query(Asset).filter(Asset.slug == "dashboard-hero-reference").one()
        newsletter = session.query(Asset).filter(Asset.slug == "newsletter-card-reference").one()
        saas = session.query(Category).filter(Category.slug == "saas").one()
        marketing = session.query(Category).filter(Category.slug == "marketing").one()
        tags = {tag.slug: tag for tag in session.query(Tag).all()}
        audit = session.query(AuditLog).filter(AuditLog.action == "asset.bulk_imported").one()
        assert dashboard.status == "inbox"
        assert dashboard.category_id == saas.id
        assert newsletter.category_id == marketing.id
        assert {"hero", "dashboard", "newsletter"}.issubset(tags)
        assert session.query(AssetTag).filter(AssetTag.asset_id == dashboard.id).count() == 2
        assert audit.metadata_json == '{"created_count":2,"slugs":["dashboard-hero-reference","newsletter-card-reference"]}'


def test_asset_report_is_created_and_visible_to_admin(client: TestClient):
    report_response = client.post(
        "/api/v1/assets/101/report",
        json={"reason": "copyright", "message": "저작권 확인이 필요합니다."},
    )
    client.cookies.set("vaultix.session", "admin-session")
    inbox_response = client.get("/api/v1/admin/reports")

    assert report_response.status_code == 201
    assert report_response.json()["data"]["status"] == "open"
    assert inbox_response.status_code == 200
    assert inbox_response.json()["data"][0] == {
        "id": 1,
        "asset_id": 101,
        "asset_slug": "pending-asset",
        "reason": "copyright",
        "message": "저작권 확인이 필요합니다.",
        "status": "open",
    }

    with client.app.state.test_sessionmaker() as session:
        assert session.query(AssetReport).count() == 1


def test_admin_can_resolve_report_and_writes_audit_log(client: TestClient):
    with client.app.state.test_sessionmaker() as session:
        session.add(
            AssetReport(
                id=1,
                asset_id=101,
                reason="copyright",
                message="저작권 확인이 필요합니다.",
                status="open",
            )
        )
        session.commit()
    client.cookies.set("vaultix.session", "admin-session")

    response = client.patch(
        "/api/v1/admin/reports/1/status",
        json={"status": "resolved", "reason": "권리 확인 완료"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "resolved"
    with client.app.state.test_sessionmaker() as session:
        report = session.get(AssetReport, 1)
        audit = session.query(AuditLog).filter(AuditLog.target_type == "asset_report").one()
        assert report.status == "resolved"
        assert audit.actor_user_id == 1
        assert audit.action == "asset_report.status_changed"
        assert audit.target_id == 1
        assert audit.metadata_json == '{"from":"open","reason":"권리 확인 완료","to":"resolved"}'


def test_admin_can_list_recent_audit_logs(client: TestClient):
    with client.app.state.test_sessionmaker() as session:
        session.add(
            AuditLog(
                id=1,
                actor_user_id=1,
                action="asset.status_changed",
                target_type="asset",
                target_id=101,
                metadata_json='{"from":"inbox","to":"published"}',
            )
        )
        session.commit()
    client.cookies.set("vaultix.session", "admin-session")

    response = client.get("/api/v1/admin/audit-logs")

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "id": 1,
            "actor_user_id": 1,
            "action": "asset.status_changed",
            "target_type": "asset",
            "target_id": 101,
            "metadata": {"from": "inbox", "to": "published"},
        }
    ]


def test_admin_can_create_and_list_generation_requests(client: TestClient):
    client.cookies.set("vaultix.session", "admin-session")

    create_response = client.post(
        "/api/v1/admin/generation-requests",
        json={
            "prompt": "업무 보고서용 미니멀 아이콘 세트",
            "asset_type": "icon_set",
            "provider_preference": "openai",
            "admin_notes": "첫 MVP 큐 검증",
        },
    )
    list_response = client.get("/api/v1/admin/generation-requests")

    assert create_response.status_code == 201
    assert create_response.json()["data"] == {
        "id": 1,
        "prompt": "업무 보고서용 미니멀 아이콘 세트",
        "asset_type": "icon_set",
        "provider_preference": "openai",
        "status": "queued",
        "admin_notes": "첫 MVP 큐 검증",
        "result_asset_id": None,
    }
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["prompt"] == "업무 보고서용 미니멀 아이콘 세트"
    with client.app.state.test_sessionmaker() as session:
        request = session.query(AssetGenerationRequest).one()
        audit = session.query(AuditLog).filter(AuditLog.target_type == "asset_generation_request").one()
        assert request.status == "queued"
        assert audit.action == "asset_generation_request.created"


def test_admin_generation_request_defaults_to_openai(client: TestClient):
    client.cookies.set("vaultix.session", "admin-session")

    response = client.post(
        "/api/v1/admin/generation-requests",
        json={"prompt": "기본 provider 확인용 이미지", "asset_type": "image"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["provider_preference"] == "openai"


def test_admin_can_advance_generation_request_status(client: TestClient):
    with client.app.state.test_sessionmaker() as session:
        session.add(
            AssetGenerationRequest(
                id=1,
                prompt="SNS 배너 배경",
                asset_type="image",
                provider_preference="openai",
                status="queued",
            )
        )
        session.commit()
    client.cookies.set("vaultix.session", "admin-session")

    response = client.patch(
        "/api/v1/admin/generation-requests/1/status",
        json={"status": "processing", "admin_notes": "프롬프트 확인 완료"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "processing"
    assert response.json()["data"]["admin_notes"] == "프롬프트 확인 완료"
    with client.app.state.test_sessionmaker() as session:
        request = session.get(AssetGenerationRequest, 1)
        audit = session.query(AuditLog).filter(AuditLog.action == "asset_generation_request.status_changed").one()
        assert request.status == "processing"
        assert audit.metadata_json == '{"from":"queued","to":"processing"}'


def test_admin_can_run_generation_request_worker(client: TestClient):
    with client.app.state.test_sessionmaker() as session:
        session.add(
            AssetGenerationRequest(
                id=1,
                prompt="랜딩 페이지용 추상 배경 이미지",
                asset_type="image",
                provider_preference="openai",
                status="queued",
            )
        )
        session.commit()
    client.cookies.set("vaultix.session", "admin-session")

    response = client.post("/api/v1/admin/generation-requests/1/run")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "failed"
    assert response.json()["data"]["result_asset_id"] is None
    with client.app.state.test_sessionmaker() as session:
        request = session.get(AssetGenerationRequest, 1)
        assert request.status == "failed"
        assert request.admin_notes == "OPENAI_API_KEY가 설정되지 않았습니다."
        assert session.query(Asset).filter(Asset.slug == "generated-request-1").first() is None
