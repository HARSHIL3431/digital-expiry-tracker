from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.utils.database import init_db
from app import models
from app.api.v1 import products, scan


# ✅ Recommended modern startup method (instead of @on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Digital Expiry Tracker...")
    init_db()
    yield
    # Shutdown
    print("🛑 Shutting down...")


app = FastAPI(
    title="Digital Expiry Tracker",
    version="1.0.0",
    lifespan=lifespan
)

# 🔹 API v1 routes
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(scan.router, prefix="/api/v1/scan", tags=["OCR"])


# ✅ Root route (fixes your 404 issue)
@app.get("/")
def root():
    return {
        "message": "Digital Expiry Tracker API is running 🚀",
        "docs": "/docs",
        "version": "v1"
    }


# ✅ Test route
@app.get("/api/test")
def test():
    return {"status": "API working"}
