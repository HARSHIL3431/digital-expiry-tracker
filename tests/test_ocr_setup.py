
import io
import sys
import types

import pytest

from app.services.ocr_tesseract import TesseractRecognizer, get_tesseract_command
from app.services.ocr_service import OCRService


def test_explicit_tesseract_cmd_path_is_used(monkeypatch, tmp_path):
    executable = tmp_path / "tesseract.exe"
    executable.write_bytes(b"")

    monkeypatch.setenv("TESSERACT_CMD", str(executable))
    monkeypatch.delenv("TESSERACT_PATH", raising=False)
    monkeypatch.setattr("shutil.which", lambda _name: None)
    monkeypatch.setattr("app.services.ocr_tesseract.COMMON_TESSERACT_LOCATIONS", ())

    assert get_tesseract_command() == str(executable)


def test_missing_configured_tesseract_command_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv("TESSERACT_CMD", str(tmp_path / "missing-tesseract.exe"))
    monkeypatch.delenv("TESSERACT_PATH", raising=False)
    monkeypatch.setattr("shutil.which", lambda _name: None)
    monkeypatch.setattr("app.services.ocr_tesseract.COMMON_TESSERACT_LOCATIONS", ())

    assert get_tesseract_command() is None


def test_tesseract_path_lookup_fallback(monkeypatch):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.delenv("TESSERACT_PATH", raising=False)
    monkeypatch.setattr("shutil.which", lambda _name: "C:/tools/tesseract.exe")
    monkeypatch.setattr("app.services.ocr_tesseract.COMMON_TESSERACT_LOCATIONS", ())

    assert get_tesseract_command() == "C:/tools/tesseract.exe"


def test_tesseract_recognizer_raises_when_engine_missing(monkeypatch):
    monkeypatch.setattr("app.services.ocr_tesseract.get_tesseract_command", lambda: None)

    with pytest.raises(RuntimeError, match="Tesseract OCR engine is not installed"):
        TesseractRecognizer.recognize(object())


def test_ocr_service_raises_clear_error_when_engine_missing(monkeypatch):
    monkeypatch.setattr("app.services.ocr_tesseract.get_tesseract_command", lambda: None)
    monkeypatch.setattr(OCRService, "_require_python_ocr_dependencies", lambda _self: None)

    with pytest.raises(RuntimeError, match="Tesseract OCR engine is not installed"):
        OCRService()._full_image_tesseract("unused.png")


def test_easyocr_reader_is_reused(monkeypatch):
    fake_easyocr = types.ModuleType("easyocr")

    class FakeReader:
        def __init__(self, langs, gpu=False):
            self.langs = langs
            self.gpu = gpu

    fake_easyocr.Reader = FakeReader
    monkeypatch.setitem(sys.modules, "easyocr", fake_easyocr)
    monkeypatch.setattr(OCRService, "_require_python_ocr_dependencies", lambda _self: None)

    service = OCRService()
    first_reader = service._get_easyocr_reader()
    second_reader = service._get_easyocr_reader()

    assert first_reader is second_reader


def test_scan_image_returns_503_for_ocr_dependency_failure(client, monkeypatch):
    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
        b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
        b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def fail(_file_path):
        raise RuntimeError(
            "OCR dependencies are missing: pytesseract, easyocr. "
            "Install OCR extras to use /api/v1/scan/* endpoints."
        )

    monkeypatch.setattr("app.api.v1.scan.scan_service.scan_image", fail)

    response = client.post(
        "/api/v1/scan/image",
        files={"file": ("tiny.png", io.BytesIO(tiny_png), "image/png")},
    )

    assert response.status_code == 503
    assert "OCR dependencies are missing" in response.text
