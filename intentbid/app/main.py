from fastapi import FastAPI

from intentbid.app.api.routes_vendors import router as vendors_router

app = FastAPI(title="IntentBid API")
app.include_router(vendors_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
