import httpx

from vaultix_api.services.turnstile import TurnstileVerifier


def test_turnstile_allows_dev_token_without_secret():
    verifier = TurnstileVerifier(secret_key="")

    assert verifier.verify("dev-token", remote_ip="127.0.0.1") is True


def test_turnstile_posts_secret_and_token_when_secret_is_configured():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"success": True})

    verifier = TurnstileVerifier(secret_key="secret", transport=httpx.MockTransport(handler))

    assert verifier.verify("captcha-token", remote_ip="203.0.113.10") is True
    assert requests[0].url == "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    body = requests[0].content.decode()
    assert "secret=secret" in body
    assert "response=captcha-token" in body
    assert "remoteip=203.0.113.10" in body


def test_turnstile_rejects_failed_verification():
    verifier = TurnstileVerifier(
        secret_key="secret",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={"success": False})),
    )

    assert verifier.verify("bad-token", remote_ip=None) is False
