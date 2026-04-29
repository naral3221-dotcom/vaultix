from fastapi import FastAPI

from vaultix_api.settings import get_settings

app = FastAPI(title="Vaultix API")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.version,
        "env": settings.env,
    }
