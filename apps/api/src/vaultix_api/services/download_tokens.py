from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import secrets


@dataclass(frozen=True)
class DownloadToken:
    asset_id: int
    user_id: int
    file_path: str
    expires_at: datetime


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime


class InMemoryDownloadTokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, DownloadToken] = {}

    def issue(self, *, asset_id: int, user_id: int, file_path: str, ttl_seconds: int) -> str:
        nonce = secrets.token_urlsafe(32)
        self._tokens[nonce] = DownloadToken(
            asset_id=asset_id,
            user_id=user_id,
            file_path=file_path,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
        return nonce

    def consume(self, nonce: str) -> DownloadToken | None:
        token = self._tokens.pop(nonce, None)
        if token is None:
            return None
        if token.expires_at <= datetime.now(UTC):
            return None
        return token

    def clear(self) -> None:
        self._tokens.clear()


download_token_store = InMemoryDownloadTokenStore()


class InMemoryHourlyRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[int, tuple[int, datetime]] = {}

    def hit(self, user_id: int, *, limit: int, window_seconds: int) -> RateLimitResult:
        now = datetime.now(UTC)
        count, reset_at = self._buckets.get(
            user_id,
            (0, now + timedelta(seconds=window_seconds)),
        )
        if reset_at <= now:
            count = 0
            reset_at = now + timedelta(seconds=window_seconds)

        if count >= limit:
            return RateLimitResult(False, limit, 0, reset_at)

        count += 1
        self._buckets[user_id] = (count, reset_at)
        return RateLimitResult(True, limit, max(limit - count, 0), reset_at)

    def clear(self) -> None:
        self._buckets.clear()


download_rate_limiter = InMemoryHourlyRateLimiter()
