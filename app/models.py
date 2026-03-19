from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.database import Base


# ------------------ EXISTING SCAN RESULT ------------------

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String)
    extracted_text = Column(String)
    detected_expiry = Column(String)
    confidence = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# ------------------ USER ------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="owner")
    subscription = relationship("Subscription", back_populates="user", uselist=False)


# ------------------ PRODUCT ------------------

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    product_name = Column(String, nullable=False)
    manufacture_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="products")
    alerts = relationship("Alert", back_populates="product")


# ------------------ ALERT ------------------

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_date = Column(Date)
    status = Column(String, default="pending")

    product_id = Column(Integer, ForeignKey("products.id"))

    product = relationship("Product", back_populates="alerts")


# ------------------ SUBSCRIPTION ------------------

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    plan_type = Column(String, default="free")
    expiry_date = Column(Date)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="subscription")


# ------------------ ACTIVITY LOG ------------------

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    description = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)