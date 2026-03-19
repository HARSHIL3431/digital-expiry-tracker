from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
from app.services.activity_log_service import create_activity_log
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RegisterResponse,
    LoginResponse,
    UpgradeResponse,
    CurrentUserResponse,
)


router = APIRouter()


# ==============================
# 📝 REGISTER
# ==============================

@router.post("/register", response_model=RegisterResponse)
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

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})

    create_activity_log(
        db=db,
        user_id=user.id,
        action="USER_LOGIN",
        description=f"User logged in: {user.email}",
    )
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ==============================
# 💳 FAKE UPGRADE (Demo Mode)
# ==============================

@router.post("/upgrade", response_model=UpgradeResponse)
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


# ==============================
# 🙋 CURRENT USER (TOKEN CHECK)
# ==============================

@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
    }