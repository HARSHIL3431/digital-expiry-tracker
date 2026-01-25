from datetime import date
from app.services.expiry_parser import ExpiryParser



parser = ExpiryParser()


def test_expiry_with_keyword():
    text = """
    MFG: 12/08/2023
    EXP: 12/08/2025
    """
    assert parser.extract_expiry_date(text) == date(2025, 8, 12)


def test_best_before_format():
    text = "Best before Aug 2026"
    assert parser.extract_expiry_date(text) == date(2026, 8, 31)


def test_mm_yyyy_format():
    text = "Expiry 09/2024"
    assert parser.extract_expiry_date(text) == date(2024, 9, 30)


def test_ignore_mfg_date():
    text = """
    Manufactured: 05/06/2022
    Packed on: 06/06/2022
    """
    assert parser.extract_expiry_date(text) is None


def test_fallback_latest_future_date():
    text = """
    MFG 01/01/2023
    01/01/2024
    01/01/2026
    """
    assert parser.extract_expiry_date(text) == date(2026, 1, 1)
