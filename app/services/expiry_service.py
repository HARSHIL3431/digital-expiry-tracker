from datetime import date

NEAR_EXPIRY_THRESHOLD_DAYS = 30


def get_expiry_status(expiry_date: date) -> dict:
    """
    Determine expiry status and days left.
    """
    today = date.today()
    days_left = (expiry_date - today).days

    if days_left < 0:
        status = "EXPIRED"
    elif days_left <= NEAR_EXPIRY_THRESHOLD_DAYS:
        status = "NEAR_EXPIRY"
    else:
        status = "FRESH"

    return {
        "status": status,
        "days_left": days_left
    }
