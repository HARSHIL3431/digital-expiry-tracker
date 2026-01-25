from datetime import date, timedelta
from app.services.expiry_service import get_expiry_status


def test_expired():
    expiry = date.today() - timedelta(days=1)
    result = get_expiry_status(expiry)
    assert result["status"] == "expired"


def test_near_expiry():
    expiry = date.today() + timedelta(days=15)
    result = get_expiry_status(expiry)
    assert result["status"] == "near_expiry"


def test_safe():
    expiry = date.today() + timedelta(days=90)
    result = get_expiry_status(expiry)
    assert result["status"] == "safe"
