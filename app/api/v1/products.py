from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.utils.database import get_db
from app.schemas.product import ProductCreate
from app.services.expiry_service import get_expiry_status
from app.core.dependencies import get_current_user

# ✅ Removed prefix here (IMPORTANT)
router = APIRouter(tags=["Products"])


# ==============================
# ➕ CREATE PRODUCT
# ==============================

@router.post("/")
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

    return db_product


# ==============================
# 📋 GET PRODUCTS
# ==============================

@router.get("/")
def get_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    products = db.query(models.Product).filter(
        models.Product.user_id == current_user.id
    ).all()

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

    return response


# ==============================
# ❌ DELETE PRODUCT
# ==============================

@router.delete("/{product_id}")
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

    db.delete(product)
    db.commit()

    return {"message": "Product deleted"}


# ==============================
# 📊 GROUP BY EXPIRY STATUS
# ==============================

@router.get("/expiry-status")
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