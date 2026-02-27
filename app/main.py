from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.utils.database import init_db
from app import models  # Important: ensures models are registered
from app.api.v1 import products, scan
from app.api.v1 import auth

# ✅ Modern startup lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Digital Expiry Tracker...")
    
    # Initialize database (creates tables if not exist)
    init_db()
    
    print("✅ Database initialized successfully.")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Digital Expiry Tracker...")


app = FastAPI(
    title="Digital Expiry Tracker",
    description="AI-powered expiry detection and tracking system",
    version="1.1.0",
    lifespan=lifespan
)


# ------------------ ROUTERS ------------------

app.include_router(
    products.router,
    prefix="/api/v1/products",
    tags=["Products"]
)

app.include_router(
    scan.router,
    prefix="/api/v1/scan",
    tags=["OCR"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)
# ------------------ ROOT ROUTES ------------------

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Digital Expiry Tracker API is running 🚀",
        "docs": "/docs",
        "version": "v1.1.0"
    }


@app.get("/api/test", tags=["Test"])
def test():
    return {
        "status": "API working",
        "database": "Connected",
        "modules": ["Products", "OCR"]
    }