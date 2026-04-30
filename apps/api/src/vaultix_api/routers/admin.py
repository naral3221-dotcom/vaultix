import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from vaultix_api.deps import CurrentUser, get_db, problem, require_admin_user
from vaultix_api.models.core import Asset, AssetReport, AuditLog

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

ASSET_STATUSES = {"inbox", "approved", "published", "rejected", "archived", "taken_down"}


class AssetStatusRequest(BaseModel):
    status: str
    reason: str | None = None


def admin_asset_to_dict(asset: Asset) -> dict[str, object]:
    return {
        "id": asset.id,
        "slug": asset.slug,
        "title": asset.title_ko,
        "status": asset.status,
        "asset_type": asset.asset_type,
        "download_count": asset.download_count,
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
    if status not in {"open", "resolved", "dismissed"}:
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
