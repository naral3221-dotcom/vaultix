from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.models.core import Asset, AssetGenerationRequest, AuditLog
from vaultix_api.services.generation_worker import process_generation_request, process_next_generation_request


def test_process_generation_request_creates_inbox_asset_and_marks_completed():
    session = make_session()
    request = AssetGenerationRequest(
        id=1,
        prompt="업무 보고서용 미니멀 히어로 이미지",
        asset_type="image",
        provider_preference="nanobanana",
        status="queued",
    )
    session.add(request)
    session.commit()

    result = process_generation_request(session, request_id=1, actor_user_id=7)

    assert result is not None
    assert result.status == "completed"
    assert result.result_asset_id == 1
    asset = session.get(Asset, 1)
    assert asset is not None
    assert asset.status == "inbox"
    assert asset.slug == "generated-request-1"
    assert asset.title_ko == "AI 생성 결과 #1"
    assert "업무 보고서용 미니멀 히어로 이미지" in asset.description_ko
    assert asset.checksum == "generated:1:nanobanana"
    audit = session.query(AuditLog).filter(AuditLog.action == "asset_generation_request.completed").one()
    assert audit.actor_user_id == 7
    assert audit.target_id == 1


def test_process_next_generation_request_claims_oldest_queued_request():
    session = make_session()
    session.add_all(
        [
            AssetGenerationRequest(id=1, prompt="첫 번째 요청", asset_type="image", status="completed"),
            AssetGenerationRequest(id=2, prompt="두 번째 요청", asset_type="image", status="queued"),
        ]
    )
    session.commit()

    result = process_next_generation_request(session)

    assert result is not None
    assert result.id == 2
    assert session.get(AssetGenerationRequest, 2).status == "completed"


def make_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return maker()
