import json

import httpx

from vaultix_api.services.email_delivery import ResendEmailClient, build_reset_url, build_verify_url


def test_build_verify_and_reset_urls_encode_tokens():
    assert (
        build_verify_url("https://vaultix.example.com", "abc 123")
        == "https://vaultix.example.com/auth/verify?token=abc+123"
    )
    assert (
        build_reset_url("https://vaultix.example.com/", "reset/token")
        == "https://vaultix.example.com/auth/reset-password?token=reset%2Ftoken"
    )


def test_resend_client_posts_transactional_email_payload():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "email_123"})

    client = ResendEmailClient(
        api_key="resend-key",
        from_email="Vaultix <no-reply@vaultix.example.com>",
        transport=httpx.MockTransport(handler),
    )

    result = client.send(
        to="user@example.com",
        subject="Vaultix 이메일 인증",
        html="<p>인증</p>",
    )

    assert result == {"id": "email_123"}
    assert requests[0].url == "https://api.resend.com/emails"
    assert requests[0].headers["authorization"] == "Bearer resend-key"
    payload = json.loads(requests[0].content)
    assert payload == {
        "from": "Vaultix <no-reply@vaultix.example.com>",
        "to": ["user@example.com"],
        "subject": "Vaultix 이메일 인증",
        "html": "<p>인증</p>",
    }
