from datetime import date, datetime

def get_expiry_status(expiry_date):
    today = date.today()

    # Convert string → date if needed
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()

    days_left = (expiry_date - today).days

    if days_left < 0:
        status = "EXPIRED"
    elif days_left <= 7:
        status = "NEAR_EXPIRY"
    else:
        status = "FRESH"

    return {
        "status": status,
        "days_left": days_left
    }
