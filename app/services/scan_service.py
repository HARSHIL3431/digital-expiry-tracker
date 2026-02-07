from typing import Dict, Any
from datetime import date

from app.services.ocr_service import OCRService
from app.services.expiry_service import ExpiryService, get_expiry_status
from app.services.expiry_parser import ExpiryParser
from app.services.inventory_service import InventoryService
from app.utils.database import SessionLocal
from app.models import ScanResult


class ScanService:
    """
    Full scan pipeline (Phase 4):
    Image → OCR → Expiry Intelligence → Inventory Suggestions → DB Save
    """

    def __init__(self):
        self.ocr_service = OCRService()
        self.expiry_parser = ExpiryParser()
        self.expiry_service = ExpiryService()
        self.inventory_service = InventoryService()

    def scan_image(self, image_path: str) -> Dict[str, Any]:
        # ---------------- 1️⃣ OCR ---------------- #
        ocr_texts = self.ocr_service.enhanced_extract_text(image_path)

        # ---------------- 2️⃣ EXPIRY INTELLIGENCE ---------------- #
        expiry_candidates = []

        for text in ocr_texts:
            parsed_date = self.expiry_parser.extract_expiry_date(text)
            if parsed_date:
                expiry_candidates.append({
                    "raw": text,
                    "normalized": parsed_date.isoformat(),
                    "confidence": 0.8,          # base confidence
                    "source": "parser"
                })

        expiry_result = self.expiry_service.evaluate_candidates(expiry_candidates)
        suggested_expiry = expiry_result.get("suggested")

        expiry_date: date | None = None
        days_left = None
        status = None

        if suggested_expiry:
            expiry_date = date.fromisoformat(suggested_expiry["normalized"])
            status_info = get_expiry_status(expiry_date)
            days_left = status_info["days_left"]
            status = status_info["status"]

        # ---------------- 3️⃣ INVENTORY SUGGESTIONS ---------------- #
        prefix = max(ocr_texts, key=len, default="")
        product_suggestions = self.inventory_service.suggest_products(prefix)

        # ---------------- 4️⃣ DB SAVE ---------------- #
        db = SessionLocal()
        try:
            scan_record = ScanResult(
                expiry_date=expiry_date,
                days_left=days_left,
                status=status,
                extracted_text=" ".join(ocr_texts) if ocr_texts else None,
            )
            db.add(scan_record)
            db.commit()
        finally:
            db.close()

        # ---------------- 5️⃣ RESPONSE ---------------- #
        return {
            "success": True if expiry_date else False,
            "ocr_text": ocr_texts,
            "expiry": expiry_result,
            "product_suggestions": product_suggestions,
            "expiry_date": expiry_date.isoformat() if expiry_date else None,
            "days_left": days_left,
            "expiry_status": status,
        }
