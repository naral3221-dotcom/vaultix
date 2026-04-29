from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from vaultix_api.deps import get_db
from vaultix_api.models.core import Category, Tag
from vaultix_api.routers.serializers import category_to_dict, tag_to_dict

router = APIRouter(prefix="/api/v1/meta", tags=["meta"])


@router.get("/categories")
def list_categories(asset_type: str = "image", db: Session = Depends(get_db)) -> dict[str, object]:
    del asset_type
    categories = (
        db.query(Category)
        .filter(Category.is_active.is_(True))
        .order_by(Category.sort_order.asc(), Category.id.asc())
        .all()
    )
    return {"data": [category_to_dict(category) for category in categories]}


@router.get("/tags")
def list_tags(q: str = "", limit: int = 10, db: Session = Depends(get_db)) -> dict[str, object]:
    query = db.query(Tag)
    if q:
        query = query.filter(Tag.name_ko.contains(q) | Tag.slug.contains(q))
    tags = query.order_by(Tag.use_count.desc(), Tag.id.asc()).limit(min(limit, 50)).all()
    return {"data": [tag_to_dict(tag) for tag in tags]}

