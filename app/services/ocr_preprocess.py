import cv2
import numpy as np

class OCRPreprocess:
    @staticmethod
    def preprocess(image_path: str):
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError("Unable to read image")

        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.GaussianBlur(gray, (5, 5), 0)

        # Contrast enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            contrast,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        # Sharpen
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        sharpened = cv2.filter2D(thresh, -1, kernel)

        return sharpened
