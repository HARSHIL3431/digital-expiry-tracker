import os
import threading

from app.services.ocr_preprocess import OCRPreprocess
from app.services.ocr_easyocr import EasyOCRDetector
from app.services.ocr_tesseract import TesseractRecognizer
from app.services.expiry_parser import ExpiryParser


class OCRService:
    """
    Adaptive OCR Service

    Strategy:
    1. Try a full-image Tesseract pass, since that is fastest.
    2. If no expiry date is detected, fall back to EasyOCR region detection
       combined with Tesseract recognition.
    """

    def __init__(self):
        self.expiry_parser = ExpiryParser()
        self._easyocr_reader = None
        self._easyocr_lock = threading.Lock()
        self._easyocr_error = None

    @staticmethod
    def _normalize_bbox_points(raw_bbox):
        if not raw_bbox:
            return []

        normalized = []
        for point in raw_bbox:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                normalized.append([int(point[0]), int(point[1])])
            except (TypeError, ValueError):
                continue

        return normalized

    @staticmethod
    def _require_python_ocr_dependencies() -> None:
        """Check the optional Python OCR packages without allowing import errors to mask failures."""
        missing = []
        try:
            import cv2  # noqa: F401
        except Exception:
            missing.append("opencv-python (cv2)")
        try:
            import pytesseract  # noqa: F401
        except Exception:
            missing.append("pytesseract")

        # EasyOCR remains optional: Tesseract can handle simple expiry labels
        # without the heavier EasyOCR/Torch stack. It is only attempted in
        # the fallback path and is ignored when absent.
        if missing:
            raise RuntimeError(
                "OCR dependencies are missing: "
                + ", ".join(missing)
                + ". Install OCR extras to use /api/v1/scan/* endpoints."
            )

    def _require_ocr_dependencies(self) -> None:
        self._require_python_ocr_dependencies()
        self._require_tesseract_engine()

    @staticmethod
    def get_tesseract_command():
        """Resolve and return the currently configured Tesseract executable path."""
        return TesseractRecognizer.get_tesseract_command()

    @staticmethod
    def _require_python_dependencies() -> None:
        OCRService._require_python_ocr_dependencies()

    def _require_tesseract_engine(self) -> str:
        command = self.get_tesseract_command()
        if command is None:
            from app.services.ocr_tesseract import NO_TESSERACT_MESSAGE

            raise RuntimeError(NO_TESSERACT_MESSAGE)
        return command

    def _get_easyocr_reader(self):
        """Create the EasyOCR reader once and reuse it across OCR requests."""
        with self._easyocr_lock:
            if self._easyocr_reader is not None:
                return self._easyocr_reader
            if self._easyocr_error is not None:
                raise RuntimeError(self._easyocr_error)

            try:
                import easyocr
            except Exception as exc:
                self._easyocr_error = f"EasyOCR is not installed: {exc}"
                raise RuntimeError(self._easyocr_error) from exc

            try:
                reader = easyocr.Reader(["en"], gpu=False)
            except Exception as exc:
                self._easyocr_error = f"EasyOCR could not be initialized: {exc}"
                raise RuntimeError(self._easyocr_error) from exc

            self._easyocr_reader = reader
            return reader

    # ---------------- FULL IMAGE TESSERACT ---------------- #

    def _full_image_tesseract(self, image_path: str):
        self._require_python_ocr_dependencies()
        self._require_tesseract_engine()

        import cv2

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Unable to read image for OCR processing")

        config = "--oem 3 --psm 6"
        command = self.get_tesseract_command()
        if command is None:
            from app.services.ocr_tesseract import NO_TESSERACT_MESSAGE

            raise RuntimeError(NO_TESSERACT_MESSAGE)

        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = command
        timeout = 30
        try:
            timeout = int(os.getenv("OCR_TIMEOUT_SECONDS", "30"))
        except ValueError:
            timeout = 30

        text = pytesseract.image_to_string(
            image,
            config=config,
            lang="eng",
            timeout=timeout,
        )

        text = text.strip()
        if text:
            return [text]
        return []

    # ---------------- EASYOCR + CROP PIPELINE ---------------- #

    def _easyocr_pipeline(self, image_path: str):
        self._require_python_ocr_dependencies()
        self._require_tesseract_engine()
        image = OCRPreprocess.preprocess(image_path)

        detector = EasyOCRDetector(self._get_easyocr_reader())
        boxes = detector.detect(image)

        extracted_text = []
        for box in boxes:
            bbox = self._normalize_bbox_points(box.get("bbox"))
            if len(bbox) != 4:
                continue

            (tl, tr, br, bl) = bbox
            x1, y1 = int(tl[0]), int(tl[1])
            x2, y2 = int(br[0]), int(br[1])
            crop = image[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            text = TesseractRecognizer.recognize(crop)
            if text:
                extracted_text.append(text)

        return extracted_text

    def _easyocr_pipeline_with_regions(self, image_path: str):
        self._require_python_ocr_dependencies()
        self._require_tesseract_engine()
        image = OCRPreprocess.preprocess(image_path)

        detector = EasyOCRDetector(self._get_easyocr_reader())
        boxes = detector.detect(image)

        regions = []
        for box in boxes:
            bbox = self._normalize_bbox_points(box.get("bbox"))
            if len(bbox) != 4:
                continue

            (tl, tr, br, bl) = bbox
            x1, y1 = int(tl[0]), int(tl[1])
            x2, y2 = int(br[0]), int(br[1])
            crop = image[y1:y2, x1:x2]

            text = ""
            if crop.size != 0:
                text = TesseractRecognizer.recognize(crop) or ""

            regions.append(
                {
                    "text": text,
                    "bbox": bbox,
                    "detector_confidence": float(box.get("confidence", 0.0) or 0.0),
                }
            )

        return regions

    # ---------------- MAIN ENTRY ---------------- #

    def enhanced_extract_text(self, image_path: str):
        tesseract_texts = self._full_image_tesseract(image_path)

        for text in tesseract_texts:
            if self.expiry_parser.extract_expiry_date(text):
                return tesseract_texts

        # Keep Tesseract-only deployments functional when EasyOCR is unavailable.
        try:
            easy_texts = self._easyocr_pipeline(image_path)
        except RuntimeError:
            return tesseract_texts
        return easy_texts

    def enhanced_extract_with_regions(self, image_path: str):
        tesseract_texts = self._full_image_tesseract(image_path)

        for text in tesseract_texts:
            if self.expiry_parser.extract_expiry_date(text):
                return {
                    "texts": tesseract_texts,
                    "regions": [],
                    "engine": "tesseract_full",
                }

        # EasyOCR is optional on free deployments where only Tesseract is installed.
        try:
            easy_regions = self._easyocr_pipeline_with_regions(image_path)
        except RuntimeError:
            return {
                "texts": tesseract_texts,
                "regions": [],
                "engine": "tesseract_full",
            }
        return {
            "texts": [region["text"] for region in easy_regions],
            "regions": easy_regions,
            "engine": "easyocr_regions",
        }
