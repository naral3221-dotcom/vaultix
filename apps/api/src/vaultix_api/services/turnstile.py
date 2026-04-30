import httpx


class TurnstileVerifier:
    def __init__(
        self,
        secret_key: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.secret_key = secret_key
        self.transport = transport

    def verify(self, token: str, remote_ip: str | None = None) -> bool:
        if not self.secret_key:
            return token == "dev-token"
        if not token:
            return False

        data = {"secret": self.secret_key, "response": token}
        if remote_ip:
            data["remoteip"] = remote_ip

        with httpx.Client(transport=self.transport, timeout=10) as client:
            response = client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data=data,
            )
            response.raise_for_status()
            return bool(response.json().get("success"))


def verify_turnstile(secret_key: str, token: str, remote_ip: str | None = None) -> bool:
    return TurnstileVerifier(secret_key=secret_key).verify(token=token, remote_ip=remote_ip)
