from calendar import month_abbr
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app import models
from app.core.dependencies import get_current_user
from app.utils.database import get_db

router = APIRouter(tags=["Analytics"])


@router.get("/")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    near_expiry_cutoff = today + timedelta(days=30)

    category_expr = func.coalesce(func.nullif(func.trim(models.Product.category), ""), "General")

    category_rows = (
        db.query(category_expr.label("category"), func.count(models.Product.id).label("count"))
        .filter(models.Product.user_id == current_user.id)
        .filter(models.Product.expiry_date <= near_expiry_cutoff)
        .group_by(category_expr)
        .all()
    )

    category_risk = {}
    for row in category_rows:
        category_risk[row.category] = int(row.count or 0)

    if not category_risk:
        category_risk = {"General": 0}

    product_value = models.Product.price * func.coalesce(models.Product.quantity, 1)

    waste_profit_row = (
        db.query(
            func.coalesce(
                func.sum(
                    case((models.Product.expiry_date < today, product_value), else_=0.0)
                ),
                0.0,
            ).label("waste"),
            func.coalesce(
                func.sum(
                    case((models.Product.expiry_date >= today, product_value), else_=0.0)
                ),
                0.0,
            ).label("profit"),
        )
        .filter(models.Product.user_id == current_user.id)
        .first()
    )

    month_rows = (
        db.query(
            func.strftime("%m", models.Product.expiry_date).label("month_number"),
            func.count(models.Product.id).label("count"),
        )
        .filter(models.Product.user_id == current_user.id)
        .group_by(func.strftime("%m", models.Product.expiry_date))
        .order_by(func.strftime("%m", models.Product.expiry_date))
        .all()
    )

    expiry_trend = []
    for row in month_rows:
        month_index = int(row.month_number or 0)
        month_label = month_abbr[month_index] if 1 <= month_index <= 12 else "Unknown"
        expiry_trend.append({"month": month_label, "count": int(row.count or 0)})

    return {
        "category_risk": category_risk,
        "waste_vs_profit": {
            "waste": round(float(waste_profit_row.waste or 0.0), 2),
            "profit": round(float(waste_profit_row.profit or 0.0), 2),
        },
        "expiry_trend": expiry_trend,
    }
