from fastapi import APIRouter

from app.services.expiry_alert_service import check_expiring_products


router = APIRouter(tags=["Admin"])


@router.post("/run-expiry-check")
def run_expiry_check():
    check_expiring_products()
    return {"status": "Expiry check executed successfully"}
