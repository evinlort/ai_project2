from fastapi import FastAPI

from intentbid.app.api.routes_buyers import router as buyers_router
from intentbid.app.api.routes_dashboard import router as dashboard_router
from intentbid.app.api.routes_offers import router as offers_router
from intentbid.app.api.routes_rfo import router as rfo_router
from intentbid.app.api.routes_ru import router as ru_router
from intentbid.app.api.routes_vendors import router as vendors_router

app = FastAPI(title="IntentBid API")
app.include_router(buyers_router)
app.include_router(vendors_router)
app.include_router(rfo_router)
app.include_router(offers_router)
app.include_router(dashboard_router)
app.include_router(ru_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
