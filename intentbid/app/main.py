from fastapi import FastAPI

from intentbid.app.api.routes_rfo import router as rfo_router
from intentbid.app.api.routes_vendors import router as vendors_router

app = FastAPI(title="IntentBid API")
app.include_router(vendors_router)
app.include_router(rfo_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
