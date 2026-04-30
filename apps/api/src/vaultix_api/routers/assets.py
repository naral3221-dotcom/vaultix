from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from vaultix_api.deps import get_db
from vaultix_api.models.core import Asset, AssetReport, Category
from vaultix_api.routers.serializers import asset_to_card, asset_to_detail

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])

REPORT_REASONS = {"copyright", "inappropriate", "broken_file", "other"}


class AssetReportRequest(BaseModel):
    reason: str
    message: str | None = None


@router.get("")
def list_assets(
    type: str = "image",
    category: str | None = None,
    sort: str = "recent",
    limit: int = 24,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    query = db.query(Asset).filter(Asset.status == "published", Asset.asset_type == type)
    if category:
        query = query.join(Category, Category.id == Asset.category_id).filter(Category.slug == category)

    if sort == "popular":
        query = query.order_by(Asset.download_count.desc(), Asset.id.desc())
    else:
        query = query.order_by(Asset.id.desc())

    bounded_limit = min(max(limit, 1), 100)
    assets = query.limit(bounded_limit).all()
    return {
        "data": [asset_to_card(asset, db) for asset in assets],
        "meta": {
            "next_cursor": None,
            "limit": bounded_limit,
            "total_estimate": len(assets),
        },
    }


@router.get("/{slug_or_id}")
def get_asset(slug_or_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    query = db.query(Asset).filter(Asset.status == "published")
    if slug_or_id.isdigit():
        query = query.filter(or_(Asset.id == int(slug_or_id), Asset.slug == slug_or_id))
    else:
        query = query.filter(Asset.slug == slug_or_id)
    asset = query.first()
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return {"data": asset_to_detail(asset, db)}


@router.post("/{asset_id}/report", status_code=201)
def report_asset(asset_id: int, payload: AssetReportRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    if payload.reason not in REPORT_REASONS:
        raise HTTPException(status_code=400, detail="invalid_report_reason")
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset_not_found")

    report = AssetReport(
        id=int(db.query(func.coalesce(func.max(AssetReport.id), 0)).scalar() or 0) + 1,
        asset_id=asset.id,
        reason=payload.reason,
        message=payload.message,
        status="open",
    )
    db.add(report)
    db.commit()
    return {
        "data": {
            "id": report.id,
            "asset_id": report.asset_id,
            "reason": report.reason,
            "message": report.message,
            "status": report.status,
        }
    }
