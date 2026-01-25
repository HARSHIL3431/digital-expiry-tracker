from datetime import date


def get_expiry_status(expiry_date: date) -> dict:
    today = date.today()
    days_left = (expiry_date - today).days

    if days_left < 0:
        status = "EXPIRED"
    elif days_left <= 30:
        status = "NEAR_EXPIRY"
    else:
        status = "FRESH"

    return {
        "status": status,
        "days_left": days_left
    }
