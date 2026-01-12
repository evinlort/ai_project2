import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response


class MetricsCollector:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def record(self, method: str, path: str, status_code: int) -> None:
        key = f"{method}:{path}:{status_code}"
        self._counts[key] = self._counts.get(key, 0) + 1

    def render(self) -> str:
        lines = ["# TYPE http_requests_total counter"]
        for key, value in sorted(self._counts.items()):
            method, path, status = key.split(":", 2)
            lines.append(
                'http_requests_total{method="%s",path="%s",status="%s"} %d'
                % (method, path, status, value)
            )
        return "\n".join(lines) + "\n"


def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-Id") or uuid.uuid4().hex


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted = {}
    for key, value in headers.items():
        if key.lower() in {"authorization", "x-api-key", "x-buyer-api-key"}:
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted


def request_logger(logger: logging.Logger, request: Request, response: Response, duration: float) -> None:
    payload = {
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": round(duration * 1000, 2),
        "correlation_id": response.headers.get("X-Correlation-Id"),
        "headers": redact_headers(dict(request.headers)),
    }
    logger.info(json.dumps(payload))


def request_middleware(
    metrics: MetricsCollector,
    logger: logging.Logger,
) -> Callable:
    async def middleware(request: Request, call_next):
        correlation_id = get_correlation_id(request)
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Correlation-Id"] = correlation_id
        metrics.record(request.method, request.url.path, response.status_code)
        request_logger(logger, request, response, duration)
        return response

    return middleware
