import cv2


def preprocess_image(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Invalid image path: {image_path}")

    height, width, _ = image.shape

    # 🔑 Crop bottom 35% where expiry dates usually exist
    cropped = image[int(height * 0.65):height, 0:width]

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(
        gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC
    )

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    return thresh
