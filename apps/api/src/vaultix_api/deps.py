from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from vaultix_api.db.session import get_sessionmaker


def get_db() -> Iterator[Session]:
    maker = get_sessionmaker()
    with maker() as session:
        yield session


@dataclass(frozen=True)
class CurrentUser:
    id: int
    email_lower: str
    email_verified_at: datetime | None


def problem(status_code: int, code: str, title: str, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "type": f"https://vaultix.example.com/errors/{code}",
            "title": title,
            "status": status_code,
            "detail": detail,
            "code": code,
        },
    )


def require_verified_user() -> CurrentUser:
    raise problem(401, "unauthenticated", "Unauthenticated", "로그인이 필요합니다.")
