import cv2


def preprocess_image(image_path: str):
    """
    Improved preprocessing for dot-matrix & low-contrast text
    """

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Invalid image path: {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Resize (very important for dot-matrix text)
    gray = cv2.resize(
        gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC
    )

    # Adaptive thresholding (better than OTSU here)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    return thresh
