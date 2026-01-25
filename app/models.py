from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime
from app.utils.database import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    expiry_date = Column(Date, nullable=False)
    days_left = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    extracted_text = Column(String, nullable=True)
    scanned_at = Column(DateTime, default=datetime.utcnow)