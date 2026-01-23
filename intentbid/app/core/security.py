from fastapi import Request
from fastapi.responses import JSONResponse

from intentbid.app.core.config import settings


def https_redirect_middleware():
    async def middleware(request: Request, call_next):
        if settings.require_https:
            proto = request.headers.get("X-Forwarded-Proto") or request.url.scheme
            if proto != "https":
                return JSONResponse(status_code=400, content={"detail": "HTTPS required"})
        return await call_next(request)

    return middleware
