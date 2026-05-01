from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from vaultix_api.db.base import Base
from vaultix_api.models.core import Asset, AssetGenerationRequest, AuditLog
from vaultix_api.services.generation_worker import GeneratedImage, process_generation_request, process_next_generation_request
from vaultix_api.settings import get_settings


def test_process_generation_request_creates_inbox_asset_and_marks_completed(monkeypatch, tmp_path):
    session = make_session()
    request = AssetGenerationRequest(
        id=1,
        prompt="업무 보고서용 미니멀 히어로 이미지",
        asset_type="image",
        provider_preference="openai",
        status="queued",
    )
    session.add(request)
    session.commit()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
    monkeypatch.setenv("GENERATED_ASSET_DIR", str(tmp_path))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "vaultix_api.services.generation_worker.generate_openai_image",
        lambda **_kwargs: GeneratedImage(
            image_bytes=b"fake-image-bytes",
            model="gpt-image-1.5",
            revised_prompt="업무 보고서용 미니멀 히어로 이미지",
        ),
    )

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
    assert asset.checksum == "generated:1:openai:gpt-image-1.5"
    assert asset.file_path == str(tmp_path / "request-1.png")
    assert (tmp_path / "request-1.png").read_bytes() == b"fake-image-bytes"
    audit = session.query(AuditLog).filter(AuditLog.action == "asset_generation_request.completed").one()
    assert audit.actor_user_id == 7
    assert audit.target_id == 1
    get_settings.cache_clear()


def test_process_next_generation_request_claims_oldest_queued_request(monkeypatch, tmp_path):
    session = make_session()
    session.add_all(
        [
            AssetGenerationRequest(id=1, prompt="첫 번째 요청", asset_type="image", status="completed"),
            AssetGenerationRequest(id=2, prompt="두 번째 요청", asset_type="image", status="queued"),
        ]
    )
    session.commit()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GENERATED_ASSET_DIR", str(tmp_path))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "vaultix_api.services.generation_worker.generate_openai_image",
        lambda **_kwargs: GeneratedImage(
            image_bytes=b"fake-image-bytes",
            model="gpt-image-1.5",
            revised_prompt=None,
        ),
    )

    result = process_next_generation_request(session)

    assert result is not None
    assert result.id == 2
    assert session.get(AssetGenerationRequest, 2).status == "completed"
    get_settings.cache_clear()


def test_process_generation_request_fails_without_openai_key():
    session = make_session()
    session.add(
        AssetGenerationRequest(
            id=1,
            prompt="키 없는 요청",
            asset_type="image",
            provider_preference="openai",
            status="queued",
        )
    )
    session.commit()
    get_settings.cache_clear()

    result = process_generation_request(session, request_id=1)

    assert result.status == "failed"
    assert result.admin_notes == "OPENAI_API_KEY가 설정되지 않았습니다."
    assert session.query(Asset).count() == 0


def make_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return maker()
