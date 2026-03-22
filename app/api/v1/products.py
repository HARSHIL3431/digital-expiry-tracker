from datetime import date
from io import StringIO
import csv

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
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

    product_payload = product.model_dump()
    product_payload["category"] = product_payload.get("category") or "General"
    raw_quantity = product_payload.get("quantity")
    product_payload["quantity"] = raw_quantity if isinstance(raw_quantity, int) and raw_quantity > 0 else 1

    db_product = models.Product(
        **product_payload,
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


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    try:
        decoded_content = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from error

    reader = csv.DictReader(StringIO(decoded_content))
    field_names = reader.fieldnames or []
    if not field_names:
        raise HTTPException(status_code=400, detail="CSV headers are missing")

    required_fields = {"name", "price", "expiry_date"}
    normalized_headers = {header.strip().lower() for header in field_names if header}
    missing_fields = sorted(required_fields - normalized_headers)
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required CSV columns: {', '.join(missing_fields)}"
        )

    subscription = db.query(models.Subscription).filter(
        models.Subscription.user_id == current_user.id
    ).first()
    if not subscription:
        raise HTTPException(status_code=400, detail="Subscription not found")

    existing_products = db.query(models.Product).filter(
        models.Product.user_id == current_user.id
    ).count()

    remaining_free_slots = None
    if subscription.plan_type == "free":
        remaining_free_slots = max(0, 5 - existing_products)

    products_to_insert = []
    inserted = 0
    skipped = 0

    for row in reader:
        normalized_row = {
            (key or "").strip().lower(): (value or "").strip()
            for key, value in row.items()
        }

        name = normalized_row.get("name", "")
        category = normalized_row.get("category", "") or "General"
        quantity_raw = normalized_row.get("quantity", "") or "1"
        price_raw = normalized_row.get("price", "")
        expiry_raw = normalized_row.get("expiry_date", "")

        if not all([name, price_raw, expiry_raw]):
            skipped += 1
            continue

        try:
            quantity = int(quantity_raw)
            if quantity < 0:
                raise ValueError("quantity must be non-negative")

            price = float(price_raw)
            if price < 0:
                raise ValueError("price must be non-negative")

            expiry_date = date.fromisoformat(expiry_raw)
        except ValueError:
            skipped += 1
            continue

        if remaining_free_slots is not None and inserted >= remaining_free_slots:
            skipped += 1
            continue

        products_to_insert.append(models.Product(
            product_name=name,
            category=category,
            quantity=quantity,
            manufacture_date=date.today(),
            expiry_date=expiry_date,
            price=price,
            user_id=current_user.id,
        ))
        inserted += 1

    if products_to_insert:
        db.add_all(products_to_insert)
        db.commit()

    return {
        "inserted": inserted,
        "skipped": skipped,
    }


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
            "category": product.category or "General",
            "quantity": product.quantity or 1,
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
            "category": product.category or "General",
            "quantity": product.quantity or 1,
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


# ==============================
# 🆕 ADD PRODUCT FROM SCAN (Task 5)
# ==============================

@router.post("/add-from-scan")
def add_product_from_scan(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Add a product to inventory from OCR scan result.
    User-confirmed endpoint (not auto-save).
    
    Expected payload:
    {
        "name": "Product Name",
        "quantity": 1,
        "expiry_date": "2025-12-31"
    }
    """
    try:
        # Extract fields with defaults
        product_name = payload.get("name", "Unknown Product").strip()
        quantity = int(payload.get("quantity", 1))
        expiry_date_str = payload.get("expiry_date")

        if not product_name:
            raise ValueError("Product name is required")
        if not expiry_date_str:
            raise ValueError("Expiry date is required")

        # Parse expiry date
        expiry_date = date.fromisoformat(expiry_date_str)

        # Create product
        product = models.Product(
            product_name=product_name,
            category="Scanned",
            quantity=quantity,
            manufacture_date=date.today(),
            expiry_date=expiry_date,
            price=0.0,
            user_id=current_user.id
        )

        db.add(product)
        db.commit()

        # Log activity
        create_activity_log(
            db=db,
            user_id=current_user.id,
            action="PRODUCT_ADDED_FROM_SCAN",
            details=f"Added '{product_name}' (Qty: {quantity}) from OCR scan"
        )

        return {"success": True, "product_id": product.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add product: {str(e)}")