from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.utils.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductListResponse,
    ProductDeleteResponse,
    ExpiryStatusGroupedResponse,
    ProductAlertsResponse,
)
from app.services.expiry_service import get_expiry_status
from app.core.dependencies import get_current_user
from app.services.activity_log_service import create_activity_log

# ✅ Removed prefix here (IMPORTANT)
router = APIRouter(tags=["Products"])


# ==============================
# ➕ CREATE PRODUCT
# ==============================

@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    subscription = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=400, detail="Subscription not found")

    product_count = db.query(models.Product).filter(
        models.Product.user_id == current_user.id
    ).count()

    if subscription.plan_type == "free" and product_count >= 5:
        raise HTTPException(
            status_code=403,
            detail="Free plan limit reached. Upgrade to PRO."
        )

    if product.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")

    db_product = models.Product(
        **product.model_dump(),
        user_id=current_user.id
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    create_activity_log(
        db=db,
        user_id=current_user.id,
        action="PRODUCT_CREATE",
        description=f"Created product '{db_product.product_name}' (id={db_product.id})",
    )

    expiry_info = get_expiry_status(db_product.expiry_date)
    if expiry_info["status"] in {"expired", "near_expiry"}:
        print(
            f"[NOTIFICATION] User {current_user.email}: product '{db_product.product_name}' "
            f"is {expiry_info['status']} ({expiry_info['days_left']} day(s) left)."
        )
        create_activity_log(
            db=db,
            user_id=current_user.id,
            action="EXPIRY_NOTICE",
            description=(
                f"Product '{db_product.product_name}' flagged as {expiry_info['status']} "
                f"({expiry_info['days_left']} day(s) left)"
            ),
        )

    db.commit()

    return db_product


# ==============================
# 📋 GET PRODUCTS
# ==============================

@router.get("/", response_model=ProductListResponse)
def get_products(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Product).filter(
        models.Product.user_id == current_user.id
    )

    if search:
        query = query.filter(models.Product.product_name.ilike(f"%{search.strip()}%"))

    total_records = query.count()
    offset = (page - 1) * limit

    products = query.order_by(models.Product.expiry_date.asc()).offset(offset).limit(limit).all()

    response = []

    for product in products:
        expiry_info = get_expiry_status(product.expiry_date)

        response.append({
            "id": product.id,
            "product_name": product.product_name,
            "manufacture_date": product.manufacture_date,
            "expiry_date": product.expiry_date,
            "price": product.price,
            "created_at": product.created_at,
            "expiry_status": expiry_info["status"],
            "days_left": expiry_info["days_left"]
        })

    total_pages = max((total_records + limit - 1) // limit, 1)

    return {
        "data": response,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": total_pages,
            "search": search or "",
        },
    }


# ==============================
# ❌ DELETE PRODUCT
# ==============================

@router.delete("/{product_id}", response_model=ProductDeleteResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_name = product.product_name
    product_id = product.id

    db.delete(product)
    db.commit()

    create_activity_log(
        db=db,
        user_id=current_user.id,
        action="PRODUCT_DELETE",
        description=f"Deleted product '{product_name}' (id={product_id})",
    )
    db.commit()

    return {"message": "Product deleted"}


# ==============================
# 📊 GROUP BY EXPIRY STATUS
# ==============================

@router.get("/expiry-status", response_model=ExpiryStatusGroupedResponse)
def get_products_by_expiry_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    products = db.query(models.Product).filter(
        models.Product.user_id == current_user.id
    ).all()

    grouped = {
        "expired": [],
        "near_expiry": [],
        "fresh": []
    }

    for product in products:
        expiry_info = get_expiry_status(product.expiry_date)

        product_data = {
            "id": product.id,
            "product_name": product.product_name,
            "manufacture_date": product.manufacture_date,
            "expiry_date": product.expiry_date,
            "price": product.price,
            "created_at": product.created_at,
            "expiry_status": expiry_info["status"],
            "days_left": expiry_info["days_left"]
        }

        if expiry_info["status"] == "EXPIRED":
            grouped["expired"].append(product_data)
        elif expiry_info["status"] == "NEAR_EXPIRY":
            grouped["near_expiry"].append(product_data)
        else:
            grouped["fresh"].append(product_data)

    return grouped


# ==============================
# 🚨 ALERTS (EXPIRED + SOON)
# ==============================

@router.get("/alerts", response_model=ProductAlertsResponse)
def get_expiry_alerts(
    soon_days: int = 7,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    products = db.query(models.Product).filter(
        models.Product.user_id == current_user.id
    ).all()

    expired = []
    expiring_soon = []

    for product in products:
        expiry_info = get_expiry_status(product.expiry_date)

        product_data = {
            "id": product.id,
            "product_name": product.product_name,
            "expiry_date": product.expiry_date,
            "days_left": expiry_info["days_left"],
            "expiry_status": expiry_info["status"],
        }

        if expiry_info["days_left"] < 0:
            expired.append(product_data)
        elif expiry_info["days_left"] <= soon_days:
            expiring_soon.append(product_data)

    return {
        "soon_days": soon_days,
        "counts": {
            "expired": len(expired),
            "expiring_soon": len(expiring_soon),
            "total_alerts": len(expired) + len(expiring_soon),
        },
        "expired": expired,
        "expiring_soon": expiring_soon,
    }