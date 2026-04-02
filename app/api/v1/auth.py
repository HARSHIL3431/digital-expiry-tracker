import secrets
from urllib.parse import quote, urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.base_client.errors import OAuthError
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.utils.database import get_db
from app.models import User, Subscription
from app.core.config import GOOGLE_REDIRECT_URI
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    is_admin
)
from app.core.oauth import get_google_oauth_client
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
# 🔐 GOOGLE OAUTH LOGIN
# ==============================

@router.get("/google/login")
async def google_login(request: Request):
    google = get_google_oauth_client()
    if google is None:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
        )

    # Use configured redirect URI as source of truth
    redirect_uri = GOOGLE_REDIRECT_URI or str(request.url_for("google_callback"))
    
    # If configured, check for localhost/127.0.0.1 mismatch and canonicalize
    if GOOGLE_REDIRECT_URI:
        configured = urlparse(GOOGLE_REDIRECT_URI)
        request_host = request.url.hostname or ""
        configured_host = configured.hostname or ""

        # Detect localhost/127.0.0.1 mismatch and redirect to canonical host
        if (
            request_host in {"localhost", "127.0.0.1"}
            and configured_host in {"localhost", "127.0.0.1"}
            and request_host != configured_host
        ):
            canonical_login_url = f"{configured.scheme}://{configured.netloc}{request.url.path}"
            if request.url.query:
                canonical_login_url = f"{canonical_login_url}?{request.url.query}"
            print(f"[OAuth] Redirecting from {request_host} to {configured_host} for consistency")
            return RedirectResponse(url=canonical_login_url, status_code=307)

    print(f"[OAuth] Using redirect_uri: {redirect_uri}")
    return await google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    google = get_google_oauth_client()
    if google is None:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
        )

    try:
        token = await google.authorize_access_token(request)
        print("TOKEN:", token)
    except OAuthError as e:
        print("OAuth error:", str(e))
        raise HTTPException(status_code=400, detail="Google authorization failed")

    user_info = token.get("userinfo")
    if not user_info:
        user_info = await google.parse_id_token(request, token)

    if not user_info:
        raise HTTPException(status_code=400, detail="Unable to read Google profile")

    email = user_info.get("email")
    name = (user_info.get("name") or "").strip()
    email_verified = user_info.get("email_verified", True)

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")
    if not email_verified:
        raise HTTPException(status_code=400, detail="Google email is not verified")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        fallback_name = email.split("@")[0]
        user = User(
            name=name or fallback_name,
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        subscription = Subscription(
            user_id=user.id,
            plan_type="free",
            expiry_date=date.today() + timedelta(days=365)
        )
        db.add(subscription)
        db.commit()

    token = create_access_token({"sub": user.email})

    create_activity_log(
        db=db,
        user_id=user.id,
        action="USER_LOGIN_GOOGLE",
        description=f"User logged in via Google: {user.email}",
    )
    db.commit()

    token_safe = quote(token, safe="")
    return RedirectResponse(url=f"/app/dashboard?token={token_safe}")


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