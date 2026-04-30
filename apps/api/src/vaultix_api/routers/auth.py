from datetime import UTC, datetime, timedelta
import re
import secrets

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from vaultix_api.deps import get_db, problem
from vaultix_api.models.core import EmailVerification, Session as UserSession, User
from vaultix_api.services.passwords import hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None
    locale: str = "ko"
    turnstile_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    email = payload.email.strip()
    email_lower = email.lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_lower):
        raise problem(400, "validation_error", "Validation error", "올바른 이메일 주소를 입력해 주세요.")
    if len(payload.password) < 8 or not any(char.isdigit() for char in payload.password):
        raise problem(400, "validation_error", "Validation error", "비밀번호는 8자 이상이며 숫자를 포함해야 합니다.")

    existing_user = db.query(User).filter(User.email_lower == email_lower).first()
    if existing_user is not None:
        raise problem(409, "conflict", "Conflict", "이미 가입된 이메일입니다.")

    next_user_id = int(db.query(func.coalesce(func.max(User.id), 0)).scalar() or 0) + 1
    next_token_id = int(db.query(func.coalesce(func.max(EmailVerification.id), 0)).scalar() or 0) + 1
    user = User(
        id=next_user_id,
        email=email,
        email_lower=email_lower,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        locale=payload.locale,
        status="active",
    )
    db.add(user)
    db.flush()

    verification = EmailVerification(
        id=next_token_id,
        user_id=next_user_id,
        token=secrets.token_urlsafe(48)[:64],
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(verification)
    db.commit()

    return {
        "data": {
            "user": {
                "id": user.id,
                "email": user.email,
                "email_verified": False,
            }
        }
    }


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    now = datetime.now(UTC)
    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.token == payload.token,
            EmailVerification.used_at.is_(None),
            EmailVerification.expires_at > now,
        )
        .first()
    )
    if verification is None:
        raise problem(
            410,
            "verification_token_invalid",
            "Verification token invalid",
            "인증 링크가 만료되었거나 이미 사용되었습니다.",
        )

    user = db.query(User).filter(User.id == verification.user_id, User.status == "active").first()
    if user is None:
        raise problem(
            410,
            "verification_token_invalid",
            "Verification token invalid",
            "인증 링크가 만료되었거나 이미 사용되었습니다.",
        )

    user.email_verified_at = now
    verification.used_at = now
    db.commit()

    return {"data": {"verified": True, "user_id": user.id}}


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
    email_lower = payload.email.strip().lower()
    user = db.query(User).filter(User.email_lower == email_lower, User.status == "active").first()
    if user is None or user.password_hash is None or not verify_password(payload.password, user.password_hash):
        raise problem(
            401,
            "unauthenticated",
            "Unauthenticated",
            "이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    next_session_id = int(db.query(func.coalesce(func.max(UserSession.id), 0)).scalar() or 0) + 1
    session_token = secrets.token_urlsafe(48)
    session = UserSession(
        id=next_session_id,
        session_token=session_token,
        user_id=user.id,
        expires=datetime.now(UTC) + timedelta(days=30),
    )
    user.last_login_at = datetime.now(UTC)
    db.add(session)
    db.commit()

    response.set_cookie(
        "vaultix.session",
        session_token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return {
        "data": {
            "user": {
                "id": user.id,
                "email": user.email,
                "email_verified": user.email_verified_at is not None,
            }
        }
    }
