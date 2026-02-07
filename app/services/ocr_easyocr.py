import easyocr

class EasyOCRDetector:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)

    def detect(self, image):
        """
        Returns list of bounding boxes
        """
        results = self.reader.readtext(image)
        boxes = []

        for bbox, text, confidence in results:
            boxes.append({
                "bbox": bbox,
                "confidence": confidence
            })

        return boxes
