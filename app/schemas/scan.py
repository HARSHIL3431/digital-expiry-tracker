from pydantic import BaseModel
from typing import Optional


class ScanResponse(BaseModel):
    success: bool
    expiry_date: Optional[str] = None
    expiry_status: Optional[str] = None
    days_left: Optional[int] = None
    extracted_text: str
    message: Optional[str] = None
