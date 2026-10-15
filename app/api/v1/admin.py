from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.core.security import is_admin
from app.models import User
from app.services.expiry_alert_service import check_expiring_products


router = APIRouter(tags=["Admin"])


@router.post("/run-expiry-check")
def run_expiry_check(current_user: User = Depends(get_current_user)):
    if not is_admin(current_user.email):
        raise HTTPException(status_code=403, detail="Admin access required")
    check_expiring_products()
    return {"status": "Expiry check executed successfully"}
