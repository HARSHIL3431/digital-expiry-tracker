from datetime import date, timedelta
from app.services.expiry_service import get_expiry_status

tests = {
    "expired": date.today() - timedelta(days=5),
    "near_expiry": date.today() + timedelta(days=10),
    "fresh": date.today() + timedelta(days=90),
}

for name, d in tests.items():
    print(name, d, "=>", get_expiry_status(d))
