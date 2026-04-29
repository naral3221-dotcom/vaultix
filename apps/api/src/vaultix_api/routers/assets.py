from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from vaultix_api.deps import get_db
from vaultix_api.models.core import Asset, Category
from vaultix_api.routers.serializers import asset_to_card, asset_to_detail

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


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

