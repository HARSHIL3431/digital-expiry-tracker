from pydantic import BaseModel
from datetime import date
from typing import Optional


class ProductBase(BaseModel):
    name: str
    expiry_date: date


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    is_expired: bool

    class Config:
        from_attributes = True
