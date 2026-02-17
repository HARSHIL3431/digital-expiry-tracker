import pytesseract


class TesseractRecognizer:
    @staticmethod
    def recognize(image):
        """
        Recognize text from cropped image region.
        No restrictive whitelist.
        """

        config = "--oem 3 --psm 6"

        text = pytesseract.image_to_string(
            image,
            config=config,
            lang="eng"
        )

        return text.strip()
