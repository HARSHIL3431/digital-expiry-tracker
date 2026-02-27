from pydantic import BaseModel
from datetime import date


class ProductBase(BaseModel):
    product_name: str
    manufacture_date: date
    expiry_date: date
    price: float


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True