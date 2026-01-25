from typing import Optional
from datetime import date

from app.services.ocr_service import OCRService
from app.services.expiry_parser import ExpiryParser
from app.services.expiry_service import get_expiry_status


class ScanService:
    def __init__(self):
        self.ocr_service = OCRService()
        self.expiry_parser = ExpiryParser()

    def scan_image(self, image_path: str) -> dict:
        """
        Full scan pipeline:
        OCR -> Expiry date extraction -> Status calculation
        """

        # 1. OCR
        extracted_text = self.ocr_service.extract_text(image_path)

        # 2. Parse expiry date
        expiry_date: Optional[date] = self.expiry_parser.extract_expiry_date(
            extracted_text
        )

        if not expiry_date:
            return {
                "success": False,
                "message": "Expiry date not detected",
                "extracted_text": extracted_text
            }

        # 3. Calculate status
        expiry_info = get_expiry_status(expiry_date)

        # 4. Return serialized response
        return {
            "success": True,
            "expiry_date": expiry_date.isoformat(),  # ✅ FIXED
            "expiry_status": expiry_info["status"],
            "days_left": expiry_info["days_left"],
            "extracted_text": extracted_text
        }
