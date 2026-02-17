import cv2
import pytesseract

from app.services.ocr_preprocess import OCRPreprocess
from app.services.ocr_easyocr import EasyOCRDetector
from app.services.ocr_tesseract import TesseractRecognizer
from app.services.expiry_parser import ExpiryParser


class OCRService:
    """
    Adaptive OCR Service

    Strategy:
    1️⃣ Try full image Tesseract first
    2️⃣ If expiry detected → return
    3️⃣ Else → use EasyOCR detection + Tesseract recognition
    """

    def __init__(self):
        self.expiry_parser = ExpiryParser()

    # ---------------- FULL IMAGE TESSERACT ---------------- #

    def _full_image_tesseract(self, image_path: str):
        image = cv2.imread(image_path)

        if image is None:
            return []

        config = "--oem 3 --psm 6"

        text = pytesseract.image_to_string(
            image,
            config=config,
            lang="eng"
        )

        text = text.strip()

        if text:
            return [text]

        return []

    # ---------------- EASYOCR + CROP PIPELINE ---------------- #

    def _easyocr_pipeline(self, image_path: str):
        processed = OCRPreprocess.preprocess(image_path)

        detector = EasyOCRDetector()
        boxes = detector.detect(processed)

        extracted_text = []

        for box in boxes:
            (tl, tr, br, bl) = box["bbox"]

            x1, y1 = int(tl[0]), int(tl[1])
            x2, y2 = int(br[0]), int(br[1])

            crop = processed[y1:y2, x1:x2]

            if crop.size == 0:
                continue

            text = TesseractRecognizer.recognize(crop)

            if text:
                extracted_text.append(text)

        return extracted_text

    # ---------------- MAIN ENTRY ---------------- #

    def enhanced_extract_text(self, image_path: str):
        """
        Adaptive OCR execution.
        """

        # Step 1️⃣ Try full image Tesseract
        tesseract_texts = self._full_image_tesseract(image_path)

        # Check if expiry detected
        for text in tesseract_texts:
            if self.expiry_parser.extract_expiry_date(text):
                print("✅ Expiry detected via Full Image Tesseract")
                return tesseract_texts

        # Step 2️⃣ Fallback to EasyOCR pipeline
        print("⚠ Full Image Tesseract failed → Switching to EasyOCR pipeline")

        easy_texts = self._easyocr_pipeline(image_path)

        return easy_texts
