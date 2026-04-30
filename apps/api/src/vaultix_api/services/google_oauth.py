from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime
import hashlib
import hmac
import json
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx


GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
OAUTH_STATE_MAX_AGE_SECONDS = 10 * 60


def build_google_authorize_url(*, client_id: str, redirect_uri: str, state: str) -> str:
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTHORIZE_URL}?{query}"


def sign_oauth_state(secret: str, next_url: str) -> str:
    payload = {
        "next": next_url,
        "nonce": secrets.token_urlsafe(16),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _signature(secret, encoded_payload)
    return f"{encoded_payload}.{signature}"


def verify_oauth_state(secret: str, state: str) -> str | None:
    try:
        encoded_payload, signature = state.split(".", 1)
        expected_signature = _signature(secret, encoded_payload)
        if not hmac.compare_digest(signature, expected_signature):
            return None
        payload = json.loads(_base64url_decode(encoded_payload))
        issued_at = int(payload.get("iat", 0))
        if int(datetime.now(UTC).timestamp()) - issued_at > OAUTH_STATE_MAX_AGE_SECONDS:
            return None
        next_url = str(payload.get("next") or "/explore")
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    return next_url if _is_safe_next_url(next_url) else "/explore"


def exchange_google_code(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
) -> dict[str, Any]:
    with httpx.Client(timeout=10) as client:
        token_response = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        userinfo_response = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_response.raise_for_status()
        profile = userinfo_response.json()
    email_verified = profile.get("email_verified")
    return {
        "email": profile.get("email"),
        "email_verified": email_verified is True or email_verified == "true",
        "name": profile.get("name"),
    }


def _signature(secret: str, encoded_payload: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(f"{value}{padding}").decode("utf-8")


def _is_safe_next_url(next_url: str) -> bool:
    return (next_url.startswith("/") and not next_url.startswith("//")) or next_url.startswith(
        ("http://", "https://")
    )
