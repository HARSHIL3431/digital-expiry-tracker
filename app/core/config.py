import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "college_project_secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@det.com")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expiry_tracker.db")

TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH",
    "tesseract"
)
