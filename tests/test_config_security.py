"""Security regression tests for config, demo-user, and expiry edge cases.

Uses only synthetic data and dummy credentials.
"""

import importlib
from pathlib import Path


def _reload_config(monkeypatch, env):
    for key in (
        "SECRET_KEY",
        "APP_ENV",
        "ENVIRONMENT",
        "ENABLE_DEMO_USER",
        "DEMO_USER_PASSWORD",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import app.core.config as config

    return importlib.reload(config)


def test_production_requires_secret_key(monkeypatch):
    import pytest

    with pytest.raises(RuntimeError, match="SECRET_KEY must be configured"):
        _reload_config(monkeypatch, {"APP_ENV": "production"})
    # Restore module to development defaults for other tests.
    _reload_config(monkeypatch, {})


def test_dev_secret_is_ephemeral_not_hardcoded(monkeypatch):
    config = _reload_config(monkeypatch, {"APP_ENV": "development"})
    assert config.SECRET_KEY
    assert len(config.SECRET_KEY) >= 16
    source = Path("app/core/config.py").read_text()
    assert "dev-insecure-secret-change-me" not in source
    assert "college_project_secret" not in source
    # Restore defaults.
    _reload_config(monkeypatch, {})


def test_no_hardcoded_demo_password_in_source():
    source = Path("app/main.py").read_text()
    assert 'hash_password("123456")' not in source
    assert "test_password" not in source or "123456" not in source


def test_invalid_calendar_date_rejected():
    from app.services.expiry_parser import ExpiryParser

    parser = ExpiryParser()
    assert parser.extract_expiry_date("Expiry: 31/02/2025") is None
    assert parser.extract_expiry_date("EXP 99/99/9999") is None


def test_missing_date_returns_none_for_manual_review():
    from app.services.expiry_parser import ExpiryParser

    parser = ExpiryParser()
    assert parser.extract_expiry_date("No date on this label") is None
    assert parser.extract_expiry_date("") is None


def test_low_confidence_scan_flags_manual_review(monkeypatch):
    from app.services.scan_service import ScanService

    service = ScanService()
    monkeypatch.setattr(
        service.ocr_service,
        "enhanced_extract_with_regions",
        lambda _path: {"texts": [], "regions": []},
    )
    result = service.scan_image("unused-path.png")
    assert result["success"] is False
    assert result["expiry_date"] is None
    assert "not detected" in result["message"].lower()


def test_scan_generic_failure_returns_safe_error(client, monkeypatch):
    import io

    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
        b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
        b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def boom(_path):
        raise ValueError("not an image")

    monkeypatch.setattr("app.api.v1.scan.scan_service.scan_image", boom)
    resp = client.post(
        "/api/v1/scan/image",
        files={"file": ("tiny.png", io.BytesIO(tiny_png), "image/png")},
    )
    assert resp.status_code == 400
    assert "readable image" in resp.text.lower()
    assert "not an image" not in resp.text
