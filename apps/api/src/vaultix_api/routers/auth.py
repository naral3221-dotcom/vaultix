from datetime import UTC, datetime, timedelta
from hashlib import sha256
import re
import secrets

import httpx
from fastapi import APIRouter, Cookie, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from vaultix_api.deps import get_db, problem
from vaultix_api.models.core import EmailVerification, PasswordReset, Session as UserSession, User
from vaultix_api.services.email_delivery import (
    build_reset_url,
    build_verify_url,
    reset_email_html,
    send_transactional_email,
    verification_email_html,
)
from vaultix_api.services.email_domains import is_disposable_email
from vaultix_api.services.passwords import hash_password, verify_password
from vaultix_api.services.turnstile import verify_turnstile
from vaultix_api.settings import Settings, get_settings

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


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


@router.post("/signup", status_code=201)
def signup(
    payload: SignupRequest, request: Request, db: Session = Depends(get_db)
) -> dict[str, object]:
    settings = get_settings()
    email = payload.email.strip()
    email_lower = email.lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_lower):
        raise problem(400, "validation_error", "Validation error", "올바른 이메일 주소를 입력해 주세요.")
    if is_disposable_email(email_lower):
        raise problem(
            400,
            "disposable_email_blocked",
            "Disposable email blocked",
            "일회용 이메일 주소로는 가입할 수 없습니다.",
        )
    if len(payload.password) < 8 or not any(char.isdigit() for char in payload.password):
        raise problem(400, "validation_error", "Validation error", "비밀번호는 8자 이상이며 숫자를 포함해야 합니다.")
    if not verify_turnstile(
        settings.turnstile_secret_key,
        payload.turnstile_token,
        request.client.host if request.client else None,
    ):
        raise problem(
            400,
            "turnstile_failed",
            "Turnstile failed",
            "보안 확인을 완료하지 못했습니다.",
        )

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
    _send_email_or_raise(
        to=user.email,
        subject="Vaultix 이메일 인증",
        html=verification_email_html(build_verify_url(settings.public_site_url, verification.token)),
        settings=settings,
    )

    return {
        "data": {
            "user": {
                "id": user.id,
                "email": user.email,
                "email_verified": False,
            }
        }
    }


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    secure_session_token: str | None = Cookie(default=None, alias="__Secure-vaultix.session"),
    session_token: str | None = Cookie(default=None, alias="vaultix.session"),
) -> dict[str, object]:
    token = secure_session_token or session_token
    if token:
        db.query(UserSession).filter(UserSession.session_token == token).delete()
        db.commit()
    response.delete_cookie("vaultix.session", path="/")
    response.delete_cookie("__Secure-vaultix.session", path="/")
    return {"data": {"logged_out": True}}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    settings = get_settings()
    email_lower = payload.email.strip().lower()
    user = db.query(User).filter(User.email_lower == email_lower, User.status == "active").first()
    response: dict[str, object] = {"data": {"sent": True}}
    if user is None:
        return response

    raw_token = secrets.token_urlsafe(48)
    next_reset_id = int(db.query(func.coalesce(func.max(PasswordReset.id), 0)).scalar() or 0) + 1
    reset = PasswordReset(
        id=next_reset_id,
        user_id=user.id,
        token_hash=f"sha256${sha256(raw_token.encode('utf-8')).hexdigest()}",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(reset)
    db.commit()
    _send_email_or_raise(
        to=user.email,
        subject="Vaultix 비밀번호 재설정",
        html=reset_email_html(build_reset_url(settings.public_site_url, raw_token)),
        settings=settings,
    )
    # Until Resend is wired, expose this only outside production for local/Tailnet smoke flows.
    if settings.env != "production":
        response["data"] = {"sent": True, "reset_token": raw_token}
    return response


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    if len(payload.password) < 8 or not any(char.isdigit() for char in payload.password):
        raise problem(400, "validation_error", "Validation error", "비밀번호는 8자 이상이며 숫자를 포함해야 합니다.")

    token_hash = f"sha256${sha256(payload.token.encode('utf-8')).hexdigest()}"
    reset = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.token_hash == token_hash,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > datetime.now(UTC),
        )
        .first()
    )
    if reset is None:
        raise problem(
            410,
            "reset_token_invalid",
            "Reset token invalid",
            "비밀번호 재설정 링크가 만료되었거나 이미 사용되었습니다.",
        )

    user = db.query(User).filter(User.id == reset.user_id, User.status == "active").first()
    if user is None:
        raise problem(
            410,
            "reset_token_invalid",
            "Reset token invalid",
            "비밀번호 재설정 링크가 만료되었거나 이미 사용되었습니다.",
        )

    now = datetime.now(UTC)
    user.password_hash = hash_password(payload.password)
    reset.used_at = now
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    db.commit()
    return {"data": {"reset": True}}


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


def _send_email_or_raise(*, to: str, subject: str, html: str, settings: Settings) -> None:
    try:
        send_transactional_email(
            api_key=settings.resend_api_key,
            from_email=settings.mail_from,
            to=to,
            subject=subject,
            html=html,
        )
    except httpx.HTTPError as exc:
        raise problem(
            502,
            "email_delivery_failed",
            "Email delivery failed",
            "메일 발송에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
