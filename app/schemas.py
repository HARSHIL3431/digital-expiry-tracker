from pydantic import BaseModel

class ProductBase(BaseModel):
    product_name: str
    category: str | None = None
    manufacture_date: str
    expiry_date: str
    price: float

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True
