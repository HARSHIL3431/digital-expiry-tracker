from fastapi import FastAPI

app = FastAPI(title="Digital Expiry Tracker API")

@app.get("/")
def root():
    return {"status": "Backend running"}

@app.get("/api/test")
def test_api():
    return {"message": "API working successfully"}
