from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, database
from app.services.expiry_service import get_expiry_status

# ✅ router MUST be defined before decorators
router = APIRouter(prefix="/products", tags=["Products"])


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    if product.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")

    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/")
def get_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
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


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}
