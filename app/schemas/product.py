from pydantic import BaseModel
from datetime import date, datetime


class ProductBase(BaseModel):
    product_name: str
    manufacture_date: date
    expiry_date: date
    price: float


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductWithExpiryResponse(ProductResponse):
    expiry_status: str
    days_left: int


class ProductListResponse(BaseModel):
    data: list[ProductWithExpiryResponse]
    pagination: dict


class ProductDeleteResponse(BaseModel):
    message: str


class ExpiryStatusGroupedResponse(BaseModel):
    expired: list[ProductWithExpiryResponse]
    near_expiry: list[ProductWithExpiryResponse]
    fresh: list[ProductWithExpiryResponse]


class AlertCountsResponse(BaseModel):
    expired: int
    expiring_soon: int
    total_alerts: int


class ProductAlertItemResponse(BaseModel):
    id: int
    product_name: str
    expiry_date: date
    days_left: int
    expiry_status: str


class ProductAlertsResponse(BaseModel):
    soon_days: int
    counts: AlertCountsResponse
    expired: list[ProductAlertItemResponse]
    expiring_soon: list[ProductAlertItemResponse]

    class Config:
        from_attributes = True