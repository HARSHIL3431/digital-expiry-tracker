from datetime import date


def get_expiry_status(expiry_date: date) -> dict:
    """
    Determine expiry status based on today's date.

    Rules:
    - expired      -> expiry_date < today
    - near_expiry  -> expiry_date within next 30 days
    - safe         -> expiry_date > 30 days
    """

    today = date.today()
    days_left = (expiry_date - today).days

    if days_left < 0:
        status = "expired"
    elif days_left <= 30:
        status = "near_expiry"
    else:
        status = "safe"

    return {
        "expiry_date": expiry_date,
        "days_left": days_left,
        "status": status,
    }
