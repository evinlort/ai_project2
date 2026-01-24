import hashlib
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from intentbid.app.core.config import settings


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def https_redirect_middleware():
    async def middleware(request: Request, call_next):
        if settings.require_https:
            proto = request.headers.get("X-Forwarded-Proto") or request.url.scheme
            if proto != "https":
                return JSONResponse(status_code=400, content={"detail": "HTTPS required"})
        return await call_next(request)

    return middleware
