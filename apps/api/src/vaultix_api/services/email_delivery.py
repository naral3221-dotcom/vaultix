from typing import Any
from urllib.parse import quote_plus

import httpx


def build_verify_url(public_site_url: str, token: str) -> str:
    return f"{public_site_url.rstrip('/')}/auth/verify?token={quote_plus(token)}"


def build_reset_url(public_site_url: str, token: str) -> str:
    return f"{public_site_url.rstrip('/')}/auth/reset-password?token={quote_plus(token)}"


def verification_email_html(verify_url: str) -> str:
    return (
        "<p>Vaultix 이메일 인증을 완료해 주세요.</p>"
        f'<p><a href="{verify_url}">이메일 인증하기</a></p>'
        "<p>이 링크는 24시간 동안 유효합니다.</p>"
    )


def reset_email_html(reset_url: str) -> str:
    return (
        "<p>Vaultix 비밀번호 재설정을 요청하셨습니다.</p>"
        f'<p><a href="{reset_url}">비밀번호 재설정하기</a></p>'
        "<p>이 링크는 1시간 동안 유효합니다.</p>"
    )


class ResendEmailClient:
    def __init__(
        self,
        api_key: str,
        from_email: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.from_email = from_email
        self.transport = transport

    def send(self, *, to: str, subject: str, html: str) -> dict[str, Any]:
        with httpx.Client(transport=self.transport, timeout=10) as client:
            response = client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": self.from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            response.raise_for_status()
            return response.json()


def send_transactional_email(
    *,
    api_key: str,
    from_email: str,
    to: str,
    subject: str,
    html: str,
) -> dict[str, Any] | None:
    if not api_key or not from_email:
        return None
    return ResendEmailClient(api_key=api_key, from_email=from_email).send(
        to=to,
        subject=subject,
        html=html,
    )
