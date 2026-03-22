from typing import Dict, Any, List
from datetime import date
from math import hypot
from sqlalchemy.exc import SQLAlchemyError

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
        self.context_distance_threshold = 140.0
        self.manual_input_confidence_threshold = 0.65

    @staticmethod
    def _bbox_center(bbox: Any) -> tuple[float, float] | None:
        if not bbox or len(bbox) != 4:
            return None
        xs = [float(point[0]) for point in bbox]
        ys = [float(point[1]) for point in bbox]
        return (sum(xs) / 4.0, sum(ys) / 4.0)

    def _score_with_spatial_context(self, regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not regions:
            return []

        expiry_candidates: List[Dict[str, Any]] = []
        for idx, region in enumerate(regions):
            text = (region.get("text") or "").strip()
            if not text:
                continue

            line_has_expiry = self.expiry_parser._contains_expiry_keyword(text)
            line_has_mfg = self.expiry_parser._contains_mfg_keyword(text)

            if line_has_mfg and not line_has_expiry:
                continue

            parsed_items = self.expiry_parser.extract_dates_with_confidence(text)
            if not parsed_items:
                continue

            current_center = self._bbox_center(region.get("bbox"))
            nearby_texts: List[str] = []

            if current_center:
                for jdx, other in enumerate(regions):
                    if jdx == idx:
                        continue
                    other_text = (other.get("text") or "").strip()
                    other_center = self._bbox_center(other.get("bbox"))
                    if not other_text or not other_center:
                        continue

                    if hypot(current_center[0] - other_center[0], current_center[1] - other_center[1]) <= self.context_distance_threshold:
                        nearby_texts.append(other_text)

            nearby_blob = "\n".join(nearby_texts)
            has_expiry_context = self.expiry_parser._contains_expiry_keyword(nearby_blob)
            has_mfg_context = self.expiry_parser._contains_mfg_keyword(nearby_blob)

            detector_conf = float(region.get("detector_confidence", 0.0) or 0.0)

            for parsed_date, parser_conf in parsed_items:
                base_conf = 0.35 + (detector_conf * 0.4) + (float(parser_conf) * 0.12)

                if line_has_expiry or has_expiry_context:
                    base_conf += 0.2

                if line_has_mfg or has_mfg_context:
                    base_conf -= 0.35

                final_conf = max(0.0, min(1.0, base_conf))

                expiry_candidates.append({
                    "raw": text,
                    "normalized": parsed_date.isoformat(),
                    "confidence": round(final_conf, 3),
                    "source": "bbox_context",
                    "bbox": region.get("bbox"),
                })

        return expiry_candidates

    def scan_image(self, image_path: str) -> Dict[str, Any]:

        # ---------------- 1️⃣ OCR ---------------- #
        ocr_payload = self.ocr_service.enhanced_extract_with_regions(image_path)
        ocr_texts = ocr_payload.get("texts", []) if isinstance(ocr_payload, dict) else []
        ocr_regions = ocr_payload.get("regions", []) if isinstance(ocr_payload, dict) else []

        # ---------------- 2️⃣ EXPIRY INTELLIGENCE ---------------- #
        expiry_candidates = self._score_with_spatial_context(ocr_regions)

        # Legacy-safe fallback for non-bbox OCR paths
        if not expiry_candidates:
            for text in ocr_texts:
                parsed_date = self.expiry_parser.extract_expiry_date(text)
                if parsed_date:
                    expiry_candidates.append({
                        "raw": text,
                        "normalized": parsed_date.isoformat(),
                        "confidence": 0.8,
                        "source": "parser"
                    })

        expiry_result = self.expiry_service.evaluate_candidates(expiry_candidates)
        suggested_expiry = expiry_result.get("suggested")

        expiry_date: date | None = None
        days_left = None
        status = None
        needs_manual_input = False

        if suggested_expiry:
            try:
                suggested_confidence = float(suggested_expiry.get("confidence", 0.0) or 0.0)
                if suggested_confidence < self.manual_input_confidence_threshold:
                    needs_manual_input = True
                else:
                    expiry_date = date.fromisoformat(suggested_expiry["normalized"])
                    status_info = get_expiry_status(expiry_date)
                    days_left = status_info["days_left"]
                    status = status_info["status"]
            except Exception:
                expiry_date = None
                days_left = None
                status = None
                needs_manual_input = False

        # ---------------- 3️⃣ INVENTORY SUGGESTIONS ---------------- #
        prefix = max(ocr_texts, key=len, default="")
        product_suggestions = self.inventory_service.suggest_products(prefix)

        # ---------------- 4️⃣ SAFE DB SAVE ---------------- #
        if expiry_date:
            db = SessionLocal()
            try:
                scan_record = ScanResult(
                    image_path=image_path,
                    detected_expiry=expiry_date.isoformat(),
                    confidence=str(suggested_expiry.get("confidence", 0.0)),
                    extracted_text=" ".join(ocr_texts) if ocr_texts else None,
                )
                db.add(scan_record)
                db.commit()
            except SQLAlchemyError:
                db.rollback()
            finally:
                db.close()

        # ➕ MARK EXPIRY REGIONS (Task 1) ➕ #
        if suggested_expiry:
            expiry_text = suggested_expiry.get("raw", "").lower()
            for region in ocr_regions:
                region["is_expiry"] = expiry_text in region.get("text", "").lower()

        # ❌ DB SAVE DISABLED - Now user-confirmed via API (Task 2 refactoring) ❌ #
        # Users will confirm and save via /api/v1/product/add-from-scan endpoint

        # ---------------- 5️⃣ RESPONSE ---------------- #
        response_message = "Expiry detected" if expiry_date else "Expiry date not detected"
        if needs_manual_input:
            response_message = "Low confidence. Please confirm expiry date."

        return {
            "success": bool(expiry_date),
            "message": response_message,
            "ocr_text": ocr_texts,
            "ocr_regions": ocr_regions,
            "expiry": expiry_result,
            "product_suggestions": product_suggestions,
            "expiry_date": expiry_date.isoformat() if expiry_date else None,
            "days_left": days_left,
            "expiry_status": status,
            "needs_manual_input": needs_manual_input,
        }
