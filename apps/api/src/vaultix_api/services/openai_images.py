from base64 import b64decode
from dataclasses import dataclass

import httpx


OPENAI_IMAGE_GENERATION_URL = "https://api.openai.com/v1/images/generations"


@dataclass(frozen=True)
class GeneratedImage:
    image_bytes: bytes
    model: str
    revised_prompt: str | None


def generate_openai_image(
    *,
    api_key: str,
    model: str,
    prompt: str,
    client: httpx.Client | None = None,
) -> GeneratedImage:
    owns_client = client is None
    active_client = client or httpx.Client(timeout=120)
    try:
        response = active_client.post(
            OPENAI_IMAGE_GENERATION_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "prompt": prompt,
                "size": "1024x1024",
            },
        )
        response.raise_for_status()
        payload = response.json()
    finally:
        if owns_client:
            active_client.close()
    image = payload["data"][0]
    return GeneratedImage(
        image_bytes=b64decode(image["b64_json"]),
        model=model,
        revised_prompt=image.get("revised_prompt"),
    )
