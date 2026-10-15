import os
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_FILE)

_environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
_raw_secret_key = os.getenv("SECRET_KEY")
if not _raw_secret_key:
    if _environment in {"production", "prod"}:
        raise RuntimeError("SECRET_KEY must be configured in production")
    _raw_secret_key = "dev-insecure-secret-change-me"
SECRET_KEY = _raw_secret_key

_raw_demo_user = os.getenv("ENABLE_DEMO_USER")
if _raw_demo_user is None:
    ENABLE_DEMO_USER = _environment not in {"production", "prod"}
else:
    ENABLE_DEMO_USER = _raw_demo_user.strip().lower() in {"1", "true", "yes", "on"}

_raw_secure_cookies = os.getenv("SESSION_COOKIE_SECURE")
if _raw_secure_cookies is None:
    SESSION_COOKIE_SECURE = _environment in {"production", "prod"}
else:
    SESSION_COOKIE_SECURE = _raw_secure_cookies.strip().lower() in {"1", "true", "yes", "on"}
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

# The standalone Windows Tesseract executable.  Optional; discovery below
# supports an explicit TESSERACT_CMD value, PATH lookup, and common Windows
# installation locations.  TESSERACT_PATH is retained for older deployments.
TESSERACT_CMD = (os.getenv("TESSERACT_CMD") or os.getenv("TESSERACT_PATH") or "").strip()
OCR_TIMEOUT_SECONDS = int(os.getenv("OCR_TIMEOUT_SECONDS", "30"))
