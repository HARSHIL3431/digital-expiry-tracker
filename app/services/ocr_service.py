import pytesseract
import cv2
import numpy as np

from app.services.ocr_preprocess import OCRPreprocess
from app.services.ocr_easyocr import EasyOCRDetector
from app.services.ocr_tesseract import TesseractRecognizer


class OCRService:
    """
    OCR Service
    - extract_text(): legacy OCR (Tesseract only)
    - enhanced_extract_text(): v2 OCR (Preprocess + EasyOCR + Tesseract)
    """

    def extract_text(self, image_path: str) -> str:
        """
        Legacy OCR method (DO NOT REMOVE)
        """
        image = cv2.imread(image_path)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        custom_config = r"--oem 3 --psm 6"

        text = pytesseract.image_to_string(
            thresh,
            config=custom_config,
            lang="eng"
        )

        return text.strip()

    def enhanced_extract_text(self, image_path: str):
        """
        Enhanced OCR pipeline (v2)
        Preprocessing → EasyOCR detection → Tesseract recognition
        """

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
