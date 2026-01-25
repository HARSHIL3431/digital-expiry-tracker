import pytesseract
from PIL import Image
import cv2
import numpy as np


class OCRService:
    def extract_text(self, image_path: str) -> str:
        # Load image using OpenCV
        image = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding (VERY IMPORTANT)
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # OCR configuration
        custom_config = r"--oem 3 --psm 6"

        text = pytesseract.image_to_string(
            thresh,
            config=custom_config,
            lang="eng"
        )

        return text.strip()
