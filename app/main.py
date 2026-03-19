from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.utils.database import init_db, SessionLocal
from app import models  # ensures models are registered
from app.api.v1 import products, scan
from app.api.v1 import auth
from app.api.v1 import logs


# ------------------ LIFESPAN ------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Digital Expiry Tracker...")

    # Initialize database
    init_db()
    print("Database initialized successfully.")

    # --- DEMO TEST USER SETUP ---
    from app.models import User, Subscription
    from app.core.security import hash_password
    from datetime import date, timedelta
    db = SessionLocal()
    try:
        test_email = "test@example.com"
        test_password = "123456"
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            user = User(
                name="Test User",
                email=test_email,
                password_hash=hash_password(test_password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            # Add subscription
            sub = Subscription(
                user_id=user.id,
                plan_type="free",
                expiry_date=date.today() + timedelta(days=365)
            )
            db.add(sub)
            db.commit()
            print("Test user created: test@example.com / 123456")
        else:
            print("Test user already exists.")
    finally:
        db.close()

    yield

    print("Shutting down Digital Expiry Tracker...")


# ------------------ FASTAPI APP ------------------

app = FastAPI(
    title="Digital Expiry Tracker",
    description="AI-powered expiry detection and tracking system",
    version="1.1.0",
    lifespan=lifespan
)


# ------------------ FRONTEND STATIC FILES ------------------

# Serve CSS and JS
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")


# ------------------ FRONTEND PAGES ------------------

# Landing Page
@app.get("/", tags=["Frontend"])
def landing_page():
    return FileResponse("frontend/pages/v1.html")



# Login Page
@app.get("/app/login", tags=["Frontend"])
def login_page():
    return FileResponse("frontend/pages/login.html")

# Register Page
@app.get("/app/register", tags=["Frontend"])
def register_page():
    return FileResponse("frontend/pages/register.html")

# Dashboard Page (protected)
@app.get("/app/dashboard", tags=["Frontend"])
def dashboard_page():
    return FileResponse("frontend/pages/dashboard.html")

# Fallback routes for legacy links
@app.get("/login.html", tags=["Frontend"])
def login_html_fallback():
    return FileResponse("frontend/pages/login.html")

@app.get("/register.html", tags=["Frontend"])
def register_html_fallback():
    return FileResponse("frontend/pages/register.html")


# ------------------ API ROUTERS ------------------

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

app.include_router(
    logs.router,
    prefix="/api/v1/logs",
    tags=["Logs"]
)


# ------------------ TEST ROUTES ------------------

@app.get("/api/test", tags=["Test"])
def test():
    return {
        "status": "API working",
        "database": "Connected",
        "modules": ["Products", "OCR"]
    }