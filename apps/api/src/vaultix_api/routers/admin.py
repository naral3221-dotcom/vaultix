import json
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from vaultix_api.deps import CurrentUser, get_db, problem, require_admin_user
from vaultix_api.models.core import Asset, AssetGenerationRequest, AssetReport, AssetTag, AuditLog, Category, Tag
from vaultix_api.services.generation_worker import process_generation_request

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

ASSET_STATUSES = {"inbox", "approved", "published", "rejected", "archived", "taken_down"}
ASSET_TYPES = {"image", "pptx", "svg", "docx", "xlsx", "html", "lottie", "colorbook", "icon_set"}
REPORT_STATUSES = {"open", "resolved", "dismissed"}
GENERATION_REQUEST_STATUSES = {"queued", "processing", "completed", "failed", "canceled"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class AssetStatusRequest(BaseModel):
    status: str
    reason: str | None = None


class AssetMetadataRequest(BaseModel):
    slug: str
    title: str
    description: str | None = None
    alt_text: str | None = None


class AssetImportTaxonomyRequest(BaseModel):
    slug: str
    name: str


class AssetImportItemRequest(BaseModel):
    slug: str
    title: str
    description: str | None = None
    alt_text: str | None = None
    file_path: str | None = None
    thumbnail_path: str | None = None
    preview_path: str | None = None
    mime_type: str | None = "image/png"
    category: AssetImportTaxonomyRequest | None = None
    tags: list[AssetImportTaxonomyRequest] = Field(default_factory=list)


class AssetBulkImportRequest(BaseModel):
    items: list[AssetImportItemRequest]


class ReportStatusRequest(BaseModel):
    status: str
    reason: str | None = None


class GenerationRequestCreateRequest(BaseModel):
    prompt: str
    asset_type: str = "image"
    provider_preference: str | None = "openai"
    admin_notes: str | None = None


class GenerationRequestStatusRequest(BaseModel):
    status: str
    admin_notes: str | None = None


def admin_asset_to_dict(asset: Asset) -> dict[str, object]:
    return {
        "id": asset.id,
        "slug": asset.slug,
        "title": asset.title_ko,
        "description": asset.description_ko,
        "alt_text": asset.alt_text_ko,
        "status": asset.status,
        "asset_type": asset.asset_type,
        "download_count": asset.download_count,
    }


def generation_request_to_dict(request: AssetGenerationRequest) -> dict[str, object]:
    return {
        "id": request.id,
        "prompt": request.prompt,
        "asset_type": request.asset_type,
        "provider_preference": request.provider_preference,
        "status": request.status,
        "admin_notes": request.admin_notes,
        "result_asset_id": request.result_asset_id,
    }


@router.get("/assets")
def list_admin_assets(
    status: str = "inbox",
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    if status not in ASSET_STATUSES:
        raise problem(400, "validation_error", "Validation error", "지원하지 않는 에셋 상태입니다.")
    bounded_limit = min(max(limit, 1), 100)
    assets = (
        db.query(Asset)
        .filter(Asset.status == status)
        .order_by(Asset.id.desc())
        .limit(bounded_limit)
        .all()
    )
    return {"data": [admin_asset_to_dict(asset) for asset in assets], "meta": {"limit": bounded_limit}}


@router.patch("/assets/{asset_id}/status")
def update_asset_status(
    asset_id: int,
    payload: AssetStatusRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    if payload.status not in ASSET_STATUSES:
        raise problem(400, "validation_error", "Validation error", "지원하지 않는 에셋 상태입니다.")

    asset = db.get(Asset, asset_id)
    if asset is None:
        raise problem(404, "asset_not_found", "Asset not found", "에셋을 찾을 수 없습니다.")

    previous_status = asset.status
    asset.status = payload.status
    audit = AuditLog(
        id=int(db.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0) + 1,
        actor_user_id=admin.id,
        action="asset.status_changed",
        target_type="asset",
        target_id=asset.id,
        metadata_json=json.dumps(
            {"from": previous_status, "reason": payload.reason, "to": payload.status},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )
    db.add(audit)
    db.commit()
    db.refresh(asset)
    return {"data": admin_asset_to_dict(asset)}


@router.post("/assets/import", status_code=201)
def bulk_import_assets(
    payload: AssetBulkImportRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    if not payload.items:
        raise problem(400, "validation_error", "Validation error", "등록할 에셋을 1개 이상 입력해 주세요.")
    if len(payload.items) > 50:
        raise problem(400, "validation_error", "Validation error", "한 번에 최대 50개까지 등록할 수 있습니다.")

    seen_slugs: set[str] = set()
    for item in payload.items:
        slug = item.slug.strip()
        title = item.title.strip()
        if len(title) < 2:
            raise problem(400, "validation_error", "Validation error", "제목은 2자 이상 입력해 주세요.")
        if not SLUG_PATTERN.fullmatch(slug):
            raise problem(400, "validation_error", "Validation error", "슬러그는 영문 소문자, 숫자, 하이픈만 사용할 수 있습니다.")
        if slug in seen_slugs:
            raise problem(409, "slug_conflict", "Slug conflict", "중복된 슬러그가 포함되어 있습니다.")
        seen_slugs.add(slug)

    existing_slug = db.query(Asset.slug).filter(Asset.slug.in_(seen_slugs)).first()
    if existing_slug is not None:
        raise problem(409, "slug_conflict", "Slug conflict", "이미 사용 중인 슬러그입니다.")

    next_asset_id = int(db.query(func.coalesce(func.max(Asset.id), 0)).scalar() or 0) + 1
    next_category_id = int(db.query(func.coalesce(func.max(Category.id), 0)).scalar() or 0) + 1
    next_tag_id = int(db.query(func.coalesce(func.max(Tag.id), 0)).scalar() or 0) + 1
    created_assets: list[Asset] = []

    for item in payload.items:
        category_id = None
        if item.category is not None:
            category_slug = item.category.slug.strip()
            if not SLUG_PATTERN.fullmatch(category_slug):
                raise problem(400, "validation_error", "Validation error", "카테고리 슬러그 형식이 올바르지 않습니다.")
            category = db.query(Category).filter(Category.slug == category_slug).first()
            if category is None:
                category = Category(id=next_category_id, slug=category_slug, name_ko=item.category.name.strip())
                next_category_id += 1
                db.add(category)
                db.flush()
            category_id = category.id

        asset = Asset(
            id=next_asset_id,
            slug=item.slug.strip(),
            asset_type="image",
            category_id=category_id,
            status="inbox",
            title_ko=item.title.strip(),
            description_ko=item.description.strip() if item.description else None,
            alt_text_ko=item.alt_text.strip() if item.alt_text else None,
            file_path=item.file_path.strip() if item.file_path else None,
            thumbnail_path=item.thumbnail_path.strip() if item.thumbnail_path else None,
            preview_path=item.preview_path.strip() if item.preview_path else None,
            mime_type=item.mime_type.strip() if item.mime_type else None,
            download_count=0,
        )
        next_asset_id += 1
        db.add(asset)
        db.flush()

        for tag_item in item.tags:
            tag_slug = tag_item.slug.strip()
            if not SLUG_PATTERN.fullmatch(tag_slug):
                raise problem(400, "validation_error", "Validation error", "태그 슬러그 형식이 올바르지 않습니다.")
            tag = db.query(Tag).filter(Tag.slug == tag_slug).first()
            if tag is None:
                tag = Tag(id=next_tag_id, slug=tag_slug, name_ko=tag_item.name.strip(), use_count=0)
                next_tag_id += 1
                db.add(tag)
                db.flush()
            tag.use_count += 1
            db.merge(AssetTag(asset_id=asset.id, tag_id=tag.id))

        created_assets.append(asset)

    db.add(
        AuditLog(
            id=int(db.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0) + 1,
            actor_user_id=admin.id,
            action="asset.bulk_imported",
            target_type="asset",
            target_id=created_assets[0].id,
            metadata_json=json.dumps(
                {"created_count": len(created_assets), "slugs": [asset.slug for asset in created_assets]},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    )
    db.commit()
    for asset in created_assets:
        db.refresh(asset)
    return {
        "data": {
            "created_count": len(created_assets),
            "assets": [admin_asset_to_dict(asset) for asset in created_assets],
        }
    }


@router.patch("/assets/{asset_id}")
def update_asset_metadata(
    asset_id: int,
    payload: AssetMetadataRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    slug = payload.slug.strip()
    title = payload.title.strip()
    description = payload.description.strip() if payload.description is not None else None
    alt_text = payload.alt_text.strip() if payload.alt_text is not None else None

    if len(title) < 2:
        raise problem(400, "validation_error", "Validation error", "제목은 2자 이상 입력해 주세요.")
    if not SLUG_PATTERN.fullmatch(slug):
        raise problem(400, "validation_error", "Validation error", "슬러그는 영문 소문자, 숫자, 하이픈만 사용할 수 있습니다.")

    asset = db.get(Asset, asset_id)
    if asset is None:
        raise problem(404, "asset_not_found", "Asset not found", "에셋을 찾을 수 없습니다.")

    slug_owner = db.query(Asset).filter(Asset.slug == slug, Asset.id != asset.id).first()
    if slug_owner is not None:
        raise problem(409, "slug_conflict", "Slug conflict", "이미 사용 중인 슬러그입니다.")

    changed = []
    if asset.slug != slug:
        asset.slug = slug
        changed.append("slug")
    if asset.title_ko != title:
        asset.title_ko = title
        changed.append("title")
    if asset.description_ko != description:
        asset.description_ko = description
        changed.append("description")
    if asset.alt_text_ko != alt_text:
        asset.alt_text_ko = alt_text
        changed.append("alt_text")

    db.add(
        AuditLog(
            id=int(db.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0) + 1,
            actor_user_id=admin.id,
            action="asset.metadata_updated",
            target_type="asset",
            target_id=asset.id,
            metadata_json=json.dumps(
                {"changed": sorted(changed)},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    )
    db.commit()
    db.refresh(asset)
    return {"data": admin_asset_to_dict(asset)}


@router.get("/reports")
def list_reports(
    status: str = "open",
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    if status not in REPORT_STATUSES:
        raise problem(400, "validation_error", "Validation error", "지원하지 않는 신고 상태입니다.")
    bounded_limit = min(max(limit, 1), 100)
    rows = (
        db.query(AssetReport, Asset)
        .join(Asset, Asset.id == AssetReport.asset_id)
        .filter(AssetReport.status == status)
        .order_by(AssetReport.id.desc())
        .limit(bounded_limit)
        .all()
    )
    return {
        "data": [
            {
                "id": report.id,
                "asset_id": report.asset_id,
                "asset_slug": asset.slug,
                "reason": report.reason,
                "message": report.message,
                "status": report.status,
            }
            for report, asset in rows
        ],
        "meta": {"limit": bounded_limit},
    }


@router.get("/generation-requests")
def list_generation_requests(
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    if status is not None and status not in GENERATION_REQUEST_STATUSES:
        raise problem(400, "validation_error", "Validation error", "지원하지 않는 생성 요청 상태입니다.")
    bounded_limit = min(max(limit, 1), 100)
    query = db.query(AssetGenerationRequest)
    if status is not None:
        query = query.filter(AssetGenerationRequest.status == status)
    requests = query.order_by(AssetGenerationRequest.id.desc()).limit(bounded_limit).all()
    return {"data": [generation_request_to_dict(request) for request in requests], "meta": {"limit": bounded_limit}}


@router.post("/generation-requests", status_code=201)
def create_generation_request(
    payload: GenerationRequestCreateRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    prompt = payload.prompt.strip()
    if len(prompt) < 8:
        raise problem(400, "validation_error", "Validation error", "생성 요청은 8자 이상 입력해 주세요.")
    if payload.asset_type not in ASSET_TYPES:
        raise problem(400, "validation_error", "Validation error", "지원하지 않는 에셋 유형입니다.")
    next_request_id = int(db.query(func.coalesce(func.max(AssetGenerationRequest.id), 0)).scalar() or 0) + 1
    request = AssetGenerationRequest(
        id=next_request_id,
        requester_user_id=admin.id,
        prompt=prompt,
        asset_type=payload.asset_type,
        provider_preference=payload.provider_preference.strip() if payload.provider_preference else None,
        status="queued",
        admin_notes=payload.admin_notes.strip() if payload.admin_notes else None,
    )
    db.add(request)
    db.flush()
    db.add(
        AuditLog(
            id=int(db.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0) + 1,
            actor_user_id=admin.id,
            action="asset_generation_request.created",
            target_type="asset_generation_request",
            target_id=request.id,
            metadata_json=json.dumps(
                {"asset_type": request.asset_type, "provider": request.provider_preference},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    )
    db.commit()
    db.refresh(request)
    return {"data": generation_request_to_dict(request)}


@router.patch("/generation-requests/{request_id}/status")
def update_generation_request_status(
    request_id: int,
    payload: GenerationRequestStatusRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    if payload.status not in GENERATION_REQUEST_STATUSES:
        raise problem(400, "validation_error", "Validation error", "지원하지 않는 생성 요청 상태입니다.")
    request = db.get(AssetGenerationRequest, request_id)
    if request is None:
        raise problem(404, "generation_request_not_found", "Generation request not found", "생성 요청을 찾을 수 없습니다.")
    previous_status = request.status
    request.status = payload.status
    if payload.admin_notes is not None:
        request.admin_notes = payload.admin_notes.strip() or None
    db.add(
        AuditLog(
            id=int(db.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0) + 1,
            actor_user_id=admin.id,
            action="asset_generation_request.status_changed",
            target_type="asset_generation_request",
            target_id=request.id,
            metadata_json=json.dumps(
                {"from": previous_status, "to": payload.status},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    )
    db.commit()
    db.refresh(request)
    return {"data": generation_request_to_dict(request)}


@router.post("/generation-requests/{request_id}/run")
def run_generation_request_worker(
    request_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    request = process_generation_request(db, request_id=request_id, actor_user_id=admin.id)
    if request is None:
        raise problem(404, "generation_request_not_found", "Generation request not found", "생성 요청을 찾을 수 없습니다.")
    return {"data": generation_request_to_dict(request)}


@router.patch("/reports/{report_id}/status")
def update_report_status(
    report_id: int,
    payload: ReportStatusRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    if payload.status not in REPORT_STATUSES:
        raise problem(400, "validation_error", "Validation error", "지원하지 않는 신고 상태입니다.")

    report = db.get(AssetReport, report_id)
    if report is None:
        raise problem(404, "report_not_found", "Report not found", "신고를 찾을 수 없습니다.")
    asset = db.get(Asset, report.asset_id)
    if asset is None:
        raise problem(404, "asset_not_found", "Asset not found", "에셋을 찾을 수 없습니다.")

    previous_status = report.status
    report.status = payload.status
    audit = AuditLog(
        id=int(db.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0) + 1,
        actor_user_id=admin.id,
        action="asset_report.status_changed",
        target_type="asset_report",
        target_id=report.id,
        metadata_json=json.dumps(
            {"from": previous_status, "reason": payload.reason, "to": payload.status},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )
    db.add(audit)
    db.commit()
    db.refresh(report)
    return {
        "data": {
            "id": report.id,
            "asset_id": report.asset_id,
            "asset_slug": asset.slug,
            "reason": report.reason,
            "message": report.message,
            "status": report.status,
        }
    }


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin_user),
) -> dict[str, object]:
    bounded_limit = min(max(limit, 1), 100)
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(bounded_limit).all()
    return {
        "data": [
            {
                "id": log.id,
                "actor_user_id": log.actor_user_id,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "metadata": json.loads(log.metadata_json) if log.metadata_json else None,
            }
            for log in logs
        ],
        "meta": {"limit": bounded_limit},
    }
