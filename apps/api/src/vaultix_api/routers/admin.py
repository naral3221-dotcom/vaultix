import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from vaultix_api.deps import CurrentUser, get_db, problem, require_admin_user
from vaultix_api.models.core import Asset, AssetGenerationRequest, AssetReport, AuditLog
from vaultix_api.services.generation_worker import process_generation_request

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

ASSET_STATUSES = {"inbox", "approved", "published", "rejected", "archived", "taken_down"}
ASSET_TYPES = {"image", "pptx", "svg", "docx", "xlsx", "html", "lottie", "colorbook", "icon_set"}
REPORT_STATUSES = {"open", "resolved", "dismissed"}
GENERATION_REQUEST_STATUSES = {"queued", "processing", "completed", "failed", "canceled"}


class AssetStatusRequest(BaseModel):
    status: str
    reason: str | None = None


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
