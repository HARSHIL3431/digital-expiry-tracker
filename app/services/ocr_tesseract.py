"""Utilities for locating and invoking the standalone Tesseract OCR engine."""

import os
import shutil
from pathlib import Path
from typing import Optional

COMMON_TESSERACT_LOCATIONS = (
    Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
    Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    Path("C:/Tesseract-OCR/tesseract.exe"),
    Path("C:/tools/Tesseract-OCR/tesseract.exe"),
)

NO_TESSERACT_MESSAGE = (
    "Tesseract OCR engine is not installed or configured. "
    "Install the standalone Tesseract OCR application, or set TESSERACT_CMD "
    "to the full path of its executable (for example "
    "C:/Program Files/Tesseract-OCR/tesseract.exe). "
    "Python packages such as pytesseract only provide a wrapper; they do not "
    "install the OCR engine itself."
)


def _normalize_command(candidate: str) -> Optional[str]:
    """Return an executable path/command for a user-supplied or discovered value."""
    if candidate is None:
        return None

    candidate = candidate.strip().strip('"').strip("'")
    if not candidate:
        return None

    path = Path(candidate).expanduser()
    if path.is_file():
        return str(path)

    # Allow PATH-based commands such as "tesseract" without converting them into
    # nonexistent absolute paths.
    if os.path.dirname(candidate) == "":
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    return None


def get_tesseract_command() -> Optional[str]:
    """Resolve the explicitly configured, PATH-discovered, or standard command."""

    # Environment configuration, including compatibility with the older
    # TESSERACT_PATH setting.
    for variable in ("TESSERACT_CMD", "TESSERACT_PATH"):
        configured = os.getenv(variable)
        resolved = _normalize_command(configured or "")
        if resolved:
            return resolved

    # Verify common Windows installation locations rather than assuming them.
    for location in COMMON_TESSERACT_LOCATIONS:
        try:
            if location.is_file():
                return str(location)
        except OSError:
            continue

    return shutil.which("tesseract")


def ensure_tesseract_available() -> str:
    """Raise a clear error unless Tesseract can actually be invoked."""
    command = get_tesseract_command()
    if command is None:
        raise RuntimeError(NO_TESSERACT_MESSAGE)
    return command


class TesseractRecognizer:
    """Small wrapper that configures pytesseract before recognition."""

    @staticmethod
    def get_tesseract_command() -> Optional[str]:
        return get_tesseract_command()

    @staticmethod
    def configure() -> None:
        command = ensure_tesseract_available()
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = command

    @staticmethod
    def recognize(image):
        """
        Recognize text from an image or cropped image region.
        """

        configure = TesseractRecognizer.configure
        configure()
        import pytesseract

        config = "--oem 3 --psm 6"
        text = pytesseract.image_to_string(
            image,
            config=config,
            lang="eng",
            timeout=30,
        )
        return text.strip()
