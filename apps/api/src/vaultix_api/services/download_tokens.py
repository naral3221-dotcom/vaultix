from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import secrets
from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError

from vaultix_api.settings import get_settings


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


class TokenBackend(Protocol):
    def setex(self, key: str, seconds: int, value: str) -> None: ...

    def pop(self, key: str) -> str | None: ...

    def incr_with_ttl(self, key: str, seconds: int) -> tuple[int, int]: ...

    def clear(self) -> None: ...


class InMemoryTokenBackend:
    def __init__(self) -> None:
        self._values: dict[str, tuple[str, datetime]] = {}

    def setex(self, key: str, seconds: int, value: str) -> None:
        self._values[key] = (value, datetime.now(UTC) + timedelta(seconds=seconds))

    def pop(self, key: str) -> str | None:
        item = self._values.pop(key, None)
        if item is None:
            return None
        value, expires_at = item
        if expires_at <= datetime.now(UTC):
            return None
        return value

    def incr_with_ttl(self, key: str, seconds: int) -> tuple[int, int]:
        now = datetime.now(UTC)
        item = self._values.get(key)
        if item is None or item[1] <= now:
            expires_at = now + timedelta(seconds=seconds)
            count = 1
        else:
            expires_at = item[1]
            count = int(item[0]) + 1
        self._values[key] = (str(count), expires_at)
        return count, max(int((expires_at - now).total_seconds()), 1)

    def clear(self) -> None:
        self._values.clear()


class RedisTokenBackend:
    def __init__(self, redis_url: str) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)

    def setex(self, key: str, seconds: int, value: str) -> None:
        self._redis.setex(key, seconds, value)

    def pop(self, key: str) -> str | None:
        pipeline = self._redis.pipeline()
        pipeline.get(key)
        pipeline.delete(key)
        value, _deleted = pipeline.execute()
        return value

    def incr_with_ttl(self, key: str, seconds: int) -> tuple[int, int]:
        pipeline = self._redis.pipeline()
        pipeline.incr(key)
        pipeline.ttl(key)
        count, ttl = pipeline.execute()
        if ttl == -1:
            self._redis.expire(key, seconds)
            ttl = seconds
        return int(count), int(ttl)

    def clear(self) -> None:
        for key in self._redis.scan_iter("vaultix:*"):
            self._redis.delete(key)


def create_default_backend() -> TokenBackend:
    redis_url = get_settings().redis_url
    try:
        backend = RedisTokenBackend(redis_url)
        backend.incr_with_ttl("vaultix:healthcheck", 1)
        return backend
    except RedisError:
        return InMemoryTokenBackend()


class DownloadTokenStore:
    def __init__(self, backend: TokenBackend) -> None:
        self._backend = backend

    def issue(self, *, asset_id: int, user_id: int, file_path: str, ttl_seconds: int) -> str:
        nonce = secrets.token_urlsafe(32)
        payload = {
            "asset_id": asset_id,
            "user_id": user_id,
            "file_path": file_path,
            "expires_at": (datetime.now(UTC) + timedelta(seconds=ttl_seconds)).isoformat(),
        }
        self._backend.setex(f"vaultix:download:{nonce}", ttl_seconds, json.dumps(payload))
        return nonce

    def consume(self, nonce: str) -> DownloadToken | None:
        raw = self._backend.pop(f"vaultix:download:{nonce}")
        if raw is None:
            return None
        payload = json.loads(raw)
        expires_at = datetime.fromisoformat(payload["expires_at"])
        if expires_at <= datetime.now(UTC):
            return None
        return DownloadToken(
            asset_id=int(payload["asset_id"]),
            user_id=int(payload["user_id"]),
            file_path=str(payload["file_path"]),
            expires_at=expires_at,
        )

    def clear(self) -> None:
        self._backend.clear()


class HourlyRateLimiter:
    def __init__(self, backend: TokenBackend) -> None:
        self._backend = backend

    def hit(self, user_id: int, *, limit: int, window_seconds: int) -> RateLimitResult:
        count, ttl = self._backend.incr_with_ttl(f"vaultix:download-rate:{user_id}", window_seconds)
        reset_at = datetime.now(UTC) + timedelta(seconds=ttl)
        return RateLimitResult(count <= limit, limit, max(limit - count, 0), reset_at)

    def clear(self) -> None:
        self._backend.clear()


_default_backend = create_default_backend()
download_token_store = DownloadTokenStore(_default_backend)
download_rate_limiter = HourlyRateLimiter(_default_backend)
