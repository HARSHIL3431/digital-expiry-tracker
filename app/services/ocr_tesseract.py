import pytesseract

class TesseractRecognizer:
    @staticmethod
    def recognize(image):
        config = (
            "--oem 3 "
            "--psm 6 "
            "-c tessedit_char_whitelist=0123456789/-.EXP"
        )

        text = pytesseract.image_to_string(image, config=config)
        return text.strip()
