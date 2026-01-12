import logging

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from intentbid.app.core.observability import MetricsCollector, request_middleware
from intentbid.app.api.routes_buyers import router as buyers_router
from intentbid.app.api.routes_dashboard import router as dashboard_router
from intentbid.app.api.routes_offers import router as offers_router
from intentbid.app.api.routes_rfo import router as rfo_router
from intentbid.app.api.routes_ru import router as ru_router
from intentbid.app.api.routes_vendors import router as vendors_router

app = FastAPI(title="IntentBid API")
logger = logging.getLogger("intentbid")
metrics = MetricsCollector()
app.middleware("http")(request_middleware(metrics, logger))

app.include_router(buyers_router)
app.include_router(vendors_router)
app.include_router(rfo_router)
app.include_router(offers_router)
app.include_router(dashboard_router)
app.include_router(ru_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics_endpoint():
    return metrics.render()


@app.get("/ready")
def readiness_check():
    return {"status": "ready"}
