from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.deps import get_db
from vaultix_api.main import app
from vaultix_api.models.core import Asset, AssetTag, Category, Tag


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
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def seed_catalog(session: Session) -> None:
    business = Category(id=1, slug="business", name_ko="비즈니스", sort_order=1)
    marketing = Category(id=2, slug="marketing", name_ko="마케팅", sort_order=2)
    meeting = Tag(id=1, slug="meeting", name_ko="미팅")
    report = Tag(id=2, slug="report", name_ko="보고서")
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
    session.add_all([business, marketing, meeting, report, asset])
    session.flush()
    session.add_all([AssetTag(asset_id=1, tag_id=1), AssetTag(asset_id=1, tag_id=2)])
    session.commit()


def test_categories_endpoint_returns_active_category_tree(client: TestClient):
    response = client.get("/api/v1/meta/categories")

    assert response.status_code == 200
    assert response.json()["data"][0] == {
        "id": 1,
        "slug": "business",
        "name_ko": "비즈니스",
        "name": "비즈니스",
        "children": [],
    }


def test_tags_endpoint_filters_by_query(client: TestClient):
    response = client.get("/api/v1/meta/tags?q=보")

    assert response.status_code == 200
    assert response.json()["data"] == [{"id": 2, "slug": "report", "name_ko": "보고서", "name": "보고서"}]


def test_assets_endpoint_returns_published_assets(client: TestClient):
    response = client.get("/api/v1/assets?category=business&limit=12")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"] == {"next_cursor": None, "limit": 12, "total_estimate": 1}
    assert payload["data"][0]["slug"] == "business-meeting-illustration"
    assert payload["data"][0]["category"] == {"id": 1, "slug": "business", "name": "비즈니스"}
    assert payload["data"][0]["tags"] == [
        {"slug": "meeting", "name": "미팅"},
        {"slug": "report", "name": "보고서"},
    ]


def test_asset_detail_endpoint_resolves_slug(client: TestClient):
    response = client.get("/api/v1/assets/business-meeting-illustration")

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "비즈니스 미팅 일러스트"


def test_asset_detail_endpoint_returns_404_for_missing_asset(client: TestClient):
    response = client.get("/api/v1/assets/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "asset_not_found"
