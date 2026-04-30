import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from vaultix_api.models.core import Asset, AssetGenerationRequest, AuditLog


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

    request.status = "processing"
    db.flush()
    asset = _create_inbox_asset_from_request(db, request)
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
                {"asset_id": asset.id, "provider": request.provider_preference or "local"},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    )
    db.commit()
    db.refresh(request)
    return request


def _create_inbox_asset_from_request(db: Session, request: AssetGenerationRequest) -> Asset:
    existing = (
        db.query(Asset)
        .filter(Asset.slug == _asset_slug(request.id))
        .first()
    )
    if existing is not None:
        return existing
    provider = request.provider_preference or "local"
    asset = Asset(
        id=_next_id(db, Asset),
        slug=_asset_slug(request.id),
        asset_type=request.asset_type,
        status="inbox",
        title_ko=f"AI 생성 결과 #{request.id}",
        description_ko=f"생성 요청 프롬프트: {request.prompt}",
        alt_text_ko=request.prompt[:500],
        file_path=f"/generated/request-{request.id}.png",
        thumbnail_path=f"/generated/request-{request.id}.webp",
        preview_path=f"/generated/request-{request.id}.webp",
        mime_type="image/png",
        checksum=f"generated:{request.id}:{provider}",
        download_count=0,
    )
    db.add(asset)
    db.flush()
    return asset


def _asset_slug(request_id: int) -> str:
    return f"generated-request-{request_id}"


def _next_id(db: Session, model: type[object]) -> int:
    return int(db.query(func.coalesce(func.max(model.id), 0)).scalar() or 0) + 1
