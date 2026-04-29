from sqlalchemy.orm import Session

from vaultix_api.models.core import Asset, AssetTag, Category, Tag


def category_to_dict(category: Category) -> dict[str, object]:
    return {
        "id": category.id,
        "slug": category.slug,
        "name_ko": category.name_ko,
        "name": category.name_ko,
        "children": [],
    }


def tag_to_dict(tag: Tag) -> dict[str, object]:
    return {
        "id": tag.id,
        "slug": tag.slug,
        "name_ko": tag.name_ko,
        "name": tag.name_ko,
    }


def asset_to_card(asset: Asset, db: Session) -> dict[str, object]:
    category = db.get(Category, asset.category_id) if asset.category_id else None
    tags = db.query(Tag).join(AssetTag, AssetTag.tag_id == Tag.id).filter(AssetTag.asset_id == asset.id).all()
    return {
        "id": asset.id,
        "slug": asset.slug,
        "asset_type": asset.asset_type,
        "title": asset.title_ko,
        "alt_text": asset.alt_text_ko,
        "thumbnail_url": asset.thumbnail_path,
        "preview_url": asset.preview_path,
        "category": (
            {"id": category.id, "slug": category.slug, "name": category.name_ko} if category else None
        ),
        "tags": [{"slug": tag.slug, "name": tag.name_ko} for tag in tags],
        "ai": {"model": None, "generator": None},
        "stats": {"downloads": asset.download_count, "favorites": 0},
        "published_at": None,
    }


def asset_to_detail(asset: Asset, db: Session) -> dict[str, object]:
    data = asset_to_card(asset, db)
    data.update(
        {
            "description": asset.description_ko,
            "files": [],
            "license_summary_url": "/license#summary",
            "related_asset_ids": [],
        }
    )
    return data
