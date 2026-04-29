from fastapi import FastAPI

from vaultix_api.routers import assets, meta
from vaultix_api.settings import get_settings

app = FastAPI(title="Vaultix API")
app.include_router(meta.router)
app.include_router(assets.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.version,
        "env": settings.env,
    }
