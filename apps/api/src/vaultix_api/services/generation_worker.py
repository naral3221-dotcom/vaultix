import json
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from vaultix_api.models.core import Asset, AssetGenerationRequest, AuditLog
from vaultix_api.services.openai_images import GeneratedImage, generate_openai_image
from vaultix_api.settings import get_settings


def process_next_generation_request(
    db: Session,
    *,
    actor_user_id: int | None = None,
) -> AssetGenerationRequest | None:
    request = (
        db.query(AssetGenerationRequest)
        .filter(AssetGenerationRequest.status == "queued")
        .order_by(AssetGenerationRequest.id.asc())
        .first()
    )
    if request is None:
        return None
    return process_generation_request(db, request_id=request.id, actor_user_id=actor_user_id)


def process_generation_request(
    db: Session,
    *,
    request_id: int,
    actor_user_id: int | None = None,
) -> AssetGenerationRequest | None:
    request = db.get(AssetGenerationRequest, request_id)
    if request is None:
        return None
    if request.status == "completed":
        return request
    if request.status not in {"queued", "processing"}:
        request.status = "failed"
        request.admin_notes = "처리할 수 없는 생성 요청 상태입니다."
        db.commit()
        return request

    settings = get_settings()
    if not settings.openai_api_key:
        request.status = "failed"
        request.admin_notes = "OPENAI_API_KEY가 설정되지 않았습니다."
        db.commit()
        db.refresh(request)
        return request

    request.status = "processing"
    db.flush()
    try:
        generated = generate_openai_image(
            api_key=settings.openai_api_key,
            model=settings.openai_image_model,
            prompt=request.prompt,
        )
    except Exception as exc:
        request.status = "failed"
        request.admin_notes = f"OpenAI 이미지 생성 실패: {exc.__class__.__name__}"
        db.commit()
        db.refresh(request)
        return request

    stored_path = _store_generated_image(
        generated.image_bytes,
        request_id=request.id,
        generated_asset_dir=settings.generated_asset_dir,
    )
    asset = _create_inbox_asset_from_request(db, request, generated, stored_path)
    request.status = "completed"
    request.result_asset_id = asset.id
    request.admin_notes = "생성 완료"
    db.add(
        AuditLog(
            id=_next_id(db, AuditLog),
            actor_user_id=actor_user_id,
            action="asset_generation_request.completed",
            target_type="asset_generation_request",
            target_id=request.id,
            metadata_json=json.dumps(
                {"asset_id": asset.id, "model": generated.model, "provider": "openai"},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    )
    db.commit()
    db.refresh(request)
    return request


def _create_inbox_asset_from_request(
    db: Session,
    request: AssetGenerationRequest,
    generated: GeneratedImage,
    stored_path: str,
) -> Asset:
    existing = (
        db.query(Asset)
        .filter(Asset.slug == _asset_slug(request.id))
        .first()
    )
    if existing is not None:
        return existing
    asset = Asset(
        id=_next_id(db, Asset),
        slug=_asset_slug(request.id),
        asset_type=request.asset_type,
        status="inbox",
        title_ko=f"AI 생성 결과 #{request.id}",
        description_ko=f"생성 요청 프롬프트: {generated.revised_prompt or request.prompt}",
        alt_text_ko=(generated.revised_prompt or request.prompt)[:500],
        file_path=stored_path,
        thumbnail_path=stored_path,
        preview_path=stored_path,
        mime_type="image/png",
        file_size_bytes=len(generated.image_bytes),
        checksum=f"generated:{request.id}:openai:{generated.model}",
        download_count=0,
    )
    db.add(asset)
    db.flush()
    return asset


def _asset_slug(request_id: int) -> str:
    return f"generated-request-{request_id}"


def _store_generated_image(
    image_bytes: bytes,
    *,
    request_id: int,
    generated_asset_dir: str,
) -> str:
    directory = Path(generated_asset_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"request-{request_id}.png"
    path.write_bytes(image_bytes)
    return str(path)


def _next_id(db: Session, model: type[object]) -> int:
    return int(db.query(func.coalesce(func.max(model.id), 0)).scalar() or 0) + 1
