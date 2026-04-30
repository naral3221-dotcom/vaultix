from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from vaultix_api.deps import CurrentUser, get_db, problem, require_verified_user
from vaultix_api.models.core import Asset
from vaultix_api.services.download_tokens import download_rate_limiter, download_token_store

router = APIRouter(tags=["downloads"])

DOWNLOAD_TTL_SECONDS = 300
HOURLY_DOWNLOAD_LIMIT = 30
DOWNLOAD_RATE_WINDOW_SECONDS = 3600


def to_internal_accel_path(file_path: str) -> str:
    if file_path.startswith("/cdn/"):
        return file_path.replace("/cdn/", "/internal-assets/", 1)
    return file_path


@router.post("/api/v1/downloads/{asset_id}", status_code=201)
def create_download_intent(
    asset_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_verified_user),
) -> dict[str, object]:
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.status == "published",
            Asset.file_path.is_not(None),
        )
        .first()
    )
    if asset is None or asset.file_path is None:
        raise problem(404, "not_found", "Not found", "다운로드할 자산을 찾을 수 없습니다.")

    rate = download_rate_limiter.hit(
        user.id,
        limit=HOURLY_DOWNLOAD_LIMIT,
        window_seconds=DOWNLOAD_RATE_WINDOW_SECONDS,
    )
    if not rate.allowed:
        retry_after = max(int((rate.reset_at - datetime.now(UTC)).total_seconds()), 1)
        exc = problem(
            429,
            "rate_limit_exceeded",
            "Rate limit exceeded",
            "시간당 30회 다운로드 한도를 초과했습니다.",
        )
        exc.headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(rate.limit),
            "X-RateLimit-Remaining": str(rate.remaining),
            "X-RateLimit-Reset": str(int(rate.reset_at.timestamp())),
        }
        raise exc

    nonce = download_token_store.issue(
        asset_id=asset.id,
        user_id=user.id,
        file_path=asset.file_path,
        ttl_seconds=DOWNLOAD_TTL_SECONDS,
    )
    return {
        "data": {
            "download_url": f"/dl/{asset.id}/{nonce}",
            "expires_in_seconds": DOWNLOAD_TTL_SECONDS,
        }
    }


@router.get("/dl/{asset_id}/{nonce}", status_code=204)
def download_asset(asset_id: int, nonce: str, db: Session = Depends(get_db)) -> Response:
    token = download_token_store.consume(nonce)
    if token is None or token.asset_id != asset_id:
        raise problem(
            410,
            "download_link_invalid",
            "Download link invalid",
            "다운로드 링크가 만료되었거나 이미 사용되었습니다.",
        )

    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.status == "published").first()
    if asset is None:
        raise problem(404, "not_found", "Not found", "다운로드할 자산을 찾을 수 없습니다.")

    asset.download_count += 1
    db.commit()
    return Response(status_code=204, headers={"X-Accel-Redirect": to_internal_accel_path(token.file_path)})
