from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.utils.database import init_db, SessionLocal
from app import models  # noqa: F401  # ensures models are registered
from app.core.config import DEMO_USER_PASSWORD, ENABLE_DEMO_USER, SECRET_KEY, SESSION_COOKIE_SECURE
from app.api.v1 import products, scan
from app.api.v1 import auth
from app.api.v1 import logs
from app.api.v1 import analytics
from app.api.v1 import admin
from app.services.expiry_alert_service import start_expiry_alert_scheduler, stop_expiry_alert_scheduler


# ------------------ OPTIONAL DEMO USER ------------------

def ensure_demo_user(db):
    if not ENABLE_DEMO_USER:
        return False
    if not DEMO_USER_PASSWORD:
        print("Demo user skipped: DEMO_USER_PASSWORD is not configured.")
        return False

    from app.core.security import hash_password
    from app.models import Subscription, User
    from datetime import date, timedelta

    test_email = "test@example.com"
    user = db.query(User).filter(User.email == test_email).first()
    if user:
        return False

    user = User(
        name="Test User",
        email=test_email,
        password_hash=hash_password(DEMO_USER_PASSWORD),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    subscription = Subscription(
        user_id=user.id,
        plan_type="free",
        expiry_date=date.today() + timedelta(days=365),
    )
    db.add(subscription)
    db.commit()

    print("Demo user ensured: test@example.com")
    return True


# ------------------ LIFESPAN ------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Digital Expiry Tracker...")

    # Initialize database
    init_db()
    print("Database initialized successfully.")

    # Start background expiry alert scheduler once per app process.
    start_expiry_alert_scheduler()
    print("Expiry alert scheduler initialized.")

    # --- OPTIONAL DEMO USER SETUP ---
    db = SessionLocal()
    try:
        ensure_demo_user(db)
    finally:
        db.close()

    yield

    stop_expiry_alert_scheduler()

    print("Shutting down Digital Expiry Tracker...")


# ------------------ FASTAPI APP ------------------

app = FastAPI(
    title="Digital Expiry Tracker",
    description="AI-powered expiry detection and tracking system",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=SESSION_COOKIE_SECURE,
    max_age=300,
)


# ------------------ FRONTEND STATIC FILES ------------------

# Serve CSS and JS
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")


# ------------------ FRONTEND PAGES ------------------

# Landing Page
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "digital-expiry-tracker"}


@app.get("/api/health", tags=["Health"])
def api_health_check():
    return {"status": "ok", "service": "digital-expiry-tracker"}


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

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"]
)


# ------------------ TEST ROUTES ------------------

@app.get("/api/test", tags=["Test"])
def test():
    return {
        "status": "API working",
        "database": "Connected",
        "modules": ["Products", "OCR"]
    }