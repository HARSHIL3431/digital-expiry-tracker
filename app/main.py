from fastapi import FastAPI

from app.utils.database import init_db
from app import models
from app.api.v1 import products, scan

app = FastAPI(title="Digital Expiry Tracker")

# 🔹 Run DB initialization ONCE at startup
@app.on_event("startup")
def on_startup():
    init_db()

# 🔹 API v1 routes
app.include_router(products.router, prefix="/api/v1", tags=["Products"])
app.include_router(scan.router, prefix="/api/v1", tags=["OCR"])

@app.get("/api/test")
def test():
    return {"status": "API working"}
