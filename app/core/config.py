import os
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_FILE)

SECRET_KEY = os.getenv("SECRET_KEY", "college_project_secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@det.com")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expiry_tracker.db")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/api/v1/auth/google/callback"
)

EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EXPIRY_ALERT_WINDOW_DAYS = int(os.getenv("EXPIRY_ALERT_WINDOW_DAYS", "2"))
EXPIRY_ALERT_INTERVAL_HOURS = int(os.getenv("EXPIRY_ALERT_INTERVAL_HOURS", "24"))
ENABLE_EXPIRY_ALERT_SCHEDULER = os.getenv("ENABLE_EXPIRY_ALERT_SCHEDULER", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH",
    "tesseract"
)
