from fastapi.testclient import TestClient

from vaultix_api.main import app


def test_healthz_returns_status_version_and_env():
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
        "env": "test",
    }
