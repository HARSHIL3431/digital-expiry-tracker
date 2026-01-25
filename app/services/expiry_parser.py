import re
from datetime import datetime, date
from typing import Optional
import calendar


class ExpiryParser:
    """
    Extract expiry date from OCR text.
    Handles noisy real-world formats.
    """

    DATE_PATTERNS = [
        r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b",   # DD/MM/YYYY
        r"\b(\d{2}[/-]\d{2}[/-]\d{2})\b",   # DD/MM/YY
        r"\b(\d{2}[/-]\d{4})\b",            # MM/YYYY
        r"\b([A-Za-z]{3,9}\s+\d{4})\b",     # Aug 2025
    ]

    MONTH_MAP = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    def extract_expiry_date(self, text: str) -> Optional[date]:
        text = text.lower()

        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                parsed = self._parse_date(match)
                if parsed:
                    return parsed

        return None

    def _parse_date(self, raw: str) -> Optional[date]:
        raw = raw.strip()

        # DD/MM/YYYY or DD-MM-YYYY
        try:
            if len(raw) == 10:
                return datetime.strptime(
                    raw.replace("-", "/"), "%d/%m/%Y"
                ).date()
        except ValueError:
            pass

        # DD/MM/YY
        try:
            if len(raw) == 8:
                return datetime.strptime(
                    raw.replace("-", "/"), "%d/%m/%y"
                ).date()
        except ValueError:
            pass

        # MM/YYYY (common in medicine strips)
        try:
            if len(raw) == 7:
                dt = datetime.strptime(raw.replace("-", "/"), "%m/%Y")
                last_day = calendar.monthrange(dt.year, dt.month)[1]
                return date(dt.year, dt.month, last_day)
        except ValueError:
            pass

        # Month YYYY (Aug 2025)
        parts = raw.split()
        if len(parts) == 2:
            month = self.MONTH_MAP.get(parts[0])
            try:
                year = int(parts[1])
                if month:
                    last_day = calendar.monthrange(year, month)[1]
                    return date(year, month, last_day)
            except ValueError:
                pass

        return None
