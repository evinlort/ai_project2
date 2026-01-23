import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from intentbid.app.core.observability import MetricsCollector, request_middleware
from intentbid.app.api.routes_buyer_dashboard import router as buyer_dashboard_router
from intentbid.app.api.routes_buyers import router as buyers_router
from intentbid.app.api.routes_admin import router as admin_router
from intentbid.app.api.routes_dashboard import router as dashboard_router
from intentbid.app.api.routes_offers import router as offers_router
from intentbid.app.api.routes_rfo import router as rfo_router
from intentbid.app.api.routes_ru import router as ru_router
from intentbid.app.api.routes_vendors import router as vendors_router

app = FastAPI(title="IntentBid API")
logger = logging.getLogger("intentbid")
metrics = MetricsCollector()
app.middleware("http")(request_middleware(metrics, logger))

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.include_router(buyers_router)
app.include_router(vendors_router)
app.include_router(rfo_router)
app.include_router(offers_router)
app.include_router(admin_router)
app.include_router(buyer_dashboard_router)
app.include_router(dashboard_router)
app.include_router(ru_router)


@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return templates.TemplateResponse(request, "landing.html", {"request": request})


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics_endpoint():
    return metrics.render()


@app.get("/ready")
def readiness_check():
    return {"status": "ready"}
