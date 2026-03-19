from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ADMIN_EMAIL,
)

# ==============================
# 🔐 JWT CONFIGURATION
# ==============================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ==============================
# 🔑 PASSWORD UTILITIES
# ==============================

def hash_password(password: str) -> str:
    # bcrypt supports max 72 bytes
    password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


# ==============================
# 🎟 TOKEN UTILITIES
# ==============================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ==============================
# 👑 ADMIN CHECK HELPER
# ==============================

def is_admin(email: str) -> bool:
    return email.lower() == ADMIN_EMAIL.lower()