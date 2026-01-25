from typing import Dict

from app.services.ocr_service import OCRService
from app.services.expiry_parser import ExpiryParser
from app.services.expiry_service import get_expiry_status
from app.utils.database import SessionLocal
from app.models import ScanResult


class ScanService:
    """
    Full scan pipeline:
    Image → OCR → Expiry Parsing → Status Calculation → DB Save
    """

    def __init__(self):
        self.ocr_service = OCRService()
        self.expiry_parser = ExpiryParser()

    def scan_image(self, image_path: str) -> Dict:
        # 1️⃣ OCR
        extracted_text = self.ocr_service.extract_text(image_path)

        # 2️⃣ Extract ONLY expiry date (parser already ignores MFG)
        expiry_date = self.expiry_parser.extract_expiry_date(extracted_text)

        if not expiry_date:
            return {
                "success": False,
                "message": "Expiry date not detected",
                "expiry_date": None,
                "days_left": None,
                "expiry_status": None,
                "extracted_text": extracted_text,
            }

        # 3️⃣ Calculate expiry status
        expiry_info = get_expiry_status(expiry_date)

        # 4️⃣ Persist scan result to DB
        db = SessionLocal()
        try:
            scan_record = ScanResult(
                expiry_date=expiry_info["expiry_date"],
                days_left=expiry_info["days_left"],
                status=expiry_info["status"],
                extracted_text=extracted_text,
            )
            db.add(scan_record)
            db.commit()
        finally:
            db.close()

        # 5️⃣ API response
        return {
            "success": True,
            "expiry_date": expiry_info["expiry_date"].isoformat(),
            "days_left": expiry_info["days_left"],
            "expiry_status": expiry_info["status"],
            "extracted_text": extracted_text,
        }
