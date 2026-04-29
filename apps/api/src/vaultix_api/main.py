from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse

from vaultix_api.routers import assets, auth, downloads, meta
from vaultix_api.settings import get_settings

app = FastAPI(title="Vaultix API")
app.include_router(meta.router)
app.include_router(assets.router)
app.include_router(downloads.router)
app.include_router(auth.router)


@app.exception_handler(HTTPException)
async def vaultix_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail, headers=exc.headers)
    return await http_exception_handler(request, exc)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.version,
        "env": settings.env,
    }
