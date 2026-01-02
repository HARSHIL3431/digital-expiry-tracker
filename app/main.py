from fastapi import FastAPI
from .database import engine
from . import models
from .routes import products

app = FastAPI(title="Digital Expiry Tracker")

models.Base.metadata.create_all(bind=engine)

app.include_router(products.router)

@app.get("/api/test")
def test():
    return {"status": "API working"}
