from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta

from app.utils.database import get_db
from app.models import User, Subscription
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    is_admin
)
from app.core.dependencies import get_current_user


router = APIRouter()


# ==============================
# 📦 REQUEST SCHEMAS
# ==============================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ==============================
# 📝 REGISTER
# ==============================

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 👑 Assign plan
    if is_admin(data.email):
        plan = "pro"
    else:
        plan = "free"

    subscription = Subscription(
        user_id=new_user.id,
        plan_type=plan,
        expiry_date=date.today() + timedelta(days=365)
    )

    db.add(subscription)
    db.commit()

    return {
        "message": "User registered successfully",
        "assigned_plan": plan
    }


# ==============================
# 🔐 LOGIN
# ==============================

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ==============================
# 💳 FAKE UPGRADE (Demo Mode)
# ==============================

@router.post("/upgrade")
def upgrade_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if subscription.plan_type == "pro":
        return {"message": "Already on PRO plan"}

    subscription.plan_type = "pro"
    db.commit()

    return {
        "message": "Plan upgraded to PRO (Demo Mode)",
        "note": "This is a simulated upgrade for college project"
    }