from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from vaultix_api.db.session import get_sessionmaker
from vaultix_api.models.core import Session as UserSession, User


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


def require_user(
    db: Session = Depends(get_db),
    secure_session_token: str | None = Cookie(default=None, alias="__Secure-vaultix.session"),
    session_token: str | None = Cookie(default=None, alias="vaultix.session"),
) -> CurrentUser:
    token = secure_session_token or session_token
    if not token:
        raise problem(401, "unauthenticated", "Unauthenticated", "로그인이 필요합니다.")

    record = (
        db.query(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .filter(UserSession.session_token == token, User.status == "active")
        .first()
    )
    if record is None:
        raise problem(401, "unauthenticated", "Unauthenticated", "로그인이 필요합니다.")

    session_record, user = record
    expires = session_record.expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        raise problem(401, "unauthenticated", "Unauthenticated", "로그인이 필요합니다.")

    return CurrentUser(
        id=user.id,
        email_lower=user.email_lower,
        email_verified_at=user.email_verified_at,
    )


def require_verified_user(user: CurrentUser = Depends(require_user)) -> CurrentUser:
    if user.email_verified_at is None:
        raise problem(
            403,
            "email_not_verified",
            "Email not verified",
            "이메일 인증 후 다운로드할 수 있습니다.",
        )
    return user
