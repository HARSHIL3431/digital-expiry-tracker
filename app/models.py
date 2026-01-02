from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    manufacture_date = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
