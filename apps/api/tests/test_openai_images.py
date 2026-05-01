import base64

import httpx

from vaultix_api.services.openai_images import generate_openai_image


def test_generate_openai_image_calls_images_api_and_returns_b64_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.com/v1/images/generations"
        assert request.headers["authorization"] == "Bearer test-key"
        assert request.headers["content-type"] == "application/json"
        body = request.read().decode("utf-8")
        assert '"model":"gpt-image-1.5"' in body
        assert '"prompt":"업무용 히어로 이미지"' in body
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "b64_json": base64.b64encode(b"fake-image-bytes").decode("ascii"),
                        "revised_prompt": "업무용 히어로 이미지, 깔끔한 구성",
                    }
                ]
            },
        )

    result = generate_openai_image(
        api_key="test-key",
        model="gpt-image-1.5",
        prompt="업무용 히어로 이미지",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert result.image_bytes == b"fake-image-bytes"
    assert result.revised_prompt == "업무용 히어로 이미지, 깔끔한 구성"
    assert result.model == "gpt-image-1.5"
