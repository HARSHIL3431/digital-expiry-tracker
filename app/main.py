from fastapi import FastAPI
from app.database import engine
from app import models
from app.api.v1 import products, scan

app = FastAPI(title="Digital Expiry Tracker")

models.Base.metadata.create_all(bind=engine)

# API v1 routes
app.include_router(products.router, prefix="/api/v1", tags=["Products"])
app.include_router(scan.router, prefix="/api/v1", tags=["OCR"])

@app.get("/api/test")
def test():
    return {"status": "API working"}
