import re
import calendar
from datetime import datetime, date
from typing import Optional, List, Tuple


class ExpiryParser:
    """
    Extract expiry date from OCR text.
    Production-grade, keyword-first, noise-resistant.
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

    MFG_KEYWORDS = [
        "mfg",
        "mfd",
        "mfg date",
        "manufactured",
        "manufacturing",
        "packed on",
        "pack date",
        "pkd",
    ]

    EXPIRY_KEYWORDS = [
        "expiry",
        "expiry date",
        "best before",
        "best-before",
        "use before",
        "expires",
        "exp date",
        "exp.",
        r"\bexp\b",
    ]

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    def extract_expiry_date(self, text: str) -> Optional[date]:
        text = (text or "").lower()
        lines = text.splitlines()

        # ✅ STEP 1: Keyword-based extraction (highest priority)
        for line in lines:
            if self._contains_expiry_keyword(line) and not self._contains_mfg_keyword(line):
                parsed, _ = self._extract_date_from_line(line)
                if parsed:
                    return parsed

        # ✅ STEP 2: Fallback — latest non-MFG date (NO today filtering)
        candidates: List[Tuple[date, int]] = []

        for line in lines:
            if self._contains_mfg_keyword(line):
                continue

            parsed, confidence = self._extract_date_from_line(line)
            if parsed:
                candidates.append((parsed, confidence))

        if candidates:
            # Sort by confidence first, then date
            candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
            return candidates[0][0]

        return None

    def extract_dates_with_confidence(self, text: str) -> List[Tuple[date, int]]:
        """
        Extract all date candidates from free text with parser confidence.
        """
        normalized = self._normalize_text(text)
        candidates: List[Tuple[date, int]] = []
        occupied_spans: List[Tuple[int, int]] = []

        for pattern in self.DATE_PATTERNS:
            for match in re.finditer(pattern, normalized):
                start, end = match.span(1)
                if any(start < span_end and end > span_start for span_start, span_end in occupied_spans):
                    continue

                parsed, confidence = self._parse_date(match.group(1))
                if parsed:
                    candidates.append((parsed, confidence))
                    occupied_spans.append((start, end))

        # De-duplicate by date while preserving best confidence
        dedup: dict[date, int] = {}
        for parsed, confidence in candidates:
            dedup[parsed] = max(confidence, dedup.get(parsed, 0))

        return [(parsed, confidence) for parsed, confidence in dedup.items()]

    # ---------------- HELPERS ---------------- #

    def _contains_expiry_keyword(self, line: str) -> bool:
        normalized_line = self._normalize_text(line)
        return any(re.search(k, normalized_line, flags=re.IGNORECASE) for k in self.EXPIRY_KEYWORDS)

    def _contains_mfg_keyword(self, line: str) -> bool:
        normalized_line = self._normalize_text(line)
        return any(k in normalized_line for k in self.MFG_KEYWORDS)

    def _extract_date_from_line(self, line: str) -> Tuple[Optional[date], int]:
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                return self._parse_date(match.group(1))
        return None, 0

    def _parse_date(self, raw: str) -> Tuple[Optional[date], int]:
        raw = raw.strip()

        try:
            # DD/MM/YYYY
            if re.fullmatch(r"\d{2}[/-]\d{2}[/-]\d{4}", raw):
                return datetime.strptime(raw.replace("-", "/"), "%d/%m/%Y").date(), 2

            # DD/MM/YY
            if re.fullmatch(r"\d{2}[/-]\d{2}[/-]\d{2}", raw):
                return datetime.strptime(raw.replace("-", "/"), "%d/%m/%y").date(), 2

            # MM/YYYY → last day of month
            if re.fullmatch(r"\d{2}[/-]\d{4}", raw):
                dt = datetime.strptime(raw.replace("-", "/"), "%m/%Y")
                last_day = calendar.monthrange(dt.year, dt.month)[1]
                return date(dt.year, dt.month, last_day), 1

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
                    return date(year, month, last_day), 1
            except ValueError:
                pass

        return None, 0
